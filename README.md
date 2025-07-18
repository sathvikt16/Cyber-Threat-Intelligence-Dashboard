# Autonomous Cyber Threat Intelligence Dashboard

This project is an AI-powered, autonomous Cyber Threat Intelligence (CTI) platform designed to solve the challenges faced by modern corporate security teams. It transforms the manual, reactive process of monitoring threat feeds into a proactive, automated, and intelligent workflow.

The system continuously ingests data from a variety of high-quality public sources, uses a sophisticated AI agent pipeline to analyze and structure the information, and presents it in a professional, three-pane analytical dashboard for immediate situational awareness and decision support.

<img width="1656" alt="image" src="https://panwgithub.paloaltonetworks.local/sat/Cyber-Threat-Intelligence-Dashboard/assets/3256/b750a1de-cce8-4ca2-bf30-7c268c7b6202">


---

## Core Features

* **Multi-Source Data Ingestion:** Automatically collects and processes threat data from a curated list of top-tier sources, including:
    * **NIST NVD:** For official CVE and vulnerability disclosures.
    * **CISA Advisories:** For government-level alerts and recommendations.
    * **The Hacker News:** For breaking news on campaigns and attacks.
    * **AlienVault OTX:** For community-driven, structured threat pulses and Indicators of Compromise (IoCs).

* **AI-Powered Analysis & Enrichment:** Leverages Google's Gemini Pro model via Vertex AI to perform deep analysis on unstructured data. The AI is responsible for:
    * **Generating Human-Readable Titles:** Rewrites generic headlines (like CVE IDs) into informative, understandable titles.
    * **Granular Threat Categorization:** Classifies each threat into a detailed taxonomy (e.g., Ransomware, APT Activity, Exploit Analysis) for better triage.
    * **Geolocation Inference:** Identifies and extracts affected countries, even when not explicitly mentioned.
    * **Severity Assessment:** Assigns a severity level (Low, Medium, High, Critical) to each threat.

* **Interactive Analytical UI:** A professional, three-pane dashboard designed for security analysts:
    * **Interactive Globe:** A 3D Mapbox globe provides a geographical overview of threats, with hotspots colored by severity.
    * **Dynamic Threat Chart:** A bar chart visualizes the breakdown of threats by category. Clicking a category filters the entire dashboard.
    * **Live Intelligence Feed:** A scrollable list of all incoming threats, providing at-a-glance awareness.
    * **Detailed Threat View:** Clicking any threat card or map point instantly provides a full breakdown, including an AI-generated summary and any extracted IoCs.

* **Autonomous Discovery (Extensible):** Includes a `DiscoveryAgent` powered by the Serper API, designed to autonomously find new CTI sources from the web, creating a self-expanding knowledge base.

---

## Technical Stack

* **Backend:** Python, Flask, Waitress, Schedule
* **AI / LLM:** Google Vertex AI (Gemini Pro)
* **Data Sources:** REST APIs (NIST, OTX, Serper), RSS Feeds (CISA), Web Scraping (BeautifulSoup)
* **Database:** SQLite
* **Frontend:** HTML, Tailwind CSS (via CDN), Chart.js, Mapbox GL JS

---

## Setup and Installation

Follow these steps to get the CTI Dashboard running on your local machine.

### 1. Prerequisites

* Python 3.9+
* A Google Cloud Platform (GCP) project with the **Vertex AI API enabled** and a valid **billing account** attached.
* A free **Mapbox** account to get an access token for the globe visualization.

### 2. Clone the Repository

```bash
git clone [https://panwgithub.paloaltonetworks.local/sat/Cyber-Threat-Intelligence-Dashboard]
cd [https://panwgithub.paloaltonetworks.local/sat/Cyber-Threat-Intelligence-Dashboard]
```

## 3. Set Up a Python Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies.
```bash
# Create the virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

## 4. Install Dependencies
Install all the required Python libraries using the requirements.txt file.
```bash
pip install -r requirements.txt
```

## 5. Configure Environment Variables
The application uses a .env file to manage API keys and secrets.

Create a new file named .env in the root of the project directory.
Add your keys to this file. At a minimum, you need your GCP Project ID and your Mapbox token.

```bash
# .env file

# REQUIRED: Your Google Cloud Project ID
GCP_PROJECT_ID="itd-ai-interns"

# Optional: Add these keys to enable more data sources
OTX_API_KEY=""
ABUSEIPDB_API_KEY=""
SERPER_API_KEY=""
```
## 6. Authenticate with Google Cloud
You need to authenticate your local machine so the application can access the Vertex AI API.

```bash
gcloud auth application-default login
#This will open a browser window for you to log in and approve the credentials.
```

---

## How to Run the Application


The application consists of two main components that must be run in separate terminals: the Backend Orchestrator and the Frontend Web Server.

### 1. Terminal 1: Run the Backend Orchestrator
The orchestrator is responsible for creating the database, collecting data from all sources, processing it with AI, and saving it.

Important: Run this script first and let it complete its initial data collection pass. This may take several minutes.

```bash
# Make sure your virtual environment is active
python orchestrator.py
```
### 2. Terminal 2: Run the Web Server
Once the orchestrator has run and populated the database, you can start the Flask web server.
```bash
# Open a new terminal and activate the virtual environment
source venv/bin/activate

# Run the Flask app
python app.py
```
This will start the web server, typically on http://0.0.0.0:8080.

---

Accessing the Dashboard
Open your web browser and navigate to:

```bash
http://localhost:8080
```


