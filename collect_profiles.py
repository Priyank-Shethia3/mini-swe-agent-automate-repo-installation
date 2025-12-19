import os
import json
import glob
from pathlib import Path

# Standard parsers that we include
STANDARD_PARSERS = {'jest', 'mocha', 'vitest', 'karma', 'jasmine'}

def get_parser_for_repo(repo_dir):
    """Get the parser used by a repository."""
    parsed_status_path = Path(repo_dir) / "parsed_test_status.json"
    
    if not parsed_status_path.exists():
        return None
    
    try:
        with open(parsed_status_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            parser = data.get('parser', '')
            return parser
    except Exception:
        return None

def is_standard_parser(parser_name):
    """Check if the parser is one of our standard ones."""
    if not parser_name:
        return False
    
    # Handle combined parsers like "jest+mocha"
    parsers = parser_name.lower().split('+')
    
    # Check if any of the parsers in the combination is a standard one
    for p in parsers:
        p = p.strip()
        if p in STANDARD_PARSERS:
            return True
    
    return False

def collect_profiles():
    # Find all profile_class.py files in the agent-result subdirectories
    profile_files = glob.glob("agent-result/*/generated_profiles/profile_class.py")
    profile_files.sort()  # Sort for deterministic output
    
    print(f"Found {len(profile_files)} profile files.")
    
    output_file = "javascript.py"
    included_count = 0
    excluded_count = 0
    excluded_repos = []

    with open(output_file, "w") as out:
        for f in profile_files:
            # Extract repo directory from path
            repo_dir = Path(f).parent.parent  # Go up from profile_class.py -> generated_profiles -> repo_dir
            repo_name = repo_dir.name
            
            # Check if this repo uses a standard parser
            parser = get_parser_for_repo(repo_dir)
            
            if not is_standard_parser(parser):
                excluded_count += 1
                excluded_repos.append((repo_name, parser))
                print(f"  Excluding {repo_name} (parser: {parser})")
                continue
            
            try:
                with open(f, "r") as src:
                    lines = src.readlines()
                    
                    # Remove the first 5 lines as requested
                    # (These are typically the 4 comment lines and the 1 empty line)
                    if len(lines) > 5:
                        content = lines[5:]
                        out.writelines(content)
                        # Ensure there's a couple of newlines between classes
                        out.write("\n\n")
                        included_count += 1
                    else:
                        print(f"Warning: {f} has fewer than 6 lines, skipping.")
            except Exception as e:
                print(f"Error reading {f}: {e}")

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Included: {included_count} profiles")
    print(f"  Excluded: {excluded_count} profiles (non-standard parsers)")
    print(f"  Output file: {output_file}")
    
    if excluded_repos:
        print(f"\nExcluded repos:")
        for repo, parser in excluded_repos:
            print(f"  - {repo}: {parser}")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    collect_profiles()
