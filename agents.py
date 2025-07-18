import os
import requests
import feedparser
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import warnings
import json
from dotenv import load_dotenv

from processor.vertex_ai_processor import extract_intelligence_with_gemini
from database.db_handler import insert_pulse_and_indicators

load_dotenv()
VERIFY_SSL = False
if not VERIFY_SSL:
    from urllib3.exceptions import InsecureRequestWarning
    warnings.simplefilter('ignore', InsecureRequestWarning)


class DataIngestionAgent:
    """Agent responsible for ingesting data from a hardcoded list of sources."""
    def _scrape_article(self, url):
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=VERIFY_SSL, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.select_one('h1, h1.story-title, .post-title').get_text(strip=True) if soup.select_one('h1, h1.story-title, .post-title') else "Untitled"
            content_div = soup.select_one('div.article-content, div.articlebody, .post-body, article, .td-post-content')
            full_text = content_div.get_text(separator='\n', strip=True) if content_div else ""
            if not full_text: return None
            return {"title": title, "content": full_text}
        except Exception as e:
            print(f"    ERROR scraping article {url}: {e}")
            return None

    def ingest_hacker_news(self, limit=10):
        print("AGENT (Ingestion): Fetching The Hacker News...")
        raw_data = []
        try:
            response = requests.get("https://thehackernews.com/", headers={'User-Agent': 'Mozilla/5.0'}, verify=VERIFY_SSL, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.select('a.story-link')[:limit]
            for article_link in articles:
                url = article_link.get('href')
                time.sleep(1)
                scraped_content = self._scrape_article(url)
                if scraped_content:
                    raw_data.append({"source": "The Hacker News", "url": url, **scraped_content, "published_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        except Exception as e:
            print(f"ERROR fetching THN main page: {e}")
        return raw_data

    def ingest_otx(self, limit=15):
        print("AGENT (Ingestion): Fetching AlienVault OTX pulses...")
        api_key = os.getenv("OTX_API_KEY")
        if not api_key: 
            print("  WARN: OTX_API_KEY not found in .env file. Skipping.")
            return []
        url = "https://otx.alienvault.com/api/v1/pulses/general"
        processed_pulses = []
        try:
            response = requests.get(url, headers={'X-OTX-API-KEY': api_key}, params={'limit': limit}, verify=VERIFY_SSL, timeout=30)
            response.raise_for_status()
            for pulse in response.json().get('results', []):
                if not isinstance(pulse, dict): continue
                threat_name = ", ".join([fam.get('display_name', '') for fam in pulse.get('malware_families', []) if fam.get('display_name')]) or "N/A"
                processed_pulses.append({ 
                    "source": "AlienVault OTX", "title": pulse.get('name', 'Untitled OTX Pulse'),
                    "url": f"https://otx.alienvault.com/pulse/{pulse.get('id')}", "published_at": pulse.get('created'),
                    "summary": pulse.get('description', 'No description provided.'), "threat_name": threat_name,
                    "threat_category": "Threat Intelligence Pulse", "severity": "High",
                    "targeted_countries": [geo.get('country_name') for geo in pulse.get('targeted_countries', []) if geo.get('country_name')],
                    "targeted_industries": [],
                    "indicators": [{'type': ioc.get('type'), 'value': ioc.get('indicator')} for ioc in pulse.get('indicators', [])]
                })
        except Exception as e:
            print(f"  ERROR fetching OTX data: {e}")
        return processed_pulses

    def ingest_cisa(self):
        print("AGENT (Ingestion): Fetching CISA data...")
        cisa_url = "https://www.cisa.gov/news-events/cybersecurity-advisories/all/rss.xml"
        raw_data = []
        try:
            response = requests.get(cisa_url, verify=VERIFY_SSL, timeout=30)
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:5]:
                raw_data.append({"source": "CISA", "title": entry.title, "url": entry.link, "content": f"Title: {entry.title}\n\nSummary: {entry.summary}", "published_at": entry.published})
        except Exception as e:
            print(f"  ERROR fetching CISA feed: {e}")
        return raw_data
        
    def ingest_nist_nvd(self, days=2):
        print(f"AGENT (Ingestion): Fetching NIST NVD CVEs...")
        raw_data = []
        try:
            base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            params = {'pubStartDate': start_date.isoformat(), 'pubEndDate': end_date.isoformat(), 'resultsPerPage': 200}
            response = requests.get(base_url, params=params, timeout=30, verify=VERIFY_SSL)
            cve_data = response.json()
            for item in cve_data.get('vulnerabilities', []):
                cve = item.get('cve', {})
                cve_id = cve.get('id')
                description = next((d['value'] for d in cve.get('descriptions', []) if d['lang'] == 'en'), 'No description.')
                raw_data.append({"source": "NIST NVD", "title": f"Vulnerability Details for {cve_id}", "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}", "content": f"Description: {description}", "published_at": cve.get('published')})
        except Exception as e:
            print(f"  ERROR fetching NIST NVD data: {e}")
        return raw_data


class IntelligenceExtractionAgent:
    def __init__(self):
        self.country_keywords = [ "USA", "United States", "China", "Russia", "Germany", "UK", "United Kingdom", "France", "Canada", "Australia", "India", "Brazil", "Japan", "South Korea", "Iran", "Israel", "Taiwan", "Ukraine", "Netherlands", "Spain" ]

    def _fallback_country_scan(self, text_content):
        # Set to store unique country names found in the text content
        found_countries = set()
        for country in self.country_keywords:
            if country.lower() in text_content.lower():
                if country == "USA": found_countries.add("United States")
                elif country == "UK": found_countries.add("United Kingdom")
                else: found_countries.add(country)
        return list(found_countries)

    def process_raw_data(self, raw_data_item):
        """Takes raw scraped data and returns a structured, validated pulse dictionary."""
        print(f"  AGENT (Extraction): Processing '{raw_data_item.get('title', 'Untitled')}'...")
        structured_data = extract_intelligence_with_gemini(raw_data_item['content'], raw_data_item['source'])
        
        if not structured_data:
            print("  WARN: AI processing failed completely. Creating a basic pulse for review.")
            title = raw_data_item.get('title', 'Processing Error - Review Source')
            countries = self._fallback_country_scan(raw_data_item['content'])
            return {
                "source": raw_data_item.get('source'), "title": title, "url": raw_data_item.get('url'),
                "published_at": raw_data_item.get('published_at'), "summary": "AI processing failed. Please review the source material directly.",
                "threat_name": "N/A", "threat_category": "Unprocessed", "severity": "Medium",
                "targeted_industries": [], "targeted_countries": countries if countries else ["Global"], "indicators": []
            }
        
        # --- TITLE VALIDATION AND FALLBACK ---
        ai_title = structured_data.get('pulse_title')
        is_generic_title = "Vulnerability Details for CVE" in ai_title or "NIST NVD Entry" in ai_title if ai_title else True
        final_title = raw_data_item.get('title') if is_generic_title else ai_title
        
        # Geolocation Safety Net
        if not structured_data.get('targeted_countries'):
            fallback_countries = self._fallback_country_scan(raw_data_item['content'])
            structured_data['targeted_countries'] = fallback_countries if fallback_countries else ["Global"]
        
        pulse = {
            "source": raw_data_item.get('source'),
            "url": raw_data_item.get('url'),
            "published_at": raw_data_item.get('published_at'),
            "title": final_title,
            "threat_name": structured_data.get('threat_name', 'N/A'),
            "threat_category": structured_data.get('threat_category', 'Unprocessed'),
            "severity": structured_data.get('severity', 'Medium'),
            "summary": structured_data.get('summary', 'No summary available.'),
            "targeted_industries": structured_data.get('targeted_industries', []),
            "targeted_countries": structured_data.get('targeted_countries', []),
            "indicators": structured_data.get('indicators', [])
        }
        return pulse


class IoCAnalysisAgent:
    """Agent responsible for enriching Indicators of Compromise."""
    def enrich_indicators(self, indicators):
        if not indicators: return []
        api_key = os.getenv("ABUSEIPDB_API_KEY")
        if not api_key: return indicators
        print(f"  AGENT (Analysis): Enriching {len(indicators)} indicators...")
        for ioc in indicators:
            if isinstance(ioc, dict) and ioc.get('type') == 'ipv4':
                try:
                    response = requests.get('https://api.abuseipdb.com/api/v2/check', params={'ipAddress': ioc['value'], 'maxAgeInDays': '90'}, headers={'Accept': 'application/json', 'Key': api_key}, verify=VERIFY_SSL, timeout=20)
                    if response.status_code == 200: ioc['enrichment'] = response.json().get('data', {})
                except Exception as e: print(f"    ERROR enriching IP {ioc['value']}: {e}")
        return indicators


class PersistenceAgent:
    """Agent responsible for saving the final pulse to the database."""
    def save_pulse(self, pulse_data):
        print(f"  AGENT (Persistence): Saving pulse '{pulse_data.get('title', 'NO TITLE')}' to database...")
        return insert_pulse_and_indicators(pulse_data)


class DiscoveryAgent:
    """A placeholder for the autonomous discovery agent. Not used in this orchestrator version."""
    def run_discovery_cycle(self):
        print("AGENT (Discovery): Discovery cycle is not active in this configuration.")
        pass
