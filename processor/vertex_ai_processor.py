# import vertexai
# from vertexai.generative_models import GenerativeModel
# import json
# import os

# # --- Vertex AI Initialization ---
# PROJECT_ID = "itd-ai-interns"
# REGION = "us-central1"
# vertexai.init(project=PROJECT_ID, location=REGION)

# def extract_intelligence_with_gemini(text_content: str, source: str, model_name: str = "gemini-2.5-pro") -> dict | None:
#     """
#     Analyzes text using Gemini on Vertex AI to extract structured threat intelligence.
#     Uses a more stable model version and includes threat categorization.
#     """
#     model = GenerativeModel(model_name)

#     # A more detailed prompt to mimic OTX-style data extraction
#     prompt = f"""
#     Analyze the following cyber threat intelligence text from '{source}'. Your mission is to act as an expert CTI analyst and extract structured data.

#     The text is:
#     ---
#     {text_content[:25000]}
#     ---

#     Extract the following information and structure your response as a single JSON object. Do NOT provide any text or explanation outside of the JSON object.

#     1.  "pulse_title": The original title of the article or report.
#     2.  "threat_name": The specific name of the malware (e.g., "Qakbot"), vulnerability (e.g., "CVE-2023-1234"), or threat actor group (e.g., "APT28"). If not mentioned, use "N/A".
#     3.  "threat_category": Classify the primary threat into one of these categories: ["Vulnerability", "Malware", "Phishing", "APT Activity", "Data Breach", "Cybercrime", "General Security News"]. Choose the single most appropriate category.
#     4.  "targeted_industries": A JSON list of specific industries targeted (e.g., ["Logistics", "Finance", "Healthcare"]). If none are explicitly mentioned, use an empty list [].
#     5.  "targeted_countries": A JSON list of countries targeted or affected (e.g., ["USA", "Germany", "Brazil"]). Use standard country names. If none are explicitly mentioned, use an empty list [].
#     6.  "summary": A concise, two-sentence summary of the threat for an executive audience.
#     7.  "indicators": A JSON list of observable Indicators of Compromise (IoCs) found in the text.
#         - Supported types are: 'ipv4', 'domain', 'md5', 'sha1', 'sha256', 'url'.
#         - If no indicators are found, use an empty list [].

#     Example of a perfect JSON response:
#     {{
#       "pulse_title": "Critical Flaw in FortiWeb (CVE-2025-25257) Allows SQL Injection",
#       "threat_name": "CVE-2025-25257",
#       "threat_category": "Vulnerability",
#       "targeted_industries": ["Logistics", "Finance", "Healthcare"],
#       "targeted_countries": ["Global"],
#       "summary": "Fortinet has released patches for a critical SQL injection vulnerability in its FortiWeb Web Application Firewall. The flaw, tracked as CVE-2025-25257, could allow an unauthenticated attacker to execute arbitrary code.",
#       "indicators": ['sha256']
#     }}
#     """

#     try:
#         response = model.generate_content(prompt)
#         cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
#         return json.loads(cleaned_response)
#     except json.JSONDecodeError:
#         print(f"Error: Gemini did not return valid JSON. Raw response:\n{response.text}")
#         return None
#     except Exception as e:
#         print(f"An error occurred with the Vertex AI API: {e}")
#         return None
# # import vertexai
# # from vertexai.generative_models import GenerativeModel
# # from vertexai.language_models import TextEmbeddingModel
# # import json
# # import os
# # import numpy as np

# # PROJECT_ID = "itd-ai-interns"
# # REGION = "us-central1"
# # vertexai.init(project=PROJECT_ID, location=REGION)

# # def get_text_embedding(text: str) -> np.ndarray | None:
# #     """Generates a text embedding using Vertex AI's Gecko model."""
# #     try:
# #         model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
# #         embeddings = model.get_embeddings([text])
# #         return np.array(embeddings[0].values, dtype=np.float32)
# #     except Exception as e:
# #         print(f"  ERROR generating embedding: {e}")
# #         return None

# # def extract_intelligence_with_gemini(text_content: str, source: str, model_name: str = "gemini-pro") -> dict | None:
# #     """Analyzes text using Gemini on Vertex AI to extract structured threat intelligence."""
# #     model = GenerativeModel(model_name)
# #     prompt = f"""
# #     Analyze the following cyber threat intelligence text from '{source}'. Your mission is to act as an expert CTI analyst and extract structured data.

# #     The text is:
# #     ---
# #     {text_content[:25000]}
# #     ---

# #     Extract the following information and structure your response as a single JSON object. Do NOT provide any text or explanation outside of the JSON object.

# #     1.  "pulse_title": The original title of the article or report.
# #     2.  "threat_name": The specific name of the malware (e.g., "Qakbot"), vulnerability (e.g., "CVE-2023-1234"), or threat actor group (e.g., "APT28"). If not mentioned, use "N/A".
# #     3.  "threat_category": Classify the primary threat into one of these categories: ["Vulnerability", "Malware", "Phishing", "APT Activity", "Data Breach", "Cybercrime", "General Security News"]. Choose the single most appropriate category.
# #     4.  "targeted_industries": A JSON list of specific industries targeted. If none, use an empty list [].
# #     5.  "targeted_countries": A JSON list of countries targeted or affected. If none, use an empty list [].
# #     6.  "summary": A concise, two-sentence summary of the threat for an executive audience.
# #     7.  "indicators": A JSON list of observable Indicators of Compromise (IoCs) found in the text. Supported types: 'ipv4', 'domain', 'md5', 'sha1', 'sha256', 'url'. If none, use an empty list [].
# #     """
# #     try:
# #         response = model.generate_content(prompt)
# #         cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
# #         return json.loads(cleaned_response)
# #     except Exception as e:
# #         print(f"  CRITICAL: Vertex AI API call failed. Error: {e}")
# #         return None

# # def vet_domain_with_ai(domain: str) -> bool:
# #     """Uses AI to quickly check if a domain seems like a valid CTI source."""
# #     print(f"    Vetting domain with AI: {domain}...")
# #     model = GenerativeModel("gemini-pro")
# #     prompt = f"Is the domain '{domain}' a well-known and reputable source for cybersecurity news, threat intelligence, or technical security write-ups? Your entire response must be only the word YES or the word NO."
# #     try:
# #         response = model.generate_content(prompt)
# #         return "YES" in response.text.upper()
# #     except Exception as e:
# #         print(f"    ERROR during AI vetting for {domain}: {e}")
# #         return False




import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel # <-- ADD THIS IMPORT
import json
import os
import numpy as np # <-- ADD THIS IMPORT

# --- Vertex AI Initialization ---
PROJECT_ID = "itd-ai-interns"
REGION = "us-central1"
STABLE_MODEL_NAME = "gemini-2.5-flash"

try:
    vertexai.init(project=PROJECT_ID, location=REGION)
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize Vertex AI. Check your GCP authentication and project setup. Error: {e}")
    exit()

# --- AI Health Check Function (Unchanged) ---
def check_ai_health():
    print("Performing AI Health Check...")
    try:
        model = GenerativeModel(STABLE_MODEL_NAME)
        response = model.generate_content("test")
        if response.text:
            print("AI Health Check PASSED. Connection to Vertex AI is working.")
            return True
    except Exception as e:
        print("\n" + "="*80 + "\n!!! CRITICAL ERROR: AI HEALTH CHECK FAILED !!!")
        print("Please check your GCP Project settings (API enabled, Billing active, Correct Authentication).")
        print(f"Underlying Error: {e}" + "\n" + "="*80 + "\n")
        return False
    return False

# --- NEW: Add the missing get_text_embedding function ---
def get_text_embedding(text: str) -> np.ndarray | None:
    """Generates a text embedding using Vertex AI's Gecko model."""
    try:
        # Use the standard model for text embeddings
        model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
        embeddings = model.get_embeddings([text])
        # Return the embedding as a numpy array, which is needed for FAISS
        return np.array(embeddings[0].values, dtype=np.float32)
    except Exception as e:
        print(f"  ERROR generating embedding: {e}")
        return None

# --- NEW: Add the missing vet_domain_with_ai function ---
def vet_domain_with_ai(domain: str) -> bool:
    """Uses AI to quickly check if a domain seems like a valid CTI source."""
    print(f"    Vetting domain with AI: {domain}...")
    model = GenerativeModel(STABLE_MODEL_NAME)
    prompt = f"Is the domain '{domain}' a well-known and reputable source for cybersecurity news, threat intelligence, or technical security write-ups? Your entire response must be only the word YES or the word NO."
    try:
        response = model.generate_content(prompt)
        return "YES" in response.text.upper()
    except Exception as e:
        print(f"    ERROR during AI vetting for {domain}: {e}")
        return False

# --- The main extraction function is unchanged ---
def extract_intelligence_with_gemini(text_content: str, source: str) -> dict | None:
    """
    Analyzes text using Gemini with the final, re-engineered prompt for high-quality titles and data.
    """
    model = GenerativeModel(STABLE_MODEL_NAME)
    prompt = f"""
    You are a world-class Cyber Threat Intelligence (CTI) analyst. Your task is to analyze the following text from source '{source}' and generate a structured JSON output. You must follow all rules with extreme precision.

    The text to analyze is:
    ---
    {text_content[:25000]}
    ---

    Respond with ONLY a single JSON object containing these exact fields:

    1.  "pulse_title": A concise, human-readable headline. If the original title is a generic CVE ID, you MUST rewrite it to be descriptive (e.g., "Critical RCE Vulnerability in Apache Struts (CVE-2025-1234)").

    2.  "threat_category": Classify the primary threat into ONE of the following: ["Vulnerability", "Malware", "Phishing", "APT Activity", "Data Breach", "Cybercrime", "General Security News"].

    3.  "targeted_countries": A list of countries targeted or affected.
        - RULE: You MUST identify specific countries. Do not use "Global".
        - RULE: If no country is named, INFER it from context.
        - RULE: If no country can be identified, return an empty list [].

    4.  "threat_name": The specific name of the malware ("Qakbot"), vulnerability ("CVE-2023-1234"), or threat actor ("APT28").
    5.  "targeted_industries": A list of specific industries targeted. If none, use an empty list [].
    6. "severity": A single string classification: ["Low", "Medium", "High", "Critical"].
    7.  "summary": A concise, two-sentence summary for an executive audience.
    8.  "indicators": A list of IoC objects with "type" and "value". If none, use an empty list [].
    """
    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except json.JSONDecodeError:
        print(f"  ERROR: Gemini did not return valid JSON. Raw response:\n{response.text}")
        return None
    except Exception as e:
        print(f"  ERROR during AI content generation: {e}")
        return None

