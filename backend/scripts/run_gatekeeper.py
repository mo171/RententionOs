import argparse
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.gatekeeper.gatekeeper_pipeline import process_gatekeeper_pipeline

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "indian_bank_profiles.csv")

def main():
    parser = argparse.ArgumentParser(description="Run the RetentionOS Gatekeeper Pipeline")
    parser.add_argument("--count", type=int, default=10000, help="Number of profiles to process")
    parser.add_argument("--trigger", action="store_true", help="Trigger Inngest event for qualified profiles")
    args = parser.parse_args()
    
    if not os.path.exists(DATA_PATH):
        print(f"Data file not found: {DATA_PATH}")
        sys.exit(1)
        
    print(f"Loading {args.count} profiles from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    if len(df) > args.count:
        df = df.head(args.count)
        
    customers = df.to_dict('records')
    # Add dummy user_ids since the CSV doesn't have them
    for i, c in enumerate(customers):
        c['user_id'] = i + 1
        
    print("Running Gatekeeper pipeline...")
    payloads = process_gatekeeper_pipeline(customers, trigger_inngest=args.trigger)
    
    print(f"\nPipeline completed. Found {len(payloads)} persuadable users with profitable treatments.")
    if len(payloads) > 0:
        print("\nSample payload:")
        print(payloads[0].model_dump_json(indent=2))

if __name__ == "__main__":
    main()
