import csv
import re
import os
import random
import argparse
import requests
import time


def curate_repos(
    input_path,
    output_path,
    exclude_android=False,
    min_java_percentage=None,
    token=None,
    require_software_indicator=False,
):
    # Aggressive exclude list for informational repositories
    exclude_keywords = {
        # Documentation/Educational
        "awesome",
        "list",
        "awesome-list",
        "awesome list",
        "learning",
        "learn",
        "tutorial",
        "tutorials",
        "tut",
        "interview",
        "interviews",
        "interview-questions",
        "interview questions",
        "cheatsheet",
        "cheatsheets",
        "cheat sheet",
        "cheat-sheet",
        "roadmap",
        "roadmaps",
        "learning-path",
        "learning path",
        "guide",
        "guides",
        "handbook",
        "handbooks",
        "book",
        "books",
        "textbook",
        "textbooks",
        "course",
        "courses",
        "curriculum",
        "curricula",
        "lessons",
        "lesson",
        "lecture",
        "lectures",
        "education",
        "educational",
        "teaching",
        "teach",
        "syllabus",
        "syllabi",
        "program",
        "programs",
        "training",
        "workshop",
        "workshops",
        # Reference/Collection
        "collection",
        "collections",
        "compilation",
        "resource",
        "resources",
        "reference",
        "references",
        "examples",
        "example",
        "sample",
        "samples",
        "patterns",
        "design-patterns",
        "design patterns",
        "snippets",
        "snippet",
        "code-snippets",
        "code snippets",
        "recipes",
        "recipe",
        # Knowledge Base
        "notes",
        "note",
        "study",
        "studies",
        "studying",
        "knowledge",
        "know-how",
        "documentation",
        "wiki",
        "wikipedia",
        "faq",
        "faqs",
        "q&a",
        "qa",
        "questions",
        "answers",
        # Theory/Concepts
        "concepts",
        "concept",
        "theory",
        "theories",
        "principles",
        "principle",
        "fundamentals",
        "algorithms",
        "algorithm",
        "data-structures",
        "data structures",
        "practices",
        "practice",
        "best-practices",
        "best practices",
        "standard",
        "standards",
        "specification",
        "specifications",
        "style-guide",
        "style guide",
        "styleguide",
        "conventions",
        "convention",
        # Solutions/Answers
        "solutions",
        "solution",
        "solved",
        "solve",
        "exercises",
        "exercise",
        "problems",
        "problem",
        "challenges",
        "challenge",
        "puzzles",
        "puzzle",
        "assignments",
        "assignment",
        # Tips/Tricks
        "tips",
        "tip",
        "tricks",
        "trick",
        "hacks",
        "hack",
        "hacking",
        "summary",
        "summaries",
        "overview",
        "overviews",
        # Translation/Localization
        "translation",
        "translations",
        "translated",
        "chinese",
        "中文",
        "english",
        "pronunciation",
        # Other informational
        "record",
        "records",
        "logs",
        "log",
        "blog",
        "blogs",
        "article",
        "articles",
        "post",
        "posts",
        "story",
        "stories",
        "readme",
        "read-me",
        "getting-started",
        "getting started",
        "quick-start",
        "quick start",
        "introduction",
        "intro",
        "getting-started",
    }

    # Descriptors that strongly suggest the repo contains functional software
    software_indicators = {
        "library",
        "framework",
        "tool",
        "client",
        "server",
        "engine",
        "parser",
        "middleware",
        "compiler",
        "bundler",
        "runtime",
        "plugin",
        "component",
        "app",
        "application",
        "system",
        "platform",
        "sdk",
        "api",
        "service",
    }

    # Set up session for API calls if checking Java percentage
    session = None
    if min_java_percentage is not None:
        session = requests.Session()
        if token:
            session.headers.update(
                {
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                }
            )
        else:
            session.headers.update({"Accept": "application/vnd.github.v3+json"})

    def get_java_percentage(full_name):
        """Get the percentage of Java code in a repository"""
        if not session:
            return None

        url = f"https://api.github.com/repos/{full_name}/languages"
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                response = session.get(url, timeout=30)
                if response.status_code == 200:
                    languages = response.json()
                    total_bytes = sum(languages.values())
                    if total_bytes == 0:
                        return 0
                    java_bytes = languages.get("Java", 0)
                    return (java_bytes / total_bytes) * 100
                elif response.status_code == 403:
                    print(f"  Rate limit reached for {full_name}. Waiting...")
                    time.sleep(60)
                    continue
                else:
                    return None
            except (
                requests.exceptions.RequestException,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"  Network error checking {full_name}: {e}")
                    return None
            except Exception as e:
                print(f"  Error checking {full_name}: {e}")
                return None

        return None

    def is_curated(row, require_sw_indicator=require_software_indicator):
        # Criteria 1: Language must be Java
        if row["language"] != "Java":
            return False

        text = (
            row["name"]
            + " "
            + row["full_name"]
            + " "
            + row["description"]
            + " "
            + row["topics"]
        ).lower()

        # Criteria 1 (continued): Exclude Android projects if requested
        # (Android projects are often Java but may be mobile apps rather than libraries)
        if exclude_android:
            if "android" in text:
                return False

        # Note: Java percentage filtering is now done before calling is_curated()
        # for better statistics tracking, so this check here is redundant but kept
        # as a safety fallback if called directly
        if min_java_percentage is not None:
            java_pct = None
            if "java_percentage" in row and row.get("java_percentage"):
                try:
                    java_pct_str = str(row["java_percentage"]).strip()
                    if java_pct_str:
                        java_pct = float(java_pct_str)
                except (ValueError, TypeError):
                    pass

            if java_pct is None:
                # Should not reach here if filtering is done earlier, but keep as fallback
                java_pct = get_java_percentage(row["full_name"])
                if java_pct is None:
                    return False
                time.sleep(0.5)

            if java_pct < min_java_percentage:
                return False

        # Criteria 2: Exclude informational/documentation/awesome-list repos
        for word in exclude_keywords:
            if re.search(r"\b" + re.escape(word) + r"\b", text):
                return False

        # Exclude common non-production repo types (already covered by exclude_keywords but keeping for clarity)
        non_production_keywords = [
            "sample",
            "demo",
            "demos",
            "example",
            "examples",
            "boilerplate",
            "boilerplates",
            "template",
            "templates",
            "starter",
            "starters",
            "starter-kit",
            "starter-kits",
            "scaffold",
            "scaffolding",
            "seed",
            "seeds",
        ]
        if any(
            re.search(r"\b" + re.escape(x) + r"\b", text)
            for x in non_production_keywords
        ):
            return False

        # Criteria 3: Must be actual software (heuristic for functional codebase with tests)
        # Note: This filter can be too strict - many legitimate repos don't have these keywords
        # Made optional via require_sw_indicator parameter
        if require_sw_indicator:
            if not any(
                re.search(r"\b" + re.escape(indicator) + r"\b", text)
                for indicator in software_indicators
            ):
                return False

        return True

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    curated_rows = []
    header = []
    stats = {
        "total": 0,
        "filtered_language": 0,
        "filtered_java_pct": 0,
        "filtered_java_pct_api_failed": 0,
        "filtered_android": 0,
        "filtered_keywords": 0,
        "filtered_software_indicators": 0,
        "java_percentages": [],
    }

    with open(input_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        for row in reader:
            stats["total"] += 1

            # Track why repos are filtered (for reporting)
            if row["language"] != "Java":
                stats["filtered_language"] += 1
                continue

            # Check Java percentage if filtering by it (do this before is_curated for better stats)
            if min_java_percentage is not None:
                java_pct = None
                if "java_percentage" in row and row.get("java_percentage"):
                    try:
                        java_pct_str = str(row["java_percentage"]).strip()
                        if java_pct_str:
                            java_pct = float(java_pct_str)
                    except (ValueError, TypeError):
                        pass

                if java_pct is None:
                    # Need to fetch from API
                    java_pct = get_java_percentage(row["full_name"])
                    if java_pct is None:
                        stats["filtered_java_pct_api_failed"] += 1
                        continue
                    time.sleep(0.5)

                if java_pct < min_java_percentage:
                    stats["filtered_java_pct"] += 1
                    continue

                # Track percentages for curated repos
                stats["java_percentages"].append(java_pct)

            # Now check other curation criteria
            if is_curated(row):
                curated_rows.append(row)
            else:
                # Determine why it was filtered (heuristic)
                text = (
                    row["name"]
                    + " "
                    + row["full_name"]
                    + " "
                    + row.get("description", "")
                    + " "
                    + row.get("topics", "")
                ).lower()
                if exclude_android and "android" in text:
                    stats["filtered_android"] += 1
                elif any(
                    re.search(r"\b" + re.escape(word) + r"\b", text)
                    for word in exclude_keywords
                ):
                    stats["filtered_keywords"] += 1
                elif require_software_indicator and not any(
                    re.search(r"\b" + re.escape(indicator) + r"\b", text)
                    for indicator in software_indicators
                ):
                    stats["filtered_software_indicators"] += 1

    random.shuffle(curated_rows)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(curated_rows)

    # Print statistics
    print(f"Curated {len(curated_rows)} repositories into {output_path}")
    print("\nFiltering statistics:")
    print(f"  Total input repos: {stats['total']}")
    print(f"  Filtered out - wrong language: {stats['filtered_language']}")
    if min_java_percentage is not None:
        print(
            f"  Filtered out - Java % < {min_java_percentage}%: {stats['filtered_java_pct']}"
        )
        if stats["filtered_java_pct_api_failed"] > 0:
            print(
                f"  Filtered out - Java % API fetch failed: {stats['filtered_java_pct_api_failed']}"
            )
        if stats["java_percentages"]:
            print(
                f"  Java % in curated repos: min={min(stats['java_percentages']):.2f}%, max={max(stats['java_percentages']):.2f}%, avg={sum(stats['java_percentages']) / len(stats['java_percentages']):.2f}%"
            )
            # Verify filtering worked
            below_threshold = [
                p for p in stats["java_percentages"] if p < min_java_percentage
            ]
            if below_threshold:
                print(
                    f"  ⚠️  WARNING: {len(below_threshold)} curated repos have Java % < {min_java_percentage}%!"
                )
            else:
                print(f"  ✓ All curated repos have Java % >= {min_java_percentage}%")
    if exclude_android:
        print(f"  Filtered out - Android-related: {stats['filtered_android']}")
    print(f"  Filtered out - informational keywords: {stats['filtered_keywords']}")
    if require_software_indicator:
        print(
            f"  Filtered out - missing software indicators: {stats['filtered_software_indicators']}"
        )
    print(f"  Final curated count: {len(curated_rows)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Curate Java repositories by filtering out informational and non-production repos"
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to input CSV file with repositories to curate",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path to output CSV file for curated repositories",
    )
    parser.add_argument(
        "--exclude-android",
        action="store_true",
        help="Exclude Android-related repositories",
    )
    parser.add_argument(
        "--min-java-percentage",
        type=float,
        help="Minimum percentage of Java code required (0-100). Uses pre-calculated data from CSV if available, otherwise makes API calls.",
    )
    parser.add_argument(
        "--require-software-indicator",
        action="store_true",
        help="Enable the software indicator filter (default: disabled, as it can be too strict and filter out legitimate repos like Guava, Kafka)",
    )
    parser.add_argument(
        "--token",
        help="GitHub personal access token (overrides GITHUB_TOKEN env var if provided)",
    )

    args = parser.parse_args()

    # Get token from env var or command line (command line takes precedence)
    token = args.token or os.getenv("GITHUB_TOKEN")

    if args.min_java_percentage is not None:
        if args.min_java_percentage < 0 or args.min_java_percentage > 100:
            print("Error: --min-java-percentage must be between 0 and 100")
            exit(1)

        # Check if CSV has java_percentage column (from scraper)
        # If it does, we won't need API calls
        has_java_percentage_column = False
        try:
            with open(args.input, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if "java_percentage" in reader.fieldnames:
                    has_java_percentage_column = True
        except Exception:
            pass

        if has_java_percentage_column:
            print(
                f"Filtering for repos with at least {args.min_java_percentage}% Java code (using pre-calculated percentages from CSV)"
            )
        else:
            if not token:
                print("Warning: No GitHub token provided. Rate limits will be lower.")
                print("Set GITHUB_TOKEN environment variable or use --token option.")
                print("Proceeding without token (may hit rate limits)...")
            print(
                f"Filtering for repos with at least {args.min_java_percentage}% Java code (making API calls - slower)"
            )

    require_software_indicator = args.require_software_indicator

    curate_repos(
        args.input,
        args.output,
        exclude_android=args.exclude_android,
        min_java_percentage=args.min_java_percentage,
        token=token,
        require_software_indicator=require_software_indicator,
    )
