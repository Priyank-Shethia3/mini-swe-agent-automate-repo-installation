import os
import glob
from pathlib import Path

def collect_profiles():
    # Find all profile_class.py files in the agent-result subdirectories
    profile_files = glob.glob("agent-result/*/generated_profiles/profile_class.py")
    profile_files.sort()  # Sort for deterministic output
    
    print(f"Found {len(profile_files)} profile files.")
    
    output_file = "javascript.py"

    with open(output_file, "w") as out:
        for f in profile_files:
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
                    else:
                        print(f"Warning: {f} has fewer than 6 lines, skipping.")
            except Exception as e:
                print(f"Error reading {f}: {e}")

    print(f"Successfully collected profiles into {output_file}")

if __name__ == "__main__":
    collect_profiles()
