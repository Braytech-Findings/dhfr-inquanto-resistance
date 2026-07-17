#!/usr/bin/env python3
"""
Monitor execution job on Quantinuum Nexus.
"""

import argparse
import uuid
import sys
import qnexus as qnx

def main():
    parser = argparse.ArgumentParser(description="Monitor execution job on Quantinuum Nexus")
    parser.add_argument("--job-id", required=True, help="Job UUID")
    args = parser.parse_args()

    qnx.login()
    
    try:
        job_id = uuid.UUID(args.job_id)
    except ValueError:
        print(f"❌ Invalid UUID format: {args.job_id}")
        sys.exit(1)

    print(f"🔎 Fetching status for job {job_id}...")
    try:
        job = qnx.jobs.get(job_id)
        status = qnx.jobs.status(job)
        print(f"✅ Job Found!")
        print(f"   Status: {status.status.value}")
        if status.queue_position is not None:
            print(f"   Queue Position: {status.queue_position}")
        if status.submitted_time is not None:
            print(f"   Submitted At: {status.submitted_time}")
        if status.running_time is not None:
            print(f"   Running At: {status.running_time}")
        if status.completed_time is not None:
            print(f"   Completed At: {status.completed_time}")
        if status.error_detail:
            print(f"   Error Detail: {status.error_detail}")
    except Exception as e:
        print(f"❌ Failed to fetch job: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
