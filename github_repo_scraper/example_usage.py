#!/usr/bin/env python3
"""
Example usage of the GitHub Repository Scraper
"""

from github_repo_scraper import GitHubScraper, save_to_csv, save_to_json
import os


def example_basic_search():
    """Basic repository search example"""
    print("=== Basic Search Example ===")

    # Initialize scraper (token from environment)
    scraper = GitHubScraper(token=os.getenv("GITHUB_TOKEN"))

    # Search for popular Python repositories
    repos = scraper.search_repositories(language="python", min_stars=1000, max_pages=2)

    print(f"Found {len(repos)} Python repositories with 1000+ stars")

    # Show top 5 repositories
    for i, repo in enumerate(repos[:5]):
        print(f"{i + 1}. {repo.full_name} ({repo.stars} stars)")

    return repos


def example_trending_projects():
    """Find trending projects created recently"""
    print("\n=== Trending Projects Example ===")

    scraper = GitHubScraper(token=os.getenv("GITHUB_TOKEN"))

    # Search for repositories created in the last 6 months with good activity
    repos = scraper.search_repositories(
        created_after="2024-02-01", min_stars=50, sort="stars", max_pages=3
    )

    print(f"Found {len(repos)} trending repositories from the last 6 months")

    # Group by language
    by_language = {}
    for repo in repos:
        lang = repo.language or "Unknown"
        if lang not in by_language:
            by_language[lang] = []
        by_language[lang].append(repo)

    print("\nTop repositories by language:")
    for lang, lang_repos in sorted(
        by_language.items(), key=lambda x: len(x[1]), reverse=True
    )[:5]:
        print(f"{lang}: {len(lang_repos)} repos")
        top_repo = max(lang_repos, key=lambda r: r.stars)
        print(f"  Top: {top_repo.full_name} ({top_repo.stars} stars)")

    return repos


def example_specific_language():
    """Search for repositories in a specific language with filtering"""
    print("\n=== Language-Specific Search Example ===")

    scraper = GitHubScraper(token=os.getenv("GITHUB_TOKEN"))

    # Search for Rust repositories
    repos = scraper.search_repositories(
        language="rust",
        min_stars=100,
        pushed_after="2024-01-01",  # Recently active
        sort="updated",
        max_pages=2,
    )

    print(f"Found {len(repos)} active Rust repositories")

    # Find repositories with specific topics
    web_repos = [
        r
        for r in repos
        if any(topic in ["web", "http", "server"] for topic in r.topics)
    ]
    cli_repos = [
        r
        for r in repos
        if any(topic in ["cli", "command-line", "terminal"] for topic in r.topics)
    ]

    print(f"Web-related: {len(web_repos)}")
    print(f"CLI-related: {len(cli_repos)}")

    return repos


def example_save_and_analyze():
    """Save data and perform basic analysis"""
    print("\n=== Save and Analysis Example ===")

    scraper = GitHubScraper(token=os.getenv("GITHUB_TOKEN"))

    # Search for JavaScript repositories
    repos = scraper.search_repositories(
        language="javascript", min_stars=500, max_pages=3
    )

    # Save to both formats
    save_to_csv(repos, "javascript_repos.csv")
    save_to_json(repos, "javascript_repos.json")

    # Basic analysis
    total_stars = sum(repo.stars for repo in repos)
    avg_stars = total_stars / len(repos) if repos else 0

    # Find most forked
    most_forked = max(repos, key=lambda r: r.forks) if repos else None

    # Find most recent
    most_recent = max(repos, key=lambda r: r.created_at) if repos else None

    print("JavaScript repositories analysis:")
    print(f"Total repositories: {len(repos)}")
    print(f"Average stars: {avg_stars:.1f}")
    print(f"Total stars: {total_stars:,}")

    if most_forked:
        print(f"Most forked: {most_forked.full_name} ({most_forked.forks} forks)")

    if most_recent:
        print(
            f"Most recent: {most_recent.full_name} (created {most_recent.created_at[:10]})"
        )

    return repos


def main():
    """Run all examples"""
    # Check if token is available
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Warning: No GITHUB_TOKEN environment variable set.")
        print("You can still run the examples but with lower rate limits.")
        print("Set your token with: export GITHUB_TOKEN=your_token_here\n")

    try:
        # Run examples
        repos1 = example_basic_search()
        repos2 = example_trending_projects()
        repos3 = example_specific_language()
        repos4 = example_save_and_analyze()

        print("\n=== Summary ===")
        print(
            f"Total repositories found across all examples: {len(repos1) + len(repos2) + len(repos3) + len(repos4)}"
        )

    except Exception as e:
        print(f"Error running examples: {e}")
        print("This might be due to rate limiting or network issues.")


if __name__ == "__main__":
    main()
