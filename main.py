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
import warnings
from tqdm import tqdm


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
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                # Silent handling of 404 errors (empty repos, private repos, etc.)
                return None
            else:
                print(f"HTTP Error making request to {url}: {e}")
                return None
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
            # If contents API fails (404, empty repo, etc.), return empty list
            # This can happen with empty repositories, private repos without access, or archived repos
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
    
    def get_contributors_count(self, repo_name: str) -> int:
        """
        Get the number of contributors to the repository.
        
        Args:
            repo_name: Repository name
            
        Returns:
            Number of contributors
        """
        contributors_url = f"{self.base_url}/repos/{self.org}/{repo_name}/contributors"
        contributors_params = {'per_page': 100}
        page = 1
        total_contributors = 0
        
        while True:
            contributors_params['page'] = page
            contributors_response = requests.get(contributors_url, headers=self.headers, params=contributors_params, verify=self.verify_ssl)
            
            if contributors_response.status_code != 200:
                break
                
            contributors_data = contributors_response.json()
            if not contributors_data:
                break
                
            total_contributors += len(contributors_data)
            
            # Stop if we got less than full page (last page)
            if len(contributors_data) < 100:
                break
                
            page += 1
            
            # Safety limit
            if page > 50:  # Max 5,000 contributors
                break
        
        return total_contributors
    
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
    
    def get_pr_review_analysis(self, repo_name: str) -> Dict[str, Any]:
        """
        Analyze PR review patterns and quality.
        
        Args:
            repo_name: Repository name
            
        Returns:
            Dictionary with PR review analysis
        """
        # Get recent closed PRs for analysis
        search_url = f"{self.base_url}/search/issues"
        search_params = {
            'q': f'repo:{self.org}/{repo_name} type:pr state:closed',
            'per_page': 100,  # Analyze last 100 closed PRs
            'sort': 'updated',
            'order': 'desc'
        }
        
        search_response = requests.get(search_url, headers=self.headers, params=search_params, verify=self.verify_ssl)
        
        if search_response.status_code != 200:
            return {
                'self_approved_prs': 0,
                'total_analyzed_prs': 0,
                'prs_with_description': 0,
                'prs_reviewed_by_others': 0
            }
        
        search_data = search_response.json()
        prs = search_data.get('items', [])
        
        self_approved_count = 0
        prs_with_description = 0
        prs_reviewed_by_others = 0
        total_analyzed = len(prs)
        
        for pr in prs:
            pr_number = pr['number']
            pr_author = pr['user']['login']
            
            # Check if PR has description
            if pr.get('body') and len(pr['body'].strip()) > 10:
                prs_with_description += 1
            
            # Get PR reviews
            reviews_url = f"{self.base_url}/repos/{self.org}/{repo_name}/pulls/{pr_number}/reviews"
            reviews_response = requests.get(reviews_url, headers=self.headers, verify=self.verify_ssl)
            
            if reviews_response.status_code == 200:
                reviews_data = reviews_response.json()
                
                # Check for self-approval
                approved_by_author = False
                approved_by_others = False
                
                for review in reviews_data:
                    if review['state'] == 'APPROVED':
                        if review['user']['login'] == pr_author:
                            approved_by_author = True
                        else:
                            approved_by_others = True
                
                if approved_by_author:
                    self_approved_count += 1
                
                if approved_by_others:
                    prs_reviewed_by_others += 1
        
        return {
            'self_approved_prs': self_approved_count,
            'total_analyzed_prs': total_analyzed,
            'prs_with_description': prs_with_description,
            'prs_reviewed_by_others': prs_reviewed_by_others
        }
    
    def calculate_quality_score(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate a quality score (0-100) based on repository practices.
        
        Args:
            repo_data: Repository data dictionary
            
        Returns:
            Dictionary with quality score and justification
        """
        score = 0
        justifications = []
        
        # Factor 1: PR Review Quality (40 points max)
        total_prs = repo_data.get('total_analyzed_prs', 0)
        if total_prs > 0:
            prs_reviewed_by_others = repo_data.get('prs_reviewed_by_others', 0)
            self_approved_prs = repo_data.get('self_approved_prs', 0)
            
            # Points for external reviews
            review_ratio = prs_reviewed_by_others / total_prs
            review_points = min(25, int(review_ratio * 25))
            score += review_points
            
            if review_ratio >= 0.8:
                justifications.append(f"Excellent PR review culture ({review_ratio:.1%} reviewed by others)")
            elif review_ratio >= 0.5:
                justifications.append(f"Good PR review practices ({review_ratio:.1%} reviewed by others)")
            else:
                justifications.append(f"Limited PR reviews ({review_ratio:.1%} reviewed by others)")
            
            # Deduct points for self-approvals
            self_approval_ratio = self_approved_prs / total_prs
            if self_approval_ratio > 0.2:
                deduction = min(15, int(self_approval_ratio * 15))
                score -= deduction
                justifications.append(f"High self-approval rate ({self_approval_ratio:.1%}) reduces quality")
            elif self_approval_ratio > 0:
                justifications.append(f"Some self-approvals detected ({self_approval_ratio:.1%})")
            else:
                score += 15
                justifications.append("No self-approvals detected")
        else:
            justifications.append("No PRs available for review analysis")
        
        # Factor 2: Direct Push Discipline (25 points max)
        total_commits = repo_data.get('total_commits', 1)
        direct_pushes = repo_data.get('direct_pushes_to_default', 0)
        
        if total_commits > 0:
            direct_push_ratio = direct_pushes / total_commits
            if direct_push_ratio <= 0.1:
                score += 25
                justifications.append(f"Excellent branch discipline ({direct_push_ratio:.1%} direct pushes)")
            elif direct_push_ratio <= 0.3:
                score += 15
                justifications.append(f"Good branch discipline ({direct_push_ratio:.1%} direct pushes)")
            elif direct_push_ratio <= 0.5:
                score += 5
                justifications.append(f"Moderate direct push usage ({direct_push_ratio:.1%})")
            else:
                justifications.append(f"High direct push rate ({direct_push_ratio:.1%}) bypasses review")
        
        # Factor 3: Documentation Quality (20 points max)
        prs_with_description = repo_data.get('prs_with_description', 0)
        if total_prs > 0:
            description_ratio = prs_with_description / total_prs
            description_points = min(20, int(description_ratio * 20))
            score += description_points
            
            if description_ratio >= 0.8:
                justifications.append(f"Excellent PR documentation ({description_ratio:.1%} with descriptions)")
            elif description_ratio >= 0.5:
                justifications.append(f"Good PR documentation practices ({description_ratio:.1%})")
            else:
                justifications.append(f"Limited PR descriptions ({description_ratio:.1%})")
        
        # Factor 4: Collaboration (15 points max)
        contributors_count = repo_data.get('contributors_count', 0)
        if contributors_count >= 10:
            score += 15
            justifications.append(f"High collaboration ({contributors_count} contributors)")
        elif contributors_count >= 5:
            score += 10
            justifications.append(f"Good collaboration ({contributors_count} contributors)")
        elif contributors_count >= 2:
            score += 5
            justifications.append(f"Limited collaboration ({contributors_count} contributors)")
        else:
            justifications.append(f"Single contributor repository")
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        # Create justification text
        justification_text = ". ".join(justifications) + "."
        
        return {
            'quality_score': score,
            'quality_justification': justification_text
        }
    
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
    
    def analyze_repositories(self, repos: List[Dict], show_progress: bool = True, repo_filter: List[str] = None) -> List[Dict[str, Any]]:
        """
        Analyze multiple repositories.
        
        Args:
            repos: List of repository dictionaries from GitHub API
            show_progress: Whether to show progress bar
            repo_filter: List of specific repository names to analyze (None = analyze all)
            
        Returns:
            List of analyzed repository data
        """
        analyzed_repos = []
        
        # Filter repositories if specific repos are requested
        if repo_filter:
            # Convert filter to lowercase for case-insensitive matching
            repo_filter_lower = [name.lower() for name in repo_filter]
            filtered_repos = [repo for repo in repos if repo['name'].lower() in repo_filter_lower]
            
            # Report filtering results
            if show_progress:
                print(f"Filtered {len(repos)} repositories to {len(filtered_repos)} based on --repos filter")
                if len(filtered_repos) < len(repo_filter):
                    found_names = {repo['name'].lower() for repo in filtered_repos}
                    missing = [name for name in repo_filter if name.lower() not in found_names]
                    print(f"Warning: Repository names not found: {', '.join(missing)}")
            repos = filtered_repos
        
        # Create progress bar for overall progress
        if show_progress and sys.stdout.isatty():
            use_progress = True
        else:
            use_progress = False
        
        if use_progress:
            progress_bar = tqdm(total=len(repos), desc="Analyzing repositories", unit="repo")
        
        for i, repo in enumerate(repos):
            if use_progress:
                progress_bar.set_postfix({"current": repo['name'][:20]})
            else:
                print(f"Processing repository: {repo['name']}")
            
            try:
                repo_data = self.analyze_repository(repo, show_progress=show_progress)
                analyzed_repos.append(repo_data)
            except Exception as e:
                if use_progress:
                    tqdm.write(f"Error analyzing repository {repo['name']}: {e}")
                else:
                    print(f"Error analyzing repository {repo['name']}: {e}")
                continue
            finally:
                if use_progress:
                    progress_bar.update(1)
        
        if use_progress:
            progress_bar.close()
        
        return analyzed_repos
    
    def analyze_repository(self, repo: Dict, show_progress: bool = True) -> Dict[str, Any]:
        """
        Analyze a single repository and collect all required information.
        
        Args:
            repo: Repository dictionary from GitHub API
            show_progress: Whether to show progress bar for this repository
            
        Returns:
            Dictionary with analyzed repository data
        """
        repo_name = repo['name']
        
        # Define analysis steps
        analysis_steps = [
            "Basic info",
            "Code types", 
            "Pull requests",
            "Contributors",
            "Commit stats",
            "PR reviews",
            "Quality score"
        ]
        
        # Create progress bar for this repository if requested
        if show_progress and sys.stdout.isatty():
            repo_progress = tqdm(total=len(analysis_steps), desc=f"Analyzing {repo_name[:15]}", leave=False, unit="step")
            use_repo_progress = True
        else:
            use_repo_progress = False
        
        # Step 1: Basic repository information
        if use_repo_progress:
            repo_progress.update(1)
            repo_progress.set_postfix({"step": "basic info"})
        
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
        
        # Step 2: Detect code types
        if use_repo_progress:
            repo_progress.update(1)
            repo_progress.set_postfix({"step": "code types"})
        
        code_types = self.detect_code_types(repo_name)
        repo_data['code_types'] = code_types
        repo_data['primary_code_type'] = code_types[0] if code_types else 'Unknown'
        
        # Step 3: Get pull request counts
        if use_repo_progress:
            repo_progress.update(1)
            repo_progress.set_postfix({"step": "pull requests"})
        
        pr_counts = self.get_pull_requests_count(repo_name)
        repo_data['open_prs'] = pr_counts['open']
        repo_data['closed_prs'] = pr_counts['closed']
        repo_data['total_prs'] = pr_counts['open'] + pr_counts['closed']
        
        # Step 4: Get contributors count
        if use_repo_progress:
            repo_progress.update(1)
            repo_progress.set_postfix({"step": "contributors"})
        
        repo_data['contributors_count'] = self.get_contributors_count(repo_name)
        
        # Step 5: Get commit statistics
        if use_repo_progress:
            repo_progress.update(1)
            repo_progress.set_postfix({"step": "commit stats"})
        
        commit_stats = self.get_commit_stats(repo_name, repo['default_branch'])
        repo_data.update(commit_stats)
        
        # Step 6: Get PR review analysis
        if use_repo_progress:
            repo_progress.update(1)
            repo_progress.set_postfix({"step": "PR reviews"})
        
        pr_review_analysis = self.get_pr_review_analysis(repo_name)
        repo_data.update(pr_review_analysis)
        
        # Step 7: Calculate quality score
        if use_repo_progress:
            repo_progress.update(1)
            repo_progress.set_postfix({"step": "quality score"})
        
        quality_analysis = self.calculate_quality_score(repo_data)
        repo_data.update(quality_analysis)
        
        # Format dates
        repo_data['created_date'] = datetime.fromisoformat(
            repo['created_at'].replace('Z', '+00:00')
        ).strftime('%Y-%m-%d')
        
        if repo_data['last_commit_date']:
            repo_data['last_commit_date_formatted'] = datetime.fromisoformat(
                repo_data['last_commit_date'].replace('Z', '+00:00')
            ).strftime('%Y-%m-%d')
        else:
            repo_data['last_commit_date_formatted'] = 'Never'
        
        # Close repository progress bar
        if use_repo_progress:
            repo_progress.close()
        
        return repo_data
    
    def analyze_all_repositories(self, limit: Optional[int] = None, languages: Optional[List[str]] = None, show_progress: bool = True) -> List[Dict[str, Any]]:
        """
        Analyze all repositories in the organization.
        
        Args:
            limit: Maximum number of repositories to analyze
            languages: List of languages to filter repositories by
            show_progress: Whether to show progress bar
        
        Returns:
            List of analyzed repository data
        """
        repos = self.get_all_repos()
        
        # Filter by languages if specified
        if languages:
            # Convert to lowercase for case-insensitive comparison
            target_languages = [lang.lower() for lang in languages]
            filtered_repos = []
            
            for repo in repos:
                repo_languages = analyzer.detect_code_types(repo['name'])
                repo_languages_lower = [lang.lower() for lang in repo_languages]
                
                # Check if any of the repo's languages match the target languages
                if any(lang in repo_languages_lower for lang in target_languages):
                    filtered_repos.append(repo)
            
            print(f"Filtered {len(repos)} repositories to {len(filtered_repos)} based on language filter: {', '.join(languages)}")
            repos = filtered_repos
        
        # Limit number of repositories if specified
        if limit and limit < len(repos):
            repos = repos[:limit]
            print(f"Limited analysis to first {limit} repositories")
        
        analyzed_repos = []
        
        # Create progress bar if requested and in terminal
        if show_progress:
            progress_bar = tqdm(repos, desc="Analyzing repositories", unit="repo")
        else:
            progress_bar = repos
        
        for repo in progress_bar:
            if show_progress:
                progress_bar.set_postfix({"current": repo['name'][:20]})
            else:
                print(f"Processing repository: {repo['name']}")
            
            try:
                repo_data = self.analyze_repository(repo, show_progress=show_progress)
                analyzed_repos.append(repo_data)
            except Exception as e:
                if show_progress:
                    tqdm.write(f"Error analyzing repository {repo['name']}: {e}")
                else:
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
        
        # Create table with filters - handle large column counts
        num_cols = len(df.columns)
        if num_cols <= 26:
            # Single letter columns (A-Z)
            end_col = chr(64 + num_cols)
        else:
            # Double letter columns (AA, AB, etc.)
            first_letter = chr(64 + ((num_cols - 1) // 26))
            second_letter = chr(65 + ((num_cols - 1) % 26))
            end_col = first_letter + second_letter
        
        table = Table(
            displayName="RepoTable",
            ref=f"A1:{end_col}{len(df) + 1}"
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
        '--repos',
        nargs='+',
        help='Filter specific repositories to analyze by name (e.g., --repos repo1 repo2 repo3)'
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
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bar (useful for non-terminal environments)'
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
        # Also suppress requests warnings
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        # Suppress all SSL-related warnings
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    
    # Initialize analyzer
    analyzer = GitHubRepoAnalyzer(token, org, api_url=args.api_url, verify_ssl=not args.no_ssl_verify)
    
    # Analyze repositories
    print(f"Starting analysis of repositories for organization: {org}")
    start_time = datetime.now()
    
    try:
        # Detect if running in a terminal
        show_progress = sys.stdout.isatty() and not args.no_progress
        
        # Get all repositories first
        repos = analyzer.get_all_repos()
        
        # Filter by languages if specified
        if args.languages:
            # Convert to lowercase for case-insensitive comparison
            target_languages = [lang.lower() for lang in args.languages]
            filtered_repos = []
            
            for repo in repos:
                repo_languages = analyzer.detect_code_types(repo['name'])
                repo_languages_lower = [lang.lower() for lang in repo_languages]
                
                # Check if any of the repo's languages match the target languages
                if any(lang in repo_languages_lower for lang in target_languages):
                    filtered_repos.append(repo)
            
            print(f"Filtered {len(repos)} repositories to {len(filtered_repos)} based on language filter: {', '.join(args.languages)}")
            repos = filtered_repos
        
        # Limit number of repositories if specified
        if args.limit and args.limit < len(repos):
            repos = repos[:args.limit]
            print(f"Limited analysis to first {args.limit} repositories")
        
        # Analyze repositories
        repo_data = analyzer.analyze_repositories(repos, show_progress=show_progress, repo_filter=args.repos)
        
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
