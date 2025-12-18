import csv
import subprocess
import os
import sys
import argparse

def main():
    csv_path = './github_repo_scraper/new_curated_repos.csv'
    model = 'claude-sonnet-4-5-20250929'
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Generate profiles for a range of repositories.")
    parser.add_argument('--range', type=str, default='0-50', help='Range of repositories to process (e.g., "0-50", exclusive of the end index).')
    args = parser.parse_args()

    try:
        if '-' in args.range:
            start_idx, end_idx = map(int, args.range.split('-'))
        else:
            print("Error: Range must be in the format 'start-end'.")
            sys.exit(1)
    except ValueError:
        print("Error: Range must contain valid integer indices.")
        sys.exit(1)

    repos = []
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < start_idx:
                continue
            if i >= end_idx:
                break
            # full_name is the identifier used by generate_profile.py
            repos.append({
                'full_name': row['full_name'],
                'language': row.get('language', '').lower()
            })

    print(f"Starting to process {len(repos)} repositories...")

    for i, repo_info in enumerate(repos):
        full_name = repo_info['full_name']
        language = repo_info['language']
        
        # Skip if already exists
        result_dir = os.path.join('agent-result', full_name.replace('/', '-'))
        if os.path.exists(result_dir):
            print(f"\n[{i+1}/{len(repos)}] Skipping {full_name} (already exists in agent-result/)")
            continue
            
        print(f"\n[{i+1}/{len(repos)}] Generating profile for {full_name}...")
        
        cmd = ['python', 'generate_profile.py', full_name, '--model', model, '--max-cost', '0.2', '--max-time', '300']
        
        # If the repository is identified as Python, add the --python-repo flag
        if language == 'python':
            cmd.append('--python-repo')
            
        try:
            # Impose a timeout
            # check=False ensures it doesn't raise CalledProcessError automatically, 
            # allowing us to handle it ourselves or simply move on.
            result = subprocess.run(cmd, check=False, timeout=600)
            
            if result.returncode != 0:
                print(f"⚠️  Command for {full_name} returned non-zero exit code: {result.returncode}")
            else:
                print(f"✅ Successfully finished {full_name}")

        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout: generate_profile.py for {full_name} exceeded timeout. Moving to next repo.")
        except KeyboardInterrupt:
            print("\nProcessing interrupted by user. Exiting...")
            break
        except Exception as e:
            # Broad exception catch to ensure we advance to the next repo no matter what
            print(f"❌ An error occurred for {full_name}: {e}")
            print(f"Proceeding to next repository...")

if __name__ == "__main__":
    main()
