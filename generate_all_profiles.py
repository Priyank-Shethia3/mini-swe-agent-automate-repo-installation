import csv
import subprocess
import os
import sys
import argparse

def main():
    csv_path = './github_repo_scraper/new_curated_repos.csv'
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Generate profiles for a range of repositories.")
    parser.add_argument('--range', type=str, default='0-50', help='Range of repositories to process (e.g., "0-50", exclusive of the end index).')
    parser.add_argument('--model', type=str, default='gemini/gemini-3-flash-preview', help='Model to use for generation.')
    parser.add_argument('--verify', action='store_true', help='Instruct the agent to verify generated Dockerfiles by building them.')
    parser.add_argument('--verify-testing', action='store_true', help='Instruct the agent to also run verify_testing.py to parse test output (implies --verify).')
    parser.add_argument('--livestream', action='store_true', help='Enable real-time output streaming from the agent.')
    args = parser.parse_args()

    model = args.model

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
    
    # Initialize statistics tracking
    stats = {
        'total_attempted': 0,
        'total_skipped': 0,
        'dockerfile_generated': 0,
        'dockerfile_verified': 0,
        'testing_verified': 0,
        'failed': 0,
        'timeout': 0
    }

    for i, repo_info in enumerate(repos):
        full_name = repo_info['full_name']
        language = repo_info['language']
        
        # Skip if already exists
        result_dir = os.path.join('agent-result', full_name.replace('/', '-'))
        if os.path.exists(result_dir):
            print(f"\n[{i+1}/{len(repos)}] Skipping {full_name} (already exists in agent-result/)")
            stats['total_skipped'] += 1
            continue
            
        print(f"\n[{i+1}/{len(repos)}] Generating profile for {full_name}...")
        stats['total_attempted'] += 1
        
        cmd = ['python', 'generate_profile.py', full_name, '--model', model, '--max-cost', '0.2', '--max-time', '1200']
        
        # If the repository is identified as Python, add the --python-repo flag
        if language == 'python':
            cmd.append('--python-repo')
        
        # If verify flag is set, add it to the command
        # Note: --verify-testing implies --verify
        if args.verify or args.verify_testing:
            cmd.append('--verify')
        
        # If verify-testing flag is set, add it to the command
        if args.verify_testing:
            cmd.append('--verify-testing')
        
        # If livestream flag is set, add it to the command
        if args.livestream:
            cmd.append('--livestream')
            
        try:
            # Impose a timeout (slightly longer than agent's max-time to allow graceful completion)
            # check=False ensures it doesn't raise CalledProcessError automatically, 
            # allowing us to handle it ourselves or simply move on.
            result = subprocess.run(cmd, check=False, timeout=1500)
            
            if result.returncode != 0:
                print(f"⚠️  Command for {full_name} returned non-zero exit code: {result.returncode}")
                stats['failed'] += 1
            else:
                print(f"✅ Successfully finished {full_name}")

        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout: generate_profile.py for {full_name} exceeded timeout. Moving to next repo.")
            stats['timeout'] += 1
        except KeyboardInterrupt:
            print("\nProcessing interrupted by user. Exiting...")
            break
        except Exception as e:
            # Broad exception catch to ensure we advance to the next repo no matter what
            print(f"❌ An error occurred for {full_name}: {e}")
            print(f"Proceeding to next repository...")
            stats['failed'] += 1
        
        # Check result directory for completion status
        if os.path.exists(result_dir):
            dockerfile_path = os.path.join(result_dir, 'Dockerfile')
            test_output_path = os.path.join(result_dir, 'test_output.txt')
            parsed_status_path = os.path.join(result_dir, 'parsed_test_status.json')
            
            if os.path.exists(dockerfile_path):
                stats['dockerfile_generated'] += 1
            
            if os.path.exists(test_output_path):
                stats['dockerfile_verified'] += 1
            
            if os.path.exists(parsed_status_path):
                stats['testing_verified'] += 1
        
        # Print updated statistics
        print(f"\n📊 Statistics (after {i+1}/{len(repos)} repos):")
        print(f"   Total attempted:      {stats['total_attempted']}")
        print(f"   Total skipped:        {stats['total_skipped']}")
        print(f"   Dockerfile generated: {stats['dockerfile_generated']}")
        print(f"   Dockerfile verified:  {stats['dockerfile_verified']}")
        print(f"   Testing verified:     {stats['testing_verified']}")
        print(f"   Failed:               {stats['failed']}")
        print(f"   Timeout:              {stats['timeout']}")
        
        # Calculate success rates
        if stats['total_attempted'] > 0:
            gen_rate = (stats['dockerfile_generated'] / stats['total_attempted']) * 100
            ver_rate = (stats['dockerfile_verified'] / stats['total_attempted']) * 100
            test_rate = (stats['testing_verified'] / stats['total_attempted']) * 100
            print(f"   Success rates: Gen={gen_rate:.1f}% | Ver={ver_rate:.1f}% | Test={test_rate:.1f}%")
        print("=" * 60)
    
    # Print final summary
    print(f"\n\n{'=' * 60}")
    print(f"🎯 FINAL SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total repositories in range:  {len(repos)}")
    print(f"Skipped (already exist):      {stats['total_skipped']}")
    print(f"Attempted:                    {stats['total_attempted']}")
    print(f"")
    print(f"Results:")
    print(f"  ✅ Dockerfile generated:    {stats['dockerfile_generated']}")
    print(f"  ✅ Dockerfile verified:     {stats['dockerfile_verified']}")
    print(f"  ✅ Testing verified:        {stats['testing_verified']}")
    print(f"  ❌ Failed:                  {stats['failed']}")
    print(f"  ⏰ Timeout:                 {stats['timeout']}")
    
    if stats['total_attempted'] > 0:
        gen_rate = (stats['dockerfile_generated'] / stats['total_attempted']) * 100
        ver_rate = (stats['dockerfile_verified'] / stats['total_attempted']) * 100
        test_rate = (stats['testing_verified'] / stats['total_attempted']) * 100
        print(f"")
        print(f"Success rates (of attempted):")
        print(f"  Dockerfile generation: {gen_rate:.1f}% ({stats['dockerfile_generated']}/{stats['total_attempted']})")
        print(f"  Dockerfile verified:   {ver_rate:.1f}% ({stats['dockerfile_verified']}/{stats['total_attempted']})")
        print(f"  Testing verified:      {test_rate:.1f}% ({stats['testing_verified']}/{stats['total_attempted']})")
    print(f"{'=' * 60}\n")

if __name__ == "__main__":
    main()
