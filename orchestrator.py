# import schedule
# import time
# from agents import DataIngestionAgent, IntelligenceExtractionAgent, IoCAnalysisAgent, PersistenceAgent, DiscoveryAgent # <-- Add DiscoveryAgent
# from database.db_handler import init_db
# from processor.vertex_ai_processor import check_ai_health

# def main_workflow():
#     """
#     The main orchestration function that coordinates all agents.
#     It runs a two-stage process for unstructured and structured data.
#     """
#     print("\n" + "="*50 + f"\nORCHESTRATOR: Starting new workflow run at {time.ctime()}\n" + "="*50)
    
#     # Initialize all necessary agents for the workflow
#     ingestion_agent = DataIngestionAgent()
#     extraction_agent = IntelligenceExtractionAgent()
#     analysis_agent = IoCAnalysisAgent()
#     persistence_agent = PersistenceAgent()

#     # --- Step 1: Process Unstructured Data (Needs AI) ---
#     print("\n--- Processing Unstructured Sources (CISA, NIST, News) ---")
#     raw_cisa = ingestion_agent.ingest_cisa()
    
#     # Increased limit for The Hacker News to get more data
#     raw_thn = ingestion_agent.ingest_hacker_news(limit=10)
    
#     raw_nist = ingestion_agent.ingest_nist_nvd(days=2)
#     unstructured_raw_data = raw_cisa + raw_thn + raw_nist
    
#     print(f"\nORCHESTRATOR: Ingested {len(unstructured_raw_data)} unstructured items for AI processing.")

#     for raw_item in unstructured_raw_data:
#         # Pass through the AI processing pipeline
#         pulse = extraction_agent.process_raw_data(raw_item)
#         if pulse:
#             # Enrich indicators if any are found
#             pulse['indicators'] = analysis_agent.enrich_indicators(pulse.get('indicators', []))
#             # Save the final, processed pulse to the database
#             persistence_agent.save_pulse(pulse)
#             print("-" * 20)

#     # --- Step 2: Process Structured Data from OTX (Bypasses AI) ---
#     print("\n--- Processing Structured Source (AlienVault OTX) ---")
#     otx_pulses = ingestion_agent.ingest_otx(limit=15)
#     print(f"\nORCHESTRATOR: Ingested {len(otx_pulses)} pre-structured OTX pulses.")
    
#     for pulse in otx_pulses:
#         # Data is already structured, so we just enrich and save
#         pulse['indicators'] = analysis_agent.enrich_indicators(pulse.get('indicators', []))
#         persistence_agent.save_pulse(pulse)
#         print("-" * 20)

#     print("\nORCHESTRATOR: Workflow run finished.")

# # --- NEW: A separate job function for the discovery agent ---
# def discovery_workflow():
#     """A dedicated workflow for discovering new sources."""
#     print("\n" + "="*50 + f"\nORCHESTRATOR: Starting Discovery Workflow at {time.ctime()}\n" + "="*50)
#     discovery_agent = DiscoveryAgent()
#     discovery_agent.run_discovery_cycle()
#     print("\nORCHESTRATOR: Discovery Workflow finished.")

# def main():
#     print("Initializing CTI Orchestrator...")
#     if not check_ai_health():
#         print("Aborting startup due to AI health check failure.")
#         return
#     init_db()
    
#     # Run the main data collection workflow once immediately
#     main_workflow()
    
#     # Schedule the main workflow to run every 2 hours
#     schedule.every(2).hours.do(main_workflow)
    
#     # --- NEW: Schedule the discovery workflow to run once a day ---
#     schedule.every().day.at("03:00").do(discovery_workflow) # Run at 3 AM
    
#     print("\nOrchestrator started. Data collection and discovery jobs are scheduled.")
#     print("Running initial discovery pass now...")
#     discovery_workflow() # Also run discovery once on startup
    
#     while True:
#         schedule.run_pending()
#         time.sleep(60)

# if __name__ == "__main__":
#     main()








# import time
# from agents import DiscoveryAgent  # We only need the DiscoveryAgent for this test
# from database.db_handler import init_db

# def test_serper_discovery():
#     """
#     A temporary function to ONLY test the Serper API integration.
#     It will find top threats and print the URLs it discovers.
#     """
#     print("\n" + "="*50)
#     print("--- STARTING SERPER API TEST ---")
#     print("="*50)

#     discovery_agent = DiscoveryAgent()

#     # Step 1: Get top threat names from the database to use as search terms
#     print("\n[Step 1] Getting top threat names from the database...")
#     threats_to_search = discovery_agent._get_top_threat_names(limit=3) # Limit to 3 for a quick test

#     if not threats_to_search:
#         print("\n[RESULT] No existing threats found in the database to search for.")
#         print("Please run the full orchestrator once to populate the DB with some data.")
#         print("--- SERPER API TEST FINISHED ---")
#         return

#     print(f"[SUCCESS] Found threats to search for: {threats_to_search}")

#     # Step 2: For each threat, search using the Serper API
#     print("\n[Step 2] Querying Serper API for each threat...")
#     all_discovered_links = set()
#     for threat in threats_to_search:
#         links = discovery_agent.search_for_sources(threat)
#         if links:
#             print(f"  -> Found {len(links)} links for '{threat}'")
#             for link in links:
#                 all_discovered_links.add(link)
#         else:
#             print(f"  -> No links found for '{threat}'")
#         time.sleep(1) # Be polite to the API

#     # Step 3: Print the final, unique list of discovered URLs
#     print("\n" + "="*50)
#     print("--- FINAL RESULTS ---")
#     print("="*50)
    
#     if all_discovered_links:
#         print(f"Successfully discovered a total of {len(all_discovered_links)} unique URLs:\n")
#         for i, link in enumerate(all_discovered_links, 1):
#             print(f"{i}. {link}")
#     else:
#         print("The Serper API test ran, but did not discover any new URLs.")
#         print("This could be normal if the search terms didn't yield new results.")

#     print("\n--- SERPER API TEST FINISHED ---")


# if __name__ == "__main__":
#     print("Initializing Serper API Test...")
#     # We still need to initialize the DB to get the search terms
#     init_db() 
    
#     # Run the test function directly
#     test_serper_discovery()



import schedule
import time
from agents import (
    DiscoveryAgent, 
    IntelligenceExtractionAgent, 
    IoCAnalysisAgent, 
    PersistenceAgent, 
    CorrelationAgent,
    scrape_url_to_raw_data # Import the new utility function
)
from database.db_handler import init_db
from processor.vertex_ai_processor import check_ai_health

def autonomous_workflow():
    """
    The main autonomous workflow. It discovers, scrapes, and processes in a single run.
    """
    print("\n" + "="*50 + f"\nORCHESTRATOR: Starting Autonomous Discovery & Ingestion Cycle at {time.ctime()}\n" + "="*50)
    
    # Initialize all necessary agents
    discovery_agent = DiscoveryAgent()
    extraction_agent = IntelligenceExtractionAgent()
    analysis_agent = IoCAnalysisAgent()
    persistence_agent = PersistenceAgent()
    correlation_agent = CorrelationAgent()

    # --- Step 1: Discover new URLs from the web ---
    urls_to_process = discovery_agent.discover_and_fetch_urls()

    if not urls_to_process:
        print("ORCHESTRATOR: No new URLs discovered in this cycle.")
        print("\nORCHESTRATOR: Workflow finished.")
        return

    # --- Step 2: Process each discovered URL ---
    print(f"\nORCHESTRATOR: Beginning processing for {len(urls_to_process)} URLs...")
    for url in urls_to_process:
        # Scrape the URL to get raw data
        raw_item = scrape_url_to_raw_data(url)
        
        if raw_item:
            # Pass the raw data through the AI processing pipeline
            print(f"--- PIPELINE START: {raw_item['title']} ---")
            pulse = extraction_agent.process_raw_data(raw_item)
            if pulse:
                pulse['indicators'] = analysis_agent.enrich_indicators(pulse.get('indicators', []))
                new_pulse_id = persistence_agent.save_pulse(pulse)
                if new_pulse_id:
                    correlation_agent.correlate_pulse(new_pulse_id, pulse)
            print("--- PIPELINE END ---")
            print("-" * 20)
            time.sleep(2) # Small delay between processing each URL

    print("\nORCHESTRATOR: Autonomous cycle finished.")

def main():
    """
    Main function to initialize and run the discovery-focused orchestrator.
    """
    print("Initializing CTI Orchestrator (Autonomous Discovery Mode)...")
    
    if not check_ai_health():
        print("Aborting startup due to AI health check failure.")
        return

    init_db()
    
    # Run the autonomous workflow once immediately on startup
    autonomous_workflow()
    
    # Schedule the workflow to run every 30 minutes
    schedule.every(30).minutes.do(autonomous_workflow)
    
    print("\nOrchestrator started. Autonomous discovery jobs are scheduled.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
