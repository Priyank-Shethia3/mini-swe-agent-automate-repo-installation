#!/usr/bin/env python3
"""
GitHub Repository Scraper

A script to scrape GitHub repositories based on:
- Programming language
- Star count
- Activity metrics (commits, issues, PRs)
- Creation date
"""

import requests
import json
import time
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import argparse
import os
from dataclasses import dataclass, asdict


@dataclass
class RepoInfo:
    """Data structure for repository information"""
    id: int
    name: str
    full_name: str
    owner: str
    description: str
    language: str
    stars: int
    forks: int
    watchers: int
    open_issues: int
    created_at: str
    updated_at: str
    pushed_at: str
    size: int
    license: Optional[str]
    url: str
    clone_url: str
    topics: List[str]


class GitHubScraper:
    """GitHub repository scraper using the GitHub API"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the scraper with optional GitHub token for higher rate limits
        
        Args:
            token: GitHub personal access token (optional but recommended)
        """
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            })
        else:
            self.session.headers.update({
                'Accept': 'application/vnd.github.v3+json'
            })
    
    def get_rate_limit(self) -> Dict[str, Any]:
        """Check current rate limit status"""
        response = self.session.get(f"{self.base_url}/rate_limit")
        return response.json()
    
    def get_languages(self, full_name: str) -> Dict[str, int]:
        """Get language statistics for a repository"""
        url = f"{self.base_url}/repos/{full_name}/languages"
        response = self.session.get(url)
        
        if response.status_code == 200:
            return response.json()
        return {}
    
    def has_native_code(self, full_name: str, threshold: float = 5.0) -> bool:
        """
        Check if repository has significant native C/C++ code
        
        Args:
            full_name: Repository full name (owner/repo)
            threshold: Percentage threshold for native code (default 5%)
        
        Returns:
            True if C/C++ code exceeds threshold
        """
        languages = self.get_languages(full_name)
        if not languages:
            return False
        
        total_bytes = sum(languages.values())
        if total_bytes == 0:
            return False
        
        native_languages = ['C', 'C++', 'Objective-C', 'Objective-C++']
        native_bytes = sum(languages.get(lang, 0) for lang in native_languages)
        
        native_percentage = (native_bytes / total_bytes) * 100
        return native_percentage >= threshold
    
    def is_android_related(self, repo: RepoInfo) -> bool:
        """
        Check if repository is Android-related
        
        Args:
            repo: RepoInfo object
        
        Returns:
            True if repo appears to be Android-related
        """
        android_keywords = ['android']
        
        # Check name
        name_lower = repo.name.lower()
        if any(keyword in name_lower for keyword in android_keywords):
            return True
        
        # Check description
        if repo.description:
            desc_lower = repo.description.lower()
            if any(keyword in desc_lower for keyword in android_keywords):
                return True
        
        # Check topics
        topics_lower = [topic.lower() for topic in repo.topics]
        if any(keyword in topics_lower for keyword in android_keywords):
            return True
        
        return False
    
    def search_repositories(
        self,
        language: str = "",
        min_stars: int = 0,
        max_stars: Optional[int] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        created_after: Optional[str] = None,
        pushed_after: Optional[str] = None,
        exclude_native_code: bool = False,
        native_code_threshold: float = 5.0,
        exclude_android: bool = False,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 100,
        max_pages: int = 10
    ) -> List[RepoInfo]:
        """
        Search repositories with specified criteria
        
        Args:
            language: Programming language filter
            min_stars: Minimum star count
            max_stars: Maximum star count (optional)
            min_size: Minimum repository size in KB (optional)
            max_size: Maximum repository size in KB (optional)
            created_after: Repositories created after this date (YYYY-MM-DD)
            pushed_after: Repositories pushed after this date (YYYY-MM-DD)
            exclude_native_code: Filter out repos with significant C/C++ code
            native_code_threshold: Percentage of C/C++ code to trigger exclusion (default 5%)
            exclude_android: Filter out Android-related repositories
            sort: Sort by 'stars', 'forks', 'updated'
            order: 'asc' or 'desc'
            per_page: Results per page (max 100)
            max_pages: Maximum pages to fetch
            
        Returns:
            List of RepoInfo objects
        """
        repos = []
        
        # Build search query
        query_parts = []
        
        if language:
            query_parts.append(f"language:{language}")
        
        if min_stars > 0:
            if max_stars:
                query_parts.append(f"stars:{min_stars}..{max_stars}")
            else:
                query_parts.append(f"stars:>={min_stars}")
        elif max_stars:
            query_parts.append(f"stars:<={max_stars}")
        
        # Add size filters to query
        if min_size is not None:
            if max_size is not None:
                query_parts.append(f"size:{min_size}..{max_size}")
            else:
                query_parts.append(f"size:>={min_size}")
        elif max_size is not None:
            query_parts.append(f"size:<={max_size}")
        
        if created_after:
            query_parts.append(f"created:>={created_after}")
        
        if pushed_after:
            query_parts.append(f"pushed:>={pushed_after}")
        
        query = " ".join(query_parts)
        
        print(f"Searching with query: {query}")
        if exclude_native_code:
            print(f"Will filter out repos with >{native_code_threshold}% C/C++ code")
        if exclude_android:
            print(f"Will filter out Android-related repositories")
        
        for page in range(1, max_pages + 1):
            params = {
                'q': query,
                'sort': sort,
                'order': order,
                'per_page': per_page,
                'page': page
            }
            
            response = self.session.get(f"{self.base_url}/search/repositories", params=params)
            
            if response.status_code == 403:
                print("Rate limit exceeded. Waiting...")
                time.sleep(60)
                continue
            elif response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                break
            
            data = response.json()
            
            if 'items' not in data or not data['items']:
                print(f"No more results found at page {page}")
                break
            
            print(f"Processing page {page}/{max_pages} ({len(data['items'])} repos)")
            
            for repo_data in data['items']:
                repo = self._parse_repo_data(repo_data)
                
                # Filter by Android if requested
                if exclude_android:
                    if self.is_android_related(repo):
                        print(f"  Skipping {repo.full_name} (Android-related)")
                        continue
                
                # Filter by native code if requested
                if exclude_native_code:
                    if self.has_native_code(repo.full_name, native_code_threshold):
                        print(f"  Skipping {repo.full_name} (has native code)")
                        continue
                    time.sleep(0.5)  # Extra rate limit protection for language API
                
                repos.append(repo)
            
            # Respect rate limits
            time.sleep(1)
            
            # Check if we've reached the end
            if len(data['items']) < per_page:
                break
        
        return repos
    
    def get_repo_details(self, full_name: str) -> Optional[RepoInfo]:
        """Get detailed information for a specific repository"""
        response = self.session.get(f"{self.base_url}/repos/{full_name}")
        
        if response.status_code == 200:
            return self._parse_repo_data(response.json())
        else:
            print(f"Failed to get details for {full_name}: {response.status_code}")
            return None
    
    def _parse_repo_data(self, repo_data: Dict) -> RepoInfo:
        """Parse repository data from GitHub API response"""
        return RepoInfo(
            id=repo_data['id'],
            name=repo_data['name'],
            full_name=repo_data['full_name'],
            owner=repo_data['owner']['login'],
            description=repo_data.get('description', ''),
            language=repo_data.get('language', ''),
            stars=repo_data['stargazers_count'],
            forks=repo_data['forks_count'],
            watchers=repo_data['watchers_count'],
            open_issues=repo_data['open_issues_count'],
            created_at=repo_data['created_at'],
            updated_at=repo_data['updated_at'],
            pushed_at=repo_data.get('pushed_at', ''),
            size=repo_data['size'],
            license=repo_data['license']['name'] if repo_data.get('license') else None,
            url=repo_data['html_url'],
            clone_url=repo_data['clone_url'],
            topics=repo_data.get('topics', [])
        )


def save_to_csv(repos: List[RepoInfo], filename: str):
    """Save repository data to CSV file"""
    if not repos:
        print("No repositories to save")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = list(asdict(repos[0]).keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for repo in repos:
            row = asdict(repo)
            # Convert list topics to string
            row['topics'] = ', '.join(row['topics'])
            writer.writerow(row)
    
    print(f"Saved {len(repos)} repositories to {filename}")


def save_to_json(repos: List[RepoInfo], filename: str):
    """Save repository data to JSON file"""
    if not repos:
        print("No repositories to save")
        return
    
    data = [asdict(repo) for repo in repos]
    
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(repos)} repositories to {filename}")


def main():
    parser = argparse.ArgumentParser(description='GitHub Repository Scraper')
    parser.add_argument('--language', '-l', help='Programming language filter')
    parser.add_argument('--min-stars', '-s', type=int, default=0, help='Minimum star count')
    parser.add_argument('--max-stars', type=int, help='Maximum star count')
    parser.add_argument('--min-size', type=int, help='Minimum repository size in KB')
    parser.add_argument('--max-size', type=int, help='Maximum repository size in KB')
    parser.add_argument('--created-after', help='Repositories created after (YYYY-MM-DD)')
    parser.add_argument('--pushed-after', help='Repositories pushed after (YYYY-MM-DD)')
    parser.add_argument('--exclude-native-code', action='store_true', 
                        help='Filter out repositories with significant C/C++ code')
    parser.add_argument('--native-code-threshold', type=float, default=5.0,
                        help='Percentage threshold for native code filtering (default: 5.0%%)')
    parser.add_argument('--exclude-android', action='store_true',
                        help='Filter out Android-related repositories')
    parser.add_argument('--sort', choices=['stars', 'forks', 'updated'], default='stars', help='Sort criteria')
    parser.add_argument('--order', choices=['asc', 'desc'], default='desc', help='Sort order')
    parser.add_argument('--max-pages', '-p', type=int, default=10, help='Maximum pages to fetch')
    parser.add_argument('--output', '-o', default='repos', help='Output filename (without extension)')
    parser.add_argument('--format', choices=['csv', 'json', 'both'], default='csv', help='Output format')
    parser.add_argument('--token', help='GitHub personal access token')
    
    args = parser.parse_args()
    
    # Get token from environment if not provided
    token = args.token or os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("Warning: No GitHub token provided. Rate limits will be lower.")
        print("Set GITHUB_TOKEN environment variable or use --token option.")
    
    scraper = GitHubScraper(token)
    
    # Check rate limit
    rate_limit = scraper.get_rate_limit()
    print(f"Rate limit: {rate_limit['resources']['search']['remaining']}/{rate_limit['resources']['search']['limit']}")
    
    # Search repositories
    repos = scraper.search_repositories(
        language=args.language,
        min_stars=args.min_stars,
        max_stars=args.max_stars,
        min_size=args.min_size,
        max_size=args.max_size,
        created_after=args.created_after,
        pushed_after=args.pushed_after,
        exclude_native_code=args.exclude_native_code,
        native_code_threshold=args.native_code_threshold,
        exclude_android=args.exclude_android,
        sort=args.sort,
        order=args.order,
        max_pages=args.max_pages
    )
    
    if not repos:
        print("No repositories found matching the criteria")
        return
    
    print(f"\nFound {len(repos)} repositories")
    
    # Save results
    if args.format in ['csv', 'both']:
        save_to_csv(repos, f"{args.output}.csv")
    
    if args.format in ['json', 'both']:
        save_to_json(repos, f"{args.output}.json")
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total repositories: {len(repos)}")
    if repos:
        languages = [r.language for r in repos if r.language]
        if languages:
            from collections import Counter
            lang_counts = Counter(languages)
            print(f"Top languages: {dict(lang_counts.most_common(5))}")
        
        stars = [r.stars for r in repos]
        print(f"Star range: {min(stars)} - {max(stars)}")
        
        sizes = [r.size for r in repos]
        print(f"Size range: {min(sizes)} KB - {max(sizes)} KB (avg: {sum(sizes)//len(sizes)} KB)")


if __name__ == "__main__":
    main()