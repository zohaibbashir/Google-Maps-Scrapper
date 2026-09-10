import subprocess
import time

# List of search tasks: (search_query, target_total_results)
TASKS = [
    ("solo lawyer in Katy TX", 15),
    ("family law attorney in Plano TX", 15),
    ("general contractor in Fort Worth TX", 20),
    ("consulting engineer in Frisco TX", 15),
    ("estate attorney in Boca Raton FL", 15),
    ("solo DUI lawyer in Pensacola FL", 15),
    ("private medical clinic in Sarasota FL", 20),
    ("subcontractor in Cape Coral FL", 20),
    ("family law practice in Cary NC", 15),
    ("residential trade contractor in Wilmington NC", 20),
    ("solo lawyer in Alpharetta GA", 15),
    ("criminal defense attorney in Marietta GA", 15),
    ("solo lawyer in Akron OH", 15),
    ("general contractor in Toledo OH", 20),
]

OUTPUT_FILE = "leads_batch.csv"

def run_batch():
    for index, (query, total) in enumerate(TASKS, start=1):
        print(f"\n==========================================")
        print(f"[{index}/{len(TASKS)}] Starting search for: '{query}' (Target: {total})")
        print(f"==========================================\n")
        
        # Build command: uses --append to save everything into one CSV file
        cmd = [
            "python", "main.py",
            "-s", query,
            "-t", str(total),
            "-o", OUTPUT_FILE,
            "--append"
        ]
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[!] Error running scrape for '{query}': {e}")
        except KeyboardInterrupt:
            print("\n[!] Batch run manually interrupted by user.")
            break
            
        # Brief cooldown between queries to prevent aggressive Google rate limiting
        time.sleep(5)

if __name__ == "__main__":
    run_batch()