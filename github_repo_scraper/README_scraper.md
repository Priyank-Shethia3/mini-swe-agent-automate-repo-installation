# GitHub Repository Scraper

A Python script to scrape GitHub repositories based on various criteria including programming language, star count, and activity metrics.

## Features

- **Language Filtering**: Search repositories by programming language
- **Star-based Filtering**: Filter by minimum/maximum star counts
- **Activity Metrics**: Filter by creation date and last push date
- **Flexible Sorting**: Sort by stars, forks, or last updated
- **Rate Limit Handling**: Automatic rate limit detection and waiting
- **Multiple Export Formats**: Save results as CSV or JSON
- **GitHub API Integration**: Uses official GitHub REST API v3

## Installation

### Requirements

```bash
pip install requests
```

### Setup

1. **Get a GitHub Token** (Recommended):
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Generate a new token with `public_repo` scope
   - Set it as environment variable: `export GITHUB_TOKEN=your_token_here`

2. **Make the script executable**:
   ```bash
   chmod +x github_repo_scraper.py
   ```

## Usage Examples

### Basic Usage

```bash
# Search Python repositories with 100+ stars
python github_repo_scraper.py --language python --min-stars 100

# Search JavaScript repositories with 1000-5000 stars
python github_repo_scraper.py --language javascript --min-stars 1000 --max-stars 5000

# Search repositories created in the last year
python github_repo_scraper.py --created-after 2023-01-01

# Search recently active repositories
python github_repo_scraper.py --pushed-after 2024-01-01
```

### Advanced Filtering

```bash
# Popular Python ML repositories
python github_repo_scraper.py \
  --language python \
  --min-stars 1000 \
  --sort stars \
  --max-pages 5 \
  --output python_ml_repos

# Recently active Go repositories
python github_repo_scraper.py \
  --language go \
  --pushed-after 2024-06-01 \
  --sort updated \
  --order desc \
  --max-pages 3

# Large TypeScript projects
python github_repo_scraper.py \
  --language typescript \
  --min-stars 500 \
  --sort forks \
  --format both
```

### Three-Stage Filtering Process

This workflow is designed to discover high-quality, functional JavaScript repositories suitable for test-based evaluation (e.g., for SWE-bench style benchmarks).

#### 1. Initial Scrape
Scrape active repositories with high star counts (e.g., >= 10K stars) and recent activity.
```bash
python github_repo_scraper.py --language javascript --min-stars 10000 --pushed-after 2025-01-01
```
Script: [github_repo_scraper.py](https://github.com/Priyank-Shethia3/mini-swe-agent-automate-repo-installation/blob/main/github_repo_scraper/github_repo_scraper.py)

#### 2. Exclude Existing Repositories
Filter out repositories that are already present in major benchmarks like SWE-smith, SWE-bench Multilingual, or Multi SWE-Bench.
```bash
# Ensure your current repository list is in 'repos.csv' 
# and known repositories are in 'existing_repos.csv'
python filter_existing.py
```
This produces `new_repos.csv`.

#### 3. Targeted Curation
Use keyword filtering based on name, description, and topics to further narrow down the list to functional JavaScript-only repositories with likely good test coverage. This step excludes informational repos (lists, tutorials), TypeScript-primary projects, and boilerplate/demos.
```bash
# Processes 'new_repos.csv' and outputs 'new_curated_repos.csv'
python curate_js.py
```
The final output is randomly shuffled to avoid bias.

### Output Options

```bash
# Save as JSON
python github_repo_scraper.py --language rust --format json

# Save as both CSV and JSON
python github_repo_scraper.py --language rust --format both

# Custom output filename
python github_repo_scraper.py --language python --output my_repos
```

## Command Line Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--language` | `-l` | Programming language filter | `--language python` |
| `--min-stars` | `-s` | Minimum star count | `--min-stars 100` |
| `--max-stars` | | Maximum star count | `--max-stars 5000` |
| `--created-after` | | Repos created after date | `--created-after 2023-01-01` |
| `--pushed-after` | | Repos pushed after date | `--pushed-after 2024-01-01` |
| `--sort` | | Sort by: stars, forks, updated | `--sort stars` |
| `--order` | | Sort order: asc, desc | `--order desc` |
| `--max-pages` | `-p` | Maximum pages to fetch | `--max-pages 10` |
| `--output` | `-o` | Output filename (no extension) | `--output my_repos` |
| `--format` | | Output format: csv, json, both | `--format json` |
| `--token` | | GitHub personal access token | `--token ghp_xxxx` |

## Programming Usage

You can also use the scraper as a Python module:

```python
from github_repo_scraper import GitHubScraper, save_to_csv

# Initialize scraper
scraper = GitHubScraper(token="your_github_token")

# Search repositories
repos = scraper.search_repositories(
    language="python",
    min_stars=1000,
    max_pages=5
)

# Save results
save_to_csv(repos, "python_repos.csv")

# Get details for specific repo
repo_details = scraper.get_repo_details("microsoft/vscode")
```

## Output Format

### CSV Output
The CSV file contains the following columns:
- `id`: GitHub repository ID
- `name`: Repository name
- `full_name`: Full name (owner/repo)
- `owner`: Repository owner
- `description`: Repository description
- `language`: Primary programming language
- `stars`: Star count
- `forks`: Fork count
- `watchers`: Watcher count
- `open_issues`: Open issues count
- `created_at`: Creation date
- `updated_at`: Last updated date
- `pushed_at`: Last push date
- `size`: Repository size in KB
- `license`: License name
- `url`: GitHub URL
- `clone_url`: Git clone URL
- `topics`: Repository topics (comma-separated)

### JSON Output
The JSON file contains an array of repository objects with the same fields as above.

## Rate Limits

- **Without token**: 60 requests per hour
- **With token**: 5000 requests per hour
- **Search API**: 30 requests per minute (regardless of token)

The script automatically handles rate limits by:
- Checking current rate limit status
- Waiting when limits are exceeded
- Adding delays between requests

## Common Use Cases

### 1. Finding Popular Projects by Language
```bash
python github_repo_scraper.py --language rust --min-stars 500 --sort stars
```

### 2. Discovering Active Projects
```bash
python github_repo_scraper.py --pushed-after 2024-06-01 --sort updated
```

### 3. Research Trending Technologies
```bash
python github_repo_scraper.py --language typescript --created-after 2024-01-01 --min-stars 100
```

### 4. Finding Projects to Contribute To
```bash
python github_repo_scraper.py --language python --min-stars 50 --max-stars 500 --sort updated
```

## Troubleshooting

### Rate Limit Issues
- Use a GitHub token for higher limits
- Reduce `--max-pages` parameter
- The script will automatically wait when rate limited

### No Results Found
- Check your search criteria aren't too restrictive
- Verify language names (use lowercase: `python`, `javascript`, etc.)
- Try broader date ranges

### API Errors
- Ensure your GitHub token is valid
- Check network connectivity
- Verify GitHub API status at https://www.githubstatus.com/

## License

This script is for educational and research purposes. Respect GitHub's API terms of service and rate limits.