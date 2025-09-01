# GitHub Repository Analyzer

A comprehensive Python script to analyze all repositories in a GitHub organization and generate detailed reports in multiple formats (JSON, Excel, CSV).

## Features

The script analyzes each repository and collects the following information:
- **Repository metadata**: Name, description, creation date, default branch
- **Code type detection**: Identifies programming languages based on file extensions
- **Pull Request statistics**: Count of open and closed PRs
- **Commit analysis**: Total commits, last commit date
- **Direct pushes**: Number of pushes made directly to the default branch
- **Additional metrics**: Stars, forks, watchers, issues, repository size

## Output Formats

- **JSON**: Complete structured data for programmatic use
- **Excel (.xlsx)**: Formatted spreadsheet with filters and auto-sized columns
- **CSV**: Simple comma-separated values for data analysis

## Prerequisites

1. Python 3.7 or higher
2. GitHub Personal Access Token (PAT) with appropriate permissions
3. Required Python packages (see requirements.txt)

## Installation

1. Clone or download the script
2. Create and activate a virtual environment:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Arguments

```bash
python main.py --org <organization_name> --token <github_token>
```

Or directly execute the script:
```bash
./main.py --org <organization_name> --token <github_token>
```

### Environment Variables

You can also set the following environment variables instead of using command line arguments:

```bash
export GITHUB_TOKEN="your_github_token_here"
export GITHUB_ORG="your_organization_name"
python main.py
```

Or:
```bash
export GITHUB_TOKEN="your_github_token_here"
export GITHUB_ORG="your_organization_name"
./main.py
```

### Additional Options

- `--output-dir`: Specify output directory for generated files (default: current directory)
- `--limit`: Maximum number of repositories to analyze (useful for testing or large organizations)
- `--languages`: Filter repositories by programming languages (multiple values allowed)
- `--api-url`: Specify custom GitHub API URL (default: https://api.github.com)
- `--no-ssl-verify`: Disable SSL certificate verification

#### Supported Languages for Filtering

The `--languages` argument accepts any of these programming languages:

**Popular Languages:**
- Python, JavaScript, TypeScript, Java, Go, Rust, C, C++, C#

**Web Technologies:**
- HTML, CSS, SCSS, LESS, Vue, React, React TypeScript

**Infrastructure & Config:**
- Terraform, HCL, YAML, JSON, XML, Shell, PowerShell

**Other Languages:**
- PHP, Ruby, Swift, Kotlin, Scala, SQL, R, Objective-C, Dart

**Example Usage:**
```bash
# Filter by single language
./main.py --org myorg --token xxx --languages Python

# Filter by multiple languages
./main.py --org myorg --token xxx --languages Python JavaScript TypeScript

# Case insensitive matching
./main.py --org myorg --token xxx --languages python java
```

### Examples

Using command line arguments:
```bash
python main.py --org microsoft --token ghp_xxxxxxxxxxxx
```

Using environment variables:
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_ORG="microsoft"
python main.py --output-dir ./reports
```

Direct execution:
```bash
./main.py --org microsoft --token ghp_xxxxxxxxxxxx
```

With filtering and limits:
```bash
# Analyze only first 10 repositories
./main.py --org myorg --token ghp_xxx --limit 10

# Filter by specific languages
./main.py --org myorg --token ghp_xxx --languages Python JavaScript

# Combine filters and limits
./main.py --org myorg --token ghp_xxx --limit 5 --languages Java TypeScript

# GitHub Enterprise with custom API URL
./main.py --org myorg --token ghp_xxx --api-url https://github.company.com/api/v3

# Disable SSL verification (for self-signed certificates)
./main.py --org myorg --token ghp_xxx --no-ssl-verify

# GitHub Enterprise with SSL disabled
./main.py --org myorg --token ghp_xxx --api-url https://github.company.com/api/v3 --no-ssl-verify
```

### GitHub Enterprise Support

The script supports GitHub Enterprise installations:

**Custom API URL:**
- Use `--api-url` to specify your GitHub Enterprise API endpoint
- Format: `https://your-github-enterprise-domain/api/v3`
- Default: `https://api.github.com` (GitHub.com)

**SSL Certificate Issues:**
- Use `--no-ssl-verify` to disable SSL certificate verification
- Useful for self-signed certificates or internal CA certificates
- **Security Warning**: Only use this option in trusted environments

## GitHub Personal Access Token (PAT)

To use this script, you need a GitHub Personal Access Token with the following permissions:
- `repo` (for private repositories)
- `public_repo` (for public repositories)
- `read:org` (to read organization information)

### Creating a PAT:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token"
3. Select the required scopes mentioned above
4. Copy the generated token

## Output Files

The script generates three files with timestamps:
- `{org}_repos_{timestamp}.json`
- `{org}_repos_{timestamp}.csv` 
- `{org}_repos_{timestamp}.xlsx`

### Data Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Repository name |
| `full_name` | String | Full repository name (org/repo) |
| `description` | String | Repository description |
| `created_at` | String | Raw creation timestamp from GitHub API |
| `created_date` | String | Formatted creation date (YYYY-MM-DD) |
| `default_branch` | String | Default branch name (e.g., main, master) |
| `code_types` | Array | List of detected programming languages based on file extensions |
| `primary_code_type` | String | Main programming language detected |
| `language` | String | Primary language detected by GitHub |
| `open_prs` | Integer | Number of currently open pull requests |
| `closed_prs` | Integer | Number of closed pull requests |
| `total_prs` | Integer | Total pull requests (open + closed) |
| `total_commits` | Integer | Total number of commits on default branch |
| `last_commit_date` | String | Raw timestamp of last commit |
| `last_commit_date_formatted` | String | Formatted last commit date (YYYY-MM-DD) |
| `direct_pushes_to_default` | Integer | Number of commits pushed directly to default branch (not via PR) |
| `stargazers_count` | Integer | Number of stars |
| `forks_count` | Integer | Number of forks |
| `watchers_count` | Integer | Number of watchers |
| `open_issues_count` | Integer | Number of open issues |
| `size` | Integer | Repository size in KB |
| `contributors_count` | Integer | Total number of contributors to the repository |
| `self_approved_prs` | Integer | Number of PRs approved by their own creator |
| `total_analyzed_prs` | Integer | Number of recent PRs analyzed for quality metrics |
| `prs_with_description` | Integer | Number of PRs with meaningful descriptions |
| `prs_reviewed_by_others` | Integer | Number of PRs reviewed by someone other than the author |
| `quality_score` | Integer | Quality score from 0-100 based on development practices |
| `quality_justification` | String | English explanation of the quality score |
| `private` | Boolean | Whether repository is private |
| `archived` | Boolean | Whether repository is archived |
| `disabled` | Boolean | Whether repository is disabled |

**Note on Direct Pushes**: The `direct_pushes_to_default` field analyzes the last 100 commits on the default branch and counts those not associated with any pull request. This provides an indication of commits pushed directly to the main branch without going through the PR process.

## Quality Score Calculation

The `quality_score` (0-100) is calculated using configurable rules defined in `quality_config.json`. The system applies various penalties based on development practices:

### Major Penalties
- **No Pull Requests (-50%)**: Repositories without any PRs receive a major penalty
- **High Direct Push Ratio (-25%)**: Excessive commits directly to main branch (threshold: 30%)
- **High Self-Approval Rate (-25%)**: Too many PRs approved by their own authors (threshold: 50%)

### Minor Penalties  
- **Poor PR Documentation (-10%)**: Less than 50% of PRs have meaningful descriptions
- **Low External Review (-15%)**: Less than 30% of PRs reviewed by others
- **Single Contributor (-10%)**: Repository has only one contributor
- **Inactive Repository (-5%)**: No commits in the last 365 days
- **No Commits (-10%)**: Repository has no development activity

### Configuration
All scoring rules are customizable in `quality_config.json`. See `QUALITY_SCORING.md` for detailed examples and configuration options.

The `quality_justification` field provides a detailed explanation of how the score was calculated, including specific penalties applied.

## Code Type Detection

The script detects programming languages based on file extensions found in the repository root:

- **Python**: .py
- **JavaScript**: .js, .jsx
- **TypeScript**: .ts, .tsx
- **Java**: .java
- **Terraform/HCL**: .tf, .hcl
- **Go**: .go
- **Rust**: .rs
- **C/C++**: .c, .cpp
- **C#**: .cs
- **PHP**: .php
- **Ruby**: .rb
- **Swift**: .swift
- **Kotlin**: .kt
- **Scala**: .scala
- **Shell**: .sh
- **PowerShell**: .ps1
- **YAML**: .yaml, .yml
- **And many more...**

## Rate Limiting

The script respects GitHub API rate limits. For authenticated requests, you have 5,000 requests per hour. The script includes error handling for rate limit issues.

## Troubleshooting

### Common Issues

1. **Authentication Error**: Verify your PAT is correct and has required permissions
2. **Organization Not Found**: Check the organization name spelling
3. **Rate Limit Exceeded**: Wait for the rate limit to reset or use a different token
4. **Permission Denied**: Ensure your PAT has access to the organization's repositories

### Error Messages

The script provides detailed error messages for common issues:
- Missing token or organization name
- API request failures
- File writing permissions
- Network connectivity issues

## Performance

- Processing time depends on the number of repositories and API response times
- Large organizations may take several minutes to analyze
- Progress is displayed during execution
- The script handles pagination automatically for organizations with many repositories

## Security Notes

- Never commit your GitHub token to version control
- Use environment variables for sensitive information
- Regularly rotate your GitHub tokens
- Limit token permissions to minimum required scope

## License

This script is provided as-is for educational and analysis purposes.
