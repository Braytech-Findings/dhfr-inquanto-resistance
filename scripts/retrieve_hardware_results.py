#!/usr/bin/env python3
"""
Retrieve VQE results from Quantinuum Nexus.
"""

import argparse
import uuid
import json
import sys
import pathlib
import qnexus as qnx

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results" / "tables"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description="Retrieve VQE results from Quantinuum Nexus")
    parser.add_argument("--job-id", required=True, help="Job UUID")
    parser.add_argument("--system", default="WT_TMP", help="System ID (e.g. WT_TMP)")
    args = parser.parse_args()

    qnx.login()
    
    try:
        job_id = uuid.UUID(args.job_id)
    except ValueError:
        print(f"❌ Invalid UUID format: {args.job_id}")
        sys.exit(1)

    print(f"🔎 Fetching results for job {job_id}...")
    try:
        job = qnx.jobs.get(job_id)
        status = qnx.jobs.status(job)
        
        if status.status.value != "COMPLETED":
            print(f"⚠️ Job is not completed yet. Current status: {status.status.value}")
            sys.exit(0)
            
        results_ref = qnx.jobs.results(job)
        if not results_ref:
            print("❌ No results found in completion info.")
            sys.exit(1)
            
        # Download the pytket BackendResult object
        result = results_ref[0].download_result()
        counts = result.get_counts()
        print("✅ Results retrieved successfully!")
        print("📊 Measurement Counts:")
        
        # Sort and print counts
        sorted_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        for state, count in sorted_counts[:10]:
            print(f"   {state}: {count}")
        if len(sorted_counts) > 10:
            print(f"   ... ({len(sorted_counts) - 10} other states)")
            
        # Save to file
        # Convert state keys (tuples or bitstrings) to strings for JSON serializability
        serializable_counts = {str(k): int(v) for k, v in counts.items()}
        output_path = RESULTS_DIR / f"{args.system}_hardware_results.json"
        with open(output_path, "w") as f:
            json.dump({
                "job_id": str(job_id),
                "system": args.system,
                "counts": serializable_counts
            }, f, indent=2)
        print(f"💾 Saved results to {output_path}")

    except Exception as e:
        print(f"❌ Failed to retrieve results: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
