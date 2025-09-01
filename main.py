#!/usr/bin/env python3
"""
GitHub Repository Analyzer

This script analyzes all repositories in a GitHub organization and generates reports
in JSON, Excel, and CSV formats with comprehensive repository information.

Usage:
    python github_repo_analyzer.py --org <organization_name> --token <github_token>
    
Environment variables:
    GITHUB_TOKEN: GitHub Personal Access Token
    GITHUB_ORG: GitHub organization name
"""

import argparse
import os
import sys
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import Counter
import requests
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo
import urllib3


class GitHubRepoAnalyzer:
    """Analyzes GitHub repositories for an organization."""
    
    def __init__(self, token: str, org: str, api_url: str = 'https://api.github.com', verify_ssl: bool = True):
        """
        Initialize the analyzer with GitHub token and organization name.
        
        Args:
            token: GitHub Personal Access Token
            org: GitHub organization name
            api_url: GitHub API base URL (default: https://api.github.com)
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.token = token
        self.org = org
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = api_url.rstrip('/')
        self.verify_ssl = verify_ssl
        
        # Code type mappings based on file extensions
        self.code_type_mappings = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.tf': 'Terraform',
            '.hcl': 'HCL',
            '.go': 'Go',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.sh': 'Shell',
            '.ps1': 'PowerShell',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.less': 'LESS',
            '.sql': 'SQL',
            '.r': 'R',
            '.m': 'Objective-C',
            '.dart': 'Dart',
            '.vue': 'Vue',
            '.jsx': 'React',
            '.tsx': 'React TypeScript'
        }
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages for filtering."""
        return sorted(set(self.code_type_mappings.values()))
    
    def make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make a request to the GitHub API with error handling.
        
        Args:
            url: API endpoint URL
            params: Optional query parameters
            
        Returns:
            JSON response data or None if request failed
        """
        try:
            response = requests.get(url, headers=self.headers, params=params, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return None
    
    def get_all_repos(self) -> List[Dict]:
        """
        Get all repositories for the organization.
        
        Returns:
            List of repository dictionaries
        """
        repos = []
        page = 1
        per_page = 100
        
        print(f"Fetching repositories for organization: {self.org}")
        
        while True:
            url = f"{self.base_url}/orgs/{self.org}/repos"
            params = {
                'page': page,
                'per_page': per_page,
                'type': 'all'
            }
            
            data = self.make_request(url, params)
            if not data:
                break
                
            if not data:  # Empty response means no more pages
                break
                
            repos.extend(data)
            print(f"Fetched {len(data)} repositories (page {page})")
            
            if len(data) < per_page:  # Last page
                break
                
            page += 1
        
        print(f"Total repositories found: {len(repos)}")
        return repos
    
    def detect_code_types(self, repo_name: str) -> List[str]:
        """
        Detect code types in a repository based on file extensions.
        
        Args:
            repo_name: Repository name
            
        Returns:
            List of detected code types
        """
        url = f"{self.base_url}/repos/{self.org}/{repo_name}/contents"
        data = self.make_request(url)
        
        if not data:
            return []
        
        extensions = set()
        
        # Get file extensions from root directory
        for item in data:
            if item['type'] == 'file' and '.' in item['name']:
                ext = '.' + item['name'].split('.')[-1].lower()
                extensions.add(ext)
        
        # Map extensions to code types
        code_types = []
        for ext in extensions:
            if ext in self.code_type_mappings:
                code_types.append(self.code_type_mappings[ext])
        
        return list(set(code_types))  # Remove duplicates
    
    def get_pull_requests_count(self, repo_name: str) -> Dict[str, int]:
        """
        Get count of open and closed pull requests.
        
        Args:
            repo_name: Repository name
            
        Returns:
            Dictionary with open and closed PR counts
        """
        # Get open PRs using search API for accurate count
        search_url = f"{self.base_url}/search/issues"
        open_params = {
            'q': f'repo:{self.org}/{repo_name} type:pr state:open',
            'per_page': 1
        }
        open_response = requests.get(search_url, headers=self.headers, params=open_params, verify=self.verify_ssl)
        
        open_count = 0
        if open_response.status_code == 200:
            open_data = open_response.json()
            open_count = open_data.get('total_count', 0)
        
        # Get closed PRs using search API for accurate count
        closed_params = {
            'q': f'repo:{self.org}/{repo_name} type:pr state:closed',
            'per_page': 1
        }
        closed_response = requests.get(search_url, headers=self.headers, params=closed_params, verify=self.verify_ssl)
        
        closed_count = 0
        if closed_response.status_code == 200:
            closed_data = closed_response.json()
            closed_count = closed_data.get('total_count', 0)
        
        return {'open': open_count, 'closed': closed_count}
    
    def get_direct_pushes_count(self, repo_name: str, default_branch: str) -> int:
        """
        Get count of direct pushes to default branch by analyzing commits without PRs.
        
        Args:
            repo_name: Repository name
            default_branch: Default branch name
            
        Returns:
            Number of direct pushes (commits not associated with PRs)
        """
        # Get recent commits on default branch
        commits_url = f"{self.base_url}/repos/{self.org}/{repo_name}/commits"
        commits_params = {
            'sha': default_branch,
            'per_page': 100  # Analyze last 100 commits
        }
        commits_response = requests.get(commits_url, headers=self.headers, params=commits_params, verify=self.verify_ssl)
        
        if commits_response.status_code != 200:
            return 0
        
        commits_data = commits_response.json()
        direct_pushes = 0
        
        for commit in commits_data:
            commit_sha = commit['sha']
            
            # Check if this commit is associated with any PR
            search_url = f"{self.base_url}/search/issues"
            search_params = {
                'q': f'repo:{self.org}/{repo_name} type:pr {commit_sha}',
                'per_page': 1
            }
            
            search_response = requests.get(search_url, headers=self.headers, params=search_params, verify=self.verify_ssl)
            if search_response.status_code == 200:
                search_data = search_response.json()
                # If no PRs found for this commit, it's likely a direct push
                if search_data.get('total_count', 0) == 0:
                    direct_pushes += 1
        
        return direct_pushes
    
    def get_commit_stats(self, repo_name: str, default_branch: str) -> Dict[str, Any]:
        """
        Get commit statistics for the repository.
        
        Args:
            repo_name: Repository name
            default_branch: Default branch name
            
        Returns:
            Dictionary with commit statistics
        """
        # Get total commit count using a more reliable method
        # First try to get repository statistics
        stats_url = f"{self.base_url}/repos/{self.org}/{repo_name}/stats/participation"
        stats_response = requests.get(stats_url, headers=self.headers, verify=self.verify_ssl)
        
        total_commits = 0
        last_commit_date = None
        
        # Try to get commit count from contributors API (more reliable)
        contributors_url = f"{self.base_url}/repos/{self.org}/{repo_name}/stats/contributors"
        contributors_response = requests.get(contributors_url, headers=self.headers, verify=self.verify_ssl)
        
        if contributors_response.status_code == 200:
            contributors_data = contributors_response.json()
            if contributors_data:
                # Sum up all commits from all contributors
                total_commits = sum(contributor['total'] for contributor in contributors_data)
        
        # Fallback to pagination method if contributors API fails
        if total_commits == 0:
            commits_url = f"{self.base_url}/repos/{self.org}/{repo_name}/commits"
            commits_params = {'sha': default_branch, 'per_page': 100}
            page = 1
            
            while True:
                commits_params['page'] = page
                commits_response = requests.get(commits_url, headers=self.headers, params=commits_params, verify=self.verify_ssl)
                
                if commits_response.status_code != 200:
                    break
                    
                commits_data = commits_response.json()
                if not commits_data:
                    break
                    
                total_commits += len(commits_data)
                
                # Get last commit date from first page
                if page == 1 and commits_data:
                    last_commit_date = commits_data[0]['commit']['committer']['date']
                
                # Stop if we got less than full page (last page)
                if len(commits_data) < 100:
                    break
                    
                page += 1
                
                # Safety limit to avoid infinite loops
                if page > 100:  # Max 10,000 commits
                    break
        
        # Get last commit date if not already retrieved
        if not last_commit_date:
            commits_url = f"{self.base_url}/repos/{self.org}/{repo_name}/commits"
            commits_params = {'sha': default_branch, 'per_page': 1}
            commits_response = requests.get(commits_url, headers=self.headers, params=commits_params, verify=self.verify_ssl)
            
            if commits_response.status_code == 200:
                commits_data = commits_response.json()
                if commits_data:
                    last_commit_date = commits_data[0]['commit']['committer']['date']
        
        # Get direct pushes to default branch by analyzing commits without associated PRs
        direct_pushes = self.get_direct_pushes_count(repo_name, default_branch)
        
        return {
            'total_commits': total_commits,
            'last_commit_date': last_commit_date,
            'direct_pushes_to_default': direct_pushes
        }
    
    def analyze_repository(self, repo: Dict) -> Dict[str, Any]:
        """
        Analyze a single repository and collect all required information.
        
        Args:
            repo: Repository dictionary from GitHub API
            
        Returns:
            Dictionary with analyzed repository data
        """
        repo_name = repo['name']
        print(f"Analyzing repository: {repo_name}")
        
        # Basic repository information
        repo_data = {
            'name': repo_name,
            'full_name': repo['full_name'],
            'description': repo.get('description', ''),
            'created_at': repo['created_at'],
            'default_branch': repo['default_branch'],
            'private': repo['private'],
            'archived': repo['archived'],
            'disabled': repo['disabled'],
            'size': repo['size'],  # Size in KB
            'stargazers_count': repo['stargazers_count'],
            'watchers_count': repo['watchers_count'],
            'forks_count': repo['forks_count'],
            'open_issues_count': repo['open_issues_count'],
            'language': repo.get('language', 'Unknown')
        }
        
        # Detect code types
        code_types = self.detect_code_types(repo_name)
        repo_data['code_types'] = code_types
        repo_data['primary_code_type'] = code_types[0] if code_types else 'Unknown'
        
        # Get pull request counts
        pr_counts = self.get_pull_requests_count(repo_name)
        repo_data['open_prs'] = pr_counts['open']
        repo_data['closed_prs'] = pr_counts['closed']
        repo_data['total_prs'] = pr_counts['open'] + pr_counts['closed']
        
        # Get commit statistics
        commit_stats = self.get_commit_stats(repo_name, repo['default_branch'])
        repo_data.update(commit_stats)
        
        # Format dates
        repo_data['created_date'] = datetime.fromisoformat(
            repo['created_at'].replace('Z', '+00:00')
        ).strftime('%Y-%m-%d')
        
        if repo_data['last_commit_date']:
            repo_data['last_commit_date_formatted'] = datetime.fromisoformat(
                repo_data['last_commit_date'].replace('Z', '+00:00')
            ).strftime('%Y-%m-%d')
        else:
            repo_data['last_commit_date_formatted'] = 'N/A'
        
        return repo_data
    
    def analyze_all_repositories(self, limit: Optional[int] = None, languages: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Analyze all repositories in the organization.
        
        Args:
            limit: Maximum number of repositories to analyze
            languages: List of languages to filter repositories by
        
        Returns:
            List of analyzed repository data
        """
        repos = self.get_all_repos()
        
        # Filter by languages if specified
        if languages:
            filtered_repos = []
            for repo in repos:
                repo_language = repo.get('language', '').lower()
                if repo_language and any(lang.lower() in repo_language for lang in languages):
                    filtered_repos.append(repo)
            repos = filtered_repos
            print(f"Filtered to {len(repos)} repositories matching languages: {', '.join(languages)}")
        
        # Limit number of repositories if specified
        if limit and limit < len(repos):
            repos = repos[:limit]
            print(f"Limited analysis to first {limit} repositories")
        
        analyzed_repos = []
        
        for i, repo in enumerate(repos, 1):
            print(f"Processing repository {i}/{len(repos)}: {repo['name']}")
            try:
                repo_data = self.analyze_repository(repo)
                analyzed_repos.append(repo_data)
            except Exception as e:
                print(f"Error analyzing repository {repo['name']}: {e}")
                continue
        
        return analyzed_repos
    
    def save_to_json(self, data: List[Dict], filename: str):
        """Save data to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}")
    
    def save_to_csv(self, data: List[Dict], filename: str):
        """Save data to CSV file."""
        if not data:
            return
        
        # Flatten code_types list for CSV
        csv_data = []
        for repo in data:
            repo_copy = repo.copy()
            repo_copy['code_types'] = ', '.join(repo['code_types'])
            csv_data.append(repo_copy)
        
        fieldnames = csv_data[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        print(f"Data saved to {filename}")
    
    def save_to_excel(self, data: List[Dict], filename: str):
        """Save data to Excel file with filters."""
        if not data:
            return
        
        # Prepare data for Excel
        excel_data = []
        for repo in data:
            repo_copy = repo.copy()
            repo_copy['code_types'] = ', '.join(repo['code_types'])
            excel_data.append(repo_copy)
        
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        
        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Repository Analysis"
        
        # Add data to worksheet
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)
        
        # Create table with filters
        table = Table(
            displayName="RepoTable",
            ref=f"A1:{chr(64 + len(df.columns))}{len(df) + 1}"
        )
        
        # Add table style
        style = TableStyleInfo(
            name="TableStyleMedium9",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=True
        )
        table.tableStyleInfo = style
        
        # Add table to worksheet
        ws.add_table(table)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save workbook
        wb.save(filename)
        print(f"Data saved to {filename}")


def main():
    """Main function to run the GitHub repository analyzer."""
    parser = argparse.ArgumentParser(
        description='Analyze GitHub repositories for an organization'
    )
    parser.add_argument(
        '--org',
        type=str,
        help='GitHub organization name (can also be set via GITHUB_ORG env var)'
    )
    parser.add_argument(
        '--token',
        type=str,
        help='GitHub Personal Access Token (can also be set via GITHUB_TOKEN env var)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Output directory for generated files (default: current directory)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of repositories to analyze'
    )
    # Create temporary analyzer to get supported languages list
    temp_analyzer = GitHubRepoAnalyzer('dummy', 'dummy')
    supported_langs = temp_analyzer.get_supported_languages()
    
    parser.add_argument(
        '--languages',
        nargs='+',
        help=f'Filter repositories by programming languages. Supported: {', '.join(supported_langs[:10])}... (e.g., --languages Python JavaScript Java)'
    )
    parser.add_argument(
        '--api-url',
        type=str,
        default='https://api.github.com',
        help='GitHub API base URL (default: https://api.github.com, for GitHub Enterprise use: https://your-domain/api/v3)'
    )
    parser.add_argument(
        '--no-ssl-verify',
        action='store_true',
        help='Disable SSL certificate verification (useful for self-signed certificates)'
    )
    
    args = parser.parse_args()
    
    # Get token and org from args or environment variables
    token = args.token or os.getenv('GITHUB_TOKEN')
    org = args.org or os.getenv('GITHUB_ORG')
    
    if not token:
        print("Error: GitHub token is required. Use --token argument or set GITHUB_TOKEN environment variable.")
        sys.exit(1)
    
    if not org:
        print("Error: GitHub organization is required. Use --org argument or set GITHUB_ORG environment variable.")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Suppress SSL warnings if SSL verification is disabled
    if args.no_ssl_verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Initialize analyzer
    analyzer = GitHubRepoAnalyzer(token, org, api_url=args.api_url, verify_ssl=not args.no_ssl_verify)
    
    # Analyze repositories
    print(f"Starting analysis of repositories for organization: {org}")
    start_time = datetime.now()
    
    try:
        repo_data = analyzer.analyze_all_repositories(limit=args.limit, languages=args.languages)
        
        if not repo_data:
            print("No repositories found or analyzed.")
            sys.exit(1)
        
        # Generate output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"{org}_repos_{timestamp}"
        
        # Save to different formats
        json_file = os.path.join(args.output_dir, f"{base_filename}.json")
        csv_file = os.path.join(args.output_dir, f"{base_filename}.csv")
        excel_file = os.path.join(args.output_dir, f"{base_filename}.xlsx")
        
        analyzer.save_to_json(repo_data, json_file)
        analyzer.save_to_csv(repo_data, csv_file)
        analyzer.save_to_excel(repo_data, excel_file)
        
        # Print summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n{'='*50}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*50}")
        print(f"Organization: {org}")
        print(f"Repositories analyzed: {len(repo_data)}")
        print(f"Duration: {duration}")
        print(f"\nOutput files generated:")
        print(f"  - JSON: {json_file}")
        print(f"  - CSV: {csv_file}")
        print(f"  - Excel: {excel_file}")
        
        # Print some statistics
        code_types = []
        total_prs = 0
        total_commits = 0
        
        for repo in repo_data:
            code_types.extend(repo['code_types'])
            total_prs += repo['total_prs']
            total_commits += repo['total_commits']
        
        code_type_counts = Counter(code_types)
        print(f"\nTop code types:")
        for code_type, count in code_type_counts.most_common(5):
            print(f"  - {code_type}: {count} repositories")
        
        print(f"\nTotal PRs across all repositories: {total_prs}")
        print(f"Total commits across all repositories: {total_commits}")
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
