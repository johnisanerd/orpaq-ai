import asyncio
import sys
import os

# Set PYTHONPATH to include the backend directory correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, "backend")
sys.path.insert(0, backend_path)

# Mock environment variables for testing if .env is missing or invalid
os.environ["SUPABASE_URL"] = os.environ.get("SUPABASE_URL", "https://mock.supabase.co")
os.environ["SUPABASE_KEY"] = os.environ.get("SUPABASE_KEY", "mock-key")

from app.services.pipeline import pipeline_service

async def verify():
    print("🚀 Verifying Orpaq AI Pipeline...")
    
    # Run pipeline with a small limit and mock source to avoid API costs/dependencies
    result = await pipeline_service.run_full_pipeline(
        location="New York", 
        category="restaurants", 
        limit=2
    )
    
    print("\n--- Pipeline Result ---")
    print(f"Status: {result['status']}")
    print(f"Businesses Found: {result['businesses_found']}")
    print(f"Leads Generated: {result['leads_generated']}")
    
    if result['errors']:
        print("\n❌ Errors encountered:")
        for error in result['errors']:
            print(f"  - {error}")
            
    if result['status'] == 'completed' and result['leads_generated'] > 0:
        print("\n✅ Verification Successful: Pipeline is operational.")
        
        # Fetch the generated lead from memory to show the result
        from app.services.database import db
        leads = db.get_leads(limit=1)
        if leads:
            lead = leads[0]
            print(f"\n--- Sample Generated Lead ---")
            print(f"Business: {lead['businesses'].get('name')}")
            print(f"Category: {lead['businesses'].get('category')}")
            print(f"Score: {lead['lead_score']} ({lead['priority']})")
            print(f"Outreach Message preview: {lead['outreach_message'][:150]}...")
            print(f"Redesign Suggestions: {lead['redesign_suggestions']}")
    else:
        print("\n⚠️ Verification Partial: Check errors above.")

if __name__ == "__main__":
    asyncio.run(verify())
