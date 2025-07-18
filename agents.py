import os
import requests
import feedparser
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import warnings
from urllib.parse import urlparse
import tldextract
import sqlite3
import numpy as np
import faiss
from dotenv import load_dotenv
import http.client
import json

from processor.vertex_ai_processor import extract_intelligence_with_gemini, get_text_embedding, vet_domain_with_ai
from database.db_handler import DATABASE_NAME, add_correlation, get_all_pulses_for_vector_search, add_dynamic_source, insert_pulse_and_indicators

load_dotenv()
VERIFY_SSL = False
if not VERIFY_SSL:
    from urllib3.exceptions import InsecureRequestWarning
    warnings.simplefilter('ignore', InsecureRequestWarning)

# --- All Agent Classes ---

class DiscoveryAgent:
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        self.conn = http.client.HTTPSConnection("google.serper.dev")
        # A list of broad, high-signal queries to find new threats
        self.search_queries = [
            "new malware variant discovered",
            "critical vulnerability disclosed this week",
            "major data breach notification",
            "cyber security threat intelligence report",
            "nation state hacking campaign"
        ]

    def discover_and_fetch_urls(self):
        """
        Uses Serper API with broad queries to find the latest threat articles from the web.
        Returns a list of URLs to be processed.
        """
        if not self.api_key:
            print("AGENT (Discovery): SERPER_API_KEY not found. Cannot discover new content.")
            return []

        print("AGENT (Discovery): Searching the web for new threat intelligence...")
        discovered_links = set() # Use a set to automatically handle duplicates
        
        for query in self.search_queries:
            print(f"  -> Searching for: '{query}'")
            try:
                payload = json.dumps({"q": query, "num": 5}) # Get top 5 results for each query
                headers = {'X-API-KEY': self.api_key, 'Content-Type': 'application/json'}
                self.conn.request("POST", "/search", payload, headers)
                res = self.conn.getresponse()
                data = res.read()
                search_results = json.loads(data.decode("utf-8"))
                
                for result in search_results.get('organic', []):
                    discovered_links.add(result['link'])
                
                time.sleep(1) # Be polite to the API
            except Exception as e:
                print(f"    ERROR during Serper API call for query '{query}': {e}")
                continue
        
        print(f"AGENT (Discovery): Discovered {len(discovered_links)} unique URLs to process.")
        return list(discovered_links)

# --- We no longer need the DataIngestionAgent with its hardcoded sites ---
# You can delete the entire DataIngestionAgent class.

# --- Helper function to be used by the orchestrator ---
def scrape_url_to_raw_data(url):
    """
    Takes a single URL, scrapes it, and returns a raw_data dictionary.
    This is a standalone utility function now.
    """
    print(f"  -> Scraping discovered URL: {url}")
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=VERIFY_SSL, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.select_one('h1, h1.story-title, .post-title').get_text(strip=True) if soup.select_one('h1, h1.story-title, .post-title') else "Untitled Discovery"
        content_div = soup.select_one('div.article-content, div.articlebody, .post-body, article, .td-post-content')
        full_text = content_div.get_text(separator='\n', strip=True) if content_div else ""

        if not full_text:
            print(f"    WARN: Could not extract content from {url}.")
            return None

        return {
            "source": tldextract.extract(url).registered_domain,
            "title": title, "url": url, "content": full_text,
            "published_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "is_web_content": True, "full_html": response.content
        }
    except Exception as e:
        print(f"    ERROR scraping URL {url}: {e}")
        return None



class DiscoveryAgent:
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        self.conn = http.client.HTTPSConnection("google.serper.dev")
        self.domain_blacklist = { 'twitter.com', 'linkedin.com', 'facebook.com', 'youtube.com', 'github.com', 'google.com', 'microsoft.com', 'apple.com', 't.co', 'cisa.gov', 'nist.gov', 'alienvault.com', 'bleepingcomputer.com', 'thehackernews.com' }

    def _get_top_threat_names(self, limit=5):
        """Gets the most frequently mentioned threat names from our database to search for."""
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT threat_name, COUNT(*) as count 
                    FROM pulses 
                    WHERE threat_name IS NOT 'N/A' AND threat_name IS NOT ''
                    GROUP BY threat_name 
                    HAVING count > 1
                    ORDER BY count DESC 
                    LIMIT ?
                """, (limit,))
                return [row[0] for row in cursor.fetchall()]
            except sqlite3.OperationalError:
                # This can happen if the table doesn't exist on the very first run
                return []

    def search_for_sources(self, threat_name):
        """Uses Serper API to find new potential sources for a given threat."""
        if not self.api_key: return []
        
        print(f"  AGENT (Discovery): Searching Serper for new sources related to '{threat_name}'...")
        query = f'"{threat_name}" security research OR "vulnerability analysis"'
        
        try:
            payload = json.dumps({"q": query})
            headers = {'X-API-KEY': self.api_key, 'Content-Type': 'application/json'}
            self.conn.request("POST", "/search", payload, headers)
            res = self.conn.getresponse()
            data = res.read()
            search_results = json.loads(data.decode("utf-8"))
            return [result['link'] for result in search_results.get('organic', [])]
        except Exception as e:
            print(f"    ERROR during Serper API call: {e}")
            return []

    def run_discovery_cycle(self):
        """The main orchestrator for the discovery process."""
        if not self.api_key:
            print("AGENT (Discovery): SERPER_API_KEY not found in .env. Skipping discovery cycle.")
            return

        threats_to_search = self._get_top_threat_names()
        if not threats_to_search:
            print("AGENT (Discovery): Not enough existing threat data to search for new sources yet.")
            return

        all_new_domains = set()
        for threat in threats_to_search:
            links = self.search_for_sources(threat)
            for link in links:
                try:
                    ext = tldextract.extract(link)
                    domain = f"{ext.domain}.{ext.suffix}"
                    if domain and domain not in self.domain_blacklist:
                        all_new_domains.add(domain)
                except Exception: continue
        
        print(f"AGENT (Discovery): Found {len(all_new_domains)} unique new domains to vet.")
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            for domain in all_new_domains:
                cursor.execute("SELECT domain FROM dynamic_sources WHERE domain = ?", (domain,))
                if cursor.fetchone(): continue
                if vet_domain_with_ai(domain):
                    add_dynamic_source(domain)
                    print(f"  AGENT (Discovery): NEW SOURCE ADDED -> {domain}")

class SocialMediaAgent:
    def __init__(self):
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.api_url = "https://api.twitter.com/2/tweets/search/recent"
        self.query = "#threatintel OR #infosec OR #malware OR #cybersecurity OR #zeroday -is:retweet has:links"

    def fetch_twitter_threats(self):
        if not self.bearer_token:
            return []
        print("AGENT (Social Media): Searching Twitter for recent threats...")
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        params = {"query": self.query, "tweet.fields": "created_at,author_id", "expansions": "author_id"}
        raw_data = []
        try:
            response = requests.get(self.api_url, headers=headers, params=params, timeout=20, verify=VERIFY_SSL)
            response.raise_for_status()
            response_json = response.json()
            tweets = response_json.get('data', [])
            users = {user['id']: user['username'] for user in response_json.get('includes', {}).get('users', [])}
            for tweet in tweets:
                author_username = users.get(tweet.get('author_id'), 'Unknown')
                raw_data.append({ "source": "Twitter", "title": f"Tweet by @{author_username}", "url": f"https://twitter.com/{author_username}/status/{tweet.get('id')}", "content": tweet.get('text'), "published_at": tweet.get('created_at'), "is_web_content": False })
            return raw_data
        except Exception as e:
            print(f"  ERROR fetching Twitter data: {e}"); return []


class DataIngestionAgent:
    def _scrape_article(self, url):
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=VERIFY_SSL, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.select_one('h1, h1.story-title, .post-title').get_text(strip=True) if soup.select_one('h1, h1.story-title, .post-title') else "Untitled"
            content_div = soup.select_one('div.article-content, div.articlebody, .post-body, article, .td-post-content')
            full_text = content_div.get_text(separator='\n', strip=True) if content_div else ""
            if not full_text: return None, None, None
            return title, full_text, response.content
        except Exception as e:
            print(f"    ERROR scraping article {url}: {e}")
            return None, None, None

    def ingest_hacker_news(self, limit=10):
        print(f"AGENT (Ingestion): Fetching The Hacker News (limit={limit})...")
        raw_data = []
        try:
            response = requests.get("https://thehackernews.com/", headers={'User-Agent': 'Mozilla/5.0'}, verify=VERIFY_SSL, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.select('a.story-link')[:limit]
            for article_link in articles:
                url = article_link.get('href')
                time.sleep(1)
                title, full_text, html_content = self._scrape_article(url)
                if full_text:
                    raw_data.append({"source": "The Hacker News", "title": title, "url": url, "content": full_text, "published_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "is_web_content": True, "full_html": html_content})
        except Exception as e:
            print(f"ERROR fetching THN main page: {e}")
        return raw_data

    def ingest_otx(self, limit=15):
        print("AGENT (Ingestion): Fetching AlienVault OTX pulses...")
        api_key = os.getenv("OTX_API_KEY")
        if not api_key:
            print("  WARN: OTX_API_KEY not found in .env file. Skipping OTX.")
            return []
        url = "https://otx.alienvault.com/api/v1/pulses/general"
        headers = {'X-OTX-API-KEY': api_key}
        params = {'limit': limit}
        processed_pulses = []
        try:
            response = requests.get(url, headers=headers, params=params, verify=VERIFY_SSL, timeout=30)
            response.raise_for_status()
            otx_pulses = response.json().get('results', [])
            for pulse in otx_pulses:
                try:
                    if not isinstance(pulse, dict):
                        print(f"  WARN: Skipping non-dictionary item in OTX response: {pulse}")
                        continue
                    malware_families = pulse.get('malware_families', [])
                    threat_name = ", ".join([fam.get('display_name', '') for fam in malware_families if fam.get('display_name')]) or "N/A"
                    pulse_data = {
                        "source": "AlienVault OTX", "title": pulse.get('name', 'Untitled OTX Pulse'),
                        "url": f"https://otx.alienvault.com/pulse/{pulse.get('id')}", "published_at": pulse.get('created'),
                        "summary": pulse.get('description', 'No description provided.'), "threat_name": threat_name,
                        "threat_category": "Threat Intelligence Pulse", "severity": "High",
                        "targeted_countries": [geo.get('country_name') for geo in pulse.get('targeted_countries', []) if geo.get('country_name')],
                        "targeted_industries": [],
                        "indicators": [{'type': ioc.get('type'), 'value': ioc.get('indicator')} for ioc in pulse.get('indicators', [])]
                    }
                    processed_pulses.append(pulse_data)
                except Exception as e:
                    print(f"  ERROR processing a single OTX pulse: {e}. Pulse data: {pulse}")
                    continue
        except requests.RequestException as e:
            print(f"  ERROR fetching OTX data: {e}")
        return processed_pulses

    def ingest_cisa(self):
        print("AGENT (Ingestion): Fetching CISA data...")
        cisa_url = "https://www.cisa.gov/news-events/cybersecurity-advisories/all/rss.xml"
        raw_data = []
        try:
            response = requests.get(cisa_url, verify=VERIFY_SSL, timeout=30)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:5]:
                raw_data.append({"source": "CISA", "title": entry.get('title'), "url": entry.get('link'), "content": f"Title: {entry.get('title')}\n\nSummary: {entry.get('summary')}", "published_at": entry.get('published'), "is_web_content": True, "full_html": entry.get('summary', '')})
        except requests.RequestException as e:
            print(f"  ERROR fetching CISA feed: {e}")
        return raw_data
        
    def ingest_nist_nvd(self, days=1):
        print(f"AGENT (Ingestion): Fetching NIST NVD CVEs for the last {days} day(s)...")
        raw_data = []
        try:
            base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            params = {'pubStartDate': start_date.isoformat(), 'pubEndDate': end_date.isoformat(), 'resultsPerPage': 200}
            response = requests.get(base_url, params=params, timeout=30, verify=VERIFY_SSL)
            response.raise_for_status()
            cve_data = response.json()
            for item in cve_data.get('vulnerabilities', []):
                cve = item.get('cve', {})
                cve_id = cve.get('id')
                description = next((d['value'] for d in cve.get('descriptions', []) if d['lang'] == 'en'), 'No description.')
                published_date = cve.get('published')
                raw_data.append({"source": "NIST NVD", "title": f"Vulnerability Details for {cve_id}", "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}", "content": f"Vulnerability ID: {cve_id}\n\nDescription: {description}", "published_at": published_date, "is_web_content": False})
        except requests.RequestException as e:
            print(f"  ERROR fetching NIST NVD data: {e}")
        return raw_data


class IntelligenceExtractionAgent:
    def __init__(self):
        self.country_keywords = [ "USA", "United States", "China", "Russia", "Germany", "UK", "United Kingdom", "France", "Canada", "Australia", "India", "Brazil", "Japan", "South Korea", "Iran", "Israel", "Taiwan", "Ukraine", "Netherlands", "Spain" ]

    def _fallback_country_scan(self, text_content):
        found_countries = set()
        for country in self.country_keywords:
            if country.lower() in text_content.lower():
                if country == "USA": found_countries.add("United States")
                elif country == "UK": found_countries.add("United Kingdom")
                else: found_countries.add(country)
        return list(found_countries)

    def process_raw_data(self, raw_data_item):
        print(f"  AGENT (Extraction): Processing '{raw_data_item.get('title', 'Untitled')}'...")
        structured_data = extract_intelligence_with_gemini(raw_data_item['content'], raw_data_item['source'])
        
        if not structured_data:
            print("  WARN: AI processing failed. Creating a basic pulse for review.")
            title = raw_data_item.get('title', 'Processing Error - Review Source')
            countries = self._fallback_country_scan(raw_data_item['content'])
            return {
                "source": raw_data_item.get('source'), "title": title, "url": raw_data_item.get('url'),
                "published_at": raw_data_item.get('published_at'), "summary": "AI processing failed. Please review the source material directly.",
                "threat_name": "N/A", "threat_category": "Unprocessed", "severity": "Medium",
                "targeted_industries": [], "targeted_countries": countries if countries else ["Global"], "indicators": [], "embedding": None
            }
        
        if 'title' not in structured_data or not structured_data['title']:
            structured_data['title'] = raw_data_item.get('title', 'Untitled Pulse')
            
        if not structured_data.get('targeted_countries'):
            print("  WARN: AI failed to identify a country. Running fallback scan...")
            fallback_countries = self._fallback_country_scan(raw_data_item['content'])
            structured_data['targeted_countries'] = fallback_countries if fallback_countries else ["Global"]
        
        pulse = {
            "source": raw_data_item.get('source'),
            "url": raw_data_item.get('url'),
            "published_at": raw_data_item.get('published_at'),
            **structured_data
        }
        text_for_embedding = f"Title: {pulse.get('title')}. Summary: {pulse.get('summary')}"
        pulse['embedding'] = get_text_embedding(text_for_embedding)
        return pulse


class CorrelationAgent:
    def __init__(self):
        self.index = None; self.id_map = []
    def build_vector_index(self):
        print("  AGENT (Correlation): Building vector index...")
        pulses = get_all_pulses_for_vector_search()
        if len(pulses) < 2:
            print("  AGENT (Correlation): Not enough embeddings to build index."); return
        embeddings = np.array([p['embedding'] for p in pulses])
        self.id_map = [p['id'] for p in pulses]
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)
        print(f"  AGENT (Correlation): Index built with {self.index.ntotal} vectors.")
    def correlate_pulse(self, pulse_id, pulse_data):
        if not pulse_id: return
        print(f"  AGENT (Correlation): Correlating pulse ID {pulse_id}...")
        if pulse_data.get('embedding') is not None and self.index is not None and self.index.ntotal > 0:
            query_vector = np.array([pulse_data['embedding']])
            distances, indices = self.index.search(query_vector, k=5)
            for i, idx in enumerate(indices[0]):
                if 0.0 < distances[0][i] < 0.35:
                    related_id = self.id_map[idx]
                    if related_id != pulse_id:
                        add_correlation(pulse_id, related_id, "Conceptual Similarity")
                        print(f"    Found vector correlation: Pulse {pulse_id} <-> Pulse {related_id}")


class PersistenceAgent:
    def save_pulse(self, pulse_data):
        print(f"  AGENT (Persistence): Saving pulse '{pulse_data.get('title', 'NO TITLE')}' to database...")
        return insert_pulse_and_indicators(pulse_data)


class IoCAnalysisAgent:
    def enrich_indicators(self, indicators):
        print(f"  AGENT (Analysis): Enriching {len(indicators)} indicators...")
        api_key = os.getenv("ABUSEIPDB_API_KEY")
        if not api_key: return indicators
        for ioc in indicators:
            if isinstance(ioc, dict) and ioc.get('type') == 'ipv4':
                try:
                    response = requests.get('https://api.abuseipdb.com/api/v2/check', params={'ipAddress': ioc['value'], 'maxAgeInDays': '90'}, headers={'Accept': 'application/json', 'Key': api_key}, verify=VERIFY_SSL, timeout=20)
                    if response.status_code == 200:
                        ioc['enrichment'] = response.json().get('data', {})
                except Exception as e: print(f"    ERROR enriching IP {ioc['value']}: {e}")
        return indicators

# import os
# import requests # Make sure requests is imported at the top
# import time
# from datetime import datetime
# import tldextract
# import sqlite3
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# import warnings
# import json

# from processor.vertex_ai_processor import extract_intelligence_with_gemini
# from database.db_handler import insert_pulse_and_indicators

# # --- Setup ---
# load_dotenv()
# VERIFY_SSL = False # This flag will now be used by all our network calls
# if not VERIFY_SSL:
#     from urllib3.exceptions import InsecureRequestWarning
#     warnings.simplefilter('ignore', InsecureRequestWarning)


# # --- Utility function for scraping ---
# def scrape_url_to_raw_data(url):
#     """Takes a single URL, scrapes it, and returns a raw_data dictionary."""
#     print(f"  -> Scraping discovered URL: {url}")
#     try:
#         response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=VERIFY_SSL, timeout=20)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.content, 'html.parser')
        
#         title = soup.select_one('h1, h1.story-title, .post-title').get_text(strip=True) if soup.select_one('h1, h1.story-title, .post-title') else "Untitled Discovery"
#         content_div = soup.select_one('div.article-content, div.articlebody, .post-body, article, .td-post-content')
#         full_text = content_div.get_text(separator='\n', strip=True) if content_div else ""

#         if not full_text:
#             print(f"    WARN: Could not extract content from {url}.")
#             return None

#         return {
#             "source": tldextract.extract(url).registered_domain,
#             "title": title, "url": url, "content": full_text,
#             "published_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         }
#     except Exception as e:
#         print(f"    ERROR scraping URL {url}: {e}")
#         return None

# # --- Agent Definitions ---

# class DiscoveryAgent:
#     def __init__(self):
#         self.api_key = os.getenv("SERPER_API_KEY")
#         self.api_url = "https://google.serper.dev/search"
#         self.search_queries = [
#             "new malware campaign disclosed", "critical vulnerability report",
#             "cyber security data breach notification", "threat intelligence analysis"
#         ]

#     def discover_and_fetch_urls(self):
#         """
#         Uses Serper API with the requests library to find the latest threat articles.
#         """
#         if not self.api_key:
#             print("AGENT (Discovery): SERPER_API_KEY not found. Cannot discover new content.")
#             return []

#         print("AGENT (Discovery): Searching the web for new threat intelligence...")
#         discovered_links = set()
        
#         for query in self.search_queries:
#             print(f"  -> Searching for: '{query}'")
#             try:
#                 # --- FIX: Using the requests library which is configured to handle SSL issues ---
#                 payload = json.dumps({"q": query, "num": 5})
#                 headers = {'X-API-KEY': self.api_key, 'Content-Type': 'application/json'}
                
#                 response = requests.post(self.api_url, headers=headers, data=payload, verify=VERIFY_SSL, timeout=20)
#                 response.raise_for_status()
                
#                 search_results = response.json()
                
#                 for result in search_results.get('organic', []):
#                     discovered_links.add(result['link'])
                
#                 time.sleep(1) # Be polite to the API
#             except Exception as e:
#                 print(f"    ERROR during Serper API call for query '{query}': {e}")
#                 continue
        
#         print(f"AGENT (Discovery): Discovered {len(discovered_links)} unique URLs to process.")
#         return list(discovered_links)


# class IntelligenceExtractionAgent:
#     def process_raw_data(self, raw_data_item):
#         """Takes raw scraped data and returns a structured pulse dictionary."""
#         print(f"  AGENT (Extraction): Processing '{raw_data_item.get('title', 'Untitled')}'...")
#         structured_data = extract_intelligence_with_gemini(raw_data_item['content'], raw_data_item['source'])
        
#         if not structured_data:
#             print("  WARN: AI processing failed. Creating a basic pulse for review.")
#             title = raw_data_item.get('title', 'Processing Error - Review Source')
#             return {
#                 "source": raw_data_item.get('source'), "title": title, "url": raw_data_item.get('url'),
#                 "published_at": raw_data_item.get('published_at'), "summary": "AI processing failed.",
#                 "threat_name": "N/A", "threat_category": "Unprocessed", "severity": "Medium",
#                 "targeted_industries": [], "targeted_countries": ["Global"], "indicators": []
#             }
        
#         pulse = {
#             "source": raw_data_item.get('source'),
#             "url": raw_data_item.get('url'),
#             "published_at": raw_data_item.get('published_at'),
#             "title": structured_data.get('pulse_title', raw_data_item.get('title')),
#             "threat_name": structured_data.get('threat_name', 'N/A'),
#             "threat_category": structured_data.get('threat_category', 'Unprocessed'),
#             "severity": structured_data.get('severity', 'Medium'),
#             "summary": structured_data.get('summary', 'No summary available.'),
#             "targeted_industries": structured_data.get('targeted_industries', []),
#             "targeted_countries": structured_data.get('targeted_countries', []) or ["Global"],
#             "indicators": structured_data.get('indicators', [])
#         }
#         return pulse


# class PersistenceAgent:
#     def save_pulse(self, pulse_data):
#         """Calls the database handler to save the pulse."""
#         print(f"  AGENT (Persistence): Saving pulse '{pulse_data.get('title', 'NO TITLE')}' to database...")
#         return insert_pulse_and_indicators(pulse_data)

