import schedule
import time
from agents import DataIngestionAgent, IntelligenceExtractionAgent, IoCAnalysisAgent, PersistenceAgent
from database.db_handler import init_db
from processor.vertex_ai_processor import check_ai_health

def main_workflow():
    """
    The main orchestration function that coordinates all agents.
    It runs a two-stage process for unstructured and structured data.
    """
    print("\n" + "="*50 + f"\nORCHESTRATOR: Starting new workflow run at {time.ctime()}\n" + "="*50)
    
    # Initialize all necessary agents for the workflow
    ingestion_agent = DataIngestionAgent()
    extraction_agent = IntelligenceExtractionAgent()
    analysis_agent = IoCAnalysisAgent()
    persistence_agent = PersistenceAgent()

    # --- Step 1: Process Unstructured Data (Needs AI) ---
    print("\n--- Processing Unstructured Sources (CISA, NIST, News) ---")
    raw_cisa = ingestion_agent.ingest_cisa()
    raw_thn = ingestion_agent.ingest_hacker_news(limit=10)
    raw_nist = ingestion_agent.ingest_nist_nvd(days=2)
    unstructured_raw_data = raw_cisa + raw_thn + raw_nist
    
    print(f"\nORCHESTRATOR: Ingested {len(unstructured_raw_data)} unstructured items for AI processing.")

    for raw_item in unstructured_raw_data:
        pulse = extraction_agent.process_raw_data(raw_item)
        if pulse:
            pulse['indicators'] = analysis_agent.enrich_indicators(pulse.get('indicators', []))
            persistence_agent.save_pulse(pulse)
            print("-" * 20)

    # --- Step 2: Process Structured Data from OTX (Bypasses AI) ---
    print("\n--- Processing Structured Source (AlienVault OTX) ---")
    otx_pulses = ingestion_agent.ingest_otx(limit=15)
    print(f"\nORCHESTRATOR: Ingested {len(otx_pulses)} pre-structured OTX pulses.")
    
    for pulse in otx_pulses:
        pulse['indicators'] = analysis_agent.enrich_indicators(pulse.get('indicators', []))
        persistence_agent.save_pulse(pulse)
        print("-" * 20)

    print("\nORCHESTRATOR: Workflow run finished.")

def main():
    """
    Main function to initialize and run the CTI orchestrator.
    """
    print("Initializing CTI Orchestrator...")
    
    if not check_ai_health():
        print("Aborting startup due to AI health check failure.")
        return

    init_db()
    
    main_workflow()
    
    schedule.every(2).hours.do(main_workflow)
    
    print("\nOrchestrator started. Next run is scheduled in 2 hours.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
