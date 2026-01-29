#!/usr/bin/env python3
"""
Filter repositories by license

Filters repos.json to only include repositories with permissive/research-safe licenses:
- Apache License (all versions)
- MIT License
- BSD License (all variants)
- GNU General Public License v3.0 (GPLv3)
"""

import json
import sys


def is_allowed_license(license_name):
    """
    Check if a license is in the allowed list

    Args:
        license_name: License name from GitHub (can be None)

    Returns:
        Boolean indicating if license is allowed
    """
    if not license_name:
        return False

    license_lower = license_name.lower()

    # Allowed license keywords
    allowed_keywords = [
        "apache",
        "mit",
        "bsd",
        "gpl-3",
        "gplv3",
        "gnu general public license v3",
    ]

    return any(keyword in license_lower for keyword in allowed_keywords)


def filter_repos_by_license(input_file, output_file):
    """
    Filter repositories by license

    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
    """
    print(f"Reading repositories from {input_file}...")

    # Load repositories
    with open(input_file, "r", encoding="utf-8") as f:
        repos = json.load(f)

    print(f"Total repositories: {len(repos)}")

    # Filter by license
    filtered_repos = []
    license_counts = {}

    for repo in repos:
        license_name = repo.get("license")

        if is_allowed_license(license_name):
            filtered_repos.append(repo)

            # Count licenses
            if license_name not in license_counts:
                license_counts[license_name] = 0
            license_counts[license_name] += 1

    print(f"\nFiltered repositories: {len(filtered_repos)}")
    print(f"Removed: {len(repos) - len(filtered_repos)}")

    # Print license breakdown
    print("\nLicense breakdown:")
    for license_name, count in sorted(
        license_counts.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {license_name}: {count}")

    # Save filtered results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered_repos, f, indent=2, ensure_ascii=False)

    print(f"\nSaved filtered repositories to {output_file}")

    # Print some examples
    print("\nExample repositories (top 5 by stars):")
    sorted_repos = sorted(
        filtered_repos, key=lambda r: r.get("stars", 0), reverse=True
    )[:5]
    for i, repo in enumerate(sorted_repos, 1):
        print(f"{i}. {repo['full_name']}")
        print(f"   License: {repo['license']}")
        print(f"   Stars: {repo.get('stars', 0):,}")
        print(f"   URL: {repo['url']}\n")


def main():
    input_file = "github_repo_scraper/repos.json"
    output_file = "github_repo_scraper/repos_filtered_by_license.json"

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    try:
        filter_repos_by_license(input_file, output_file)
    except FileNotFoundError:
        print(f"Error: Could not find {input_file}")
        print(f"Usage: python {sys.argv[0]} [input_file] [output_file]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_file}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
