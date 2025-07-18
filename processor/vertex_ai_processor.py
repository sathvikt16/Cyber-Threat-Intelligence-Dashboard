import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel
import json
import os
import numpy as np

# --- Vertex AI Initialization ---
PROJECT_ID = "itd-ai-interns"
REGION = "us-central1"
STABLE_MODEL_NAME = "gemini-2.5-flash"

try:
    vertexai.init(project=PROJECT_ID, location=REGION)
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize Vertex AI. Check your GCP authentication and project setup. Error: {e}")
    exit()

# --- AI Health Check Function ---
def check_ai_health():
    """Performs a simple test call to the Vertex AI API to confirm it's working."""
    print("Performing AI Health Check...")
    try:
        model = GenerativeModel(STABLE_MODEL_NAME)
        response = model.generate_content("test")
        if response.text:
            print("AI Health Check PASSED. Connection to Vertex AI is working.")
            return True
    except Exception as e:
        print("\n" + "="*80 + "\n!!! CRITICAL ERROR: AI HEALTH CHECK FAILED !!!")
        print("The system cannot connect to or get a valid response from the Vertex AI API.")
        print("Please check your GCP Project settings (API enabled, Billing active, Correct Authentication).")
        print(f"Underlying Error: {e}" + "\n" + "="*80 + "\n")
        return False
    return False

# --- Core AI Functions ---
def get_text_embedding(text: str) -> np.ndarray | None:
    """Generates a text embedding using Vertex AI's Gecko model."""
    try:
        model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
        embeddings = model.get_embeddings([text])
        return np.array(embeddings[0].values, dtype=np.float32)
    except Exception as e:
        print(f"  ERROR generating embedding: {e}")
        return None

def vet_domain_with_ai(domain: str) -> bool:
    """Uses AI to quickly check if a domain seems like a valid CTI source."""
    # This function is part of the advanced DiscoveryAgent, but we keep it here.
    model = GenerativeModel(STABLE_MODEL_NAME)
    prompt = f"Is the domain '{domain}' a reputable source for cybersecurity news or technical write-ups? Answer with only YES or NO."
    try:
        response = model.generate_content(prompt)
        return "YES" in response.text.upper()
    except Exception:
        return False

def extract_intelligence_with_gemini(text_content: str, source: str) -> dict | None:
    """
    Analyzes text using Gemini with the final, re-engineered prompt for high-quality titles and data.
    """
    model = GenerativeModel(STABLE_MODEL_NAME)

    # --- FINAL, MOST ROBUST PROMPT WITH CHAIN-OF-THOUGHT & TITLE REWRITING ---
    prompt = f"""
    You are a world-class Cyber Threat Intelligence (CTI) analyst. Your task is to analyze the following text from source '{source}' and generate a structured JSON output. You must follow all rules with extreme precision.

    The text to analyze is:
    ---
    {text_content[:25000]}
    ---

    Respond with ONLY a single JSON object containing these exact fields:

    1.  "pulse_title": A concise, human-readable headline.
        - **MANDATORY MISSION:** You MUST rewrite generic titles. If the source is "NIST NVD" and the title is "Vulnerability Details for CVE-2025-1234", analyze the description and create an informative title like "Critical RCE Vulnerability in Apache Jenkins (CVE-2025-1234)". Your value is in this translation.
    2.  "threat_category": Classify the primary threat into ONE of the following detailed categories. Analyze the text to determine the main subject and choose the MOST specific category that applies.

        - **Malware-Related:**
          - "Ransomware": For threats involving file encryption and extortion.
          - "Spyware / Infostealer": For threats focused on stealing credentials, financial data, or sensitive information.
          - "Botnet / C2": For threats involving command-and-control infrastructure or zombie networks.
          - "Dropper / Loader": For malware whose primary purpose is to install other malware.
          - "Wiper": For destructive malware designed to erase data.
          - "General Malware": For general malware analysis not fitting other categories.
        - **Actor-Related:**
          - "APT Activity": For campaigns attributed to a nation-state or sophisticated persistent threat group.
          - "Cybercrime Group": For activity from financially motivated groups (e.g., ransomware gangs).
        - **Attack Vector-Related:**
          - "Phishing Campaign": For large-scale social engineering campaigns via email.
          - "Supply Chain Attack": For attacks that compromise software vendors or updates.
          - "DDoS Attack": For Distributed Denial of Service attacks.
        - **Impact-Related:**
          - "Data Breach": For reports confirming a successful data leak or exfiltration.
        - **Rest of them**
          - Deeply analyse the content and make it fall into any threat category.

    3.  "targeted_countries": A list of countries targeted or affected.
        - RULE: You MUST identify specific countries. Do not use "Global".
        - RULE: If no country is named, INFER it from context. A US agency implies ["USA"]. A German company implies ["Germany"].
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
