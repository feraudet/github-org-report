#!/usr/bin/env python3
"""
GitHub Repository Analyzer Module

Contains the main GitHubRepoAnalyzer class for analyzing GitHub repositories.
"""

import sys
import requests
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from tqdm import tqdm


class GitHubRepoAnalyzer:
    """Analyzes GitHub repositories for an organization."""
    
    def __init__(self, token: str, org: str, api_url: str = 'https://api.github.com', verify_ssl: bool = True, config_path: str = 'quality_config.json'):
        """
        Initialize the analyzer with GitHub token and organization name.
        
        Args:
            token: GitHub Personal Access Token
            org: GitHub organization name
            api_url: GitHub API base URL (default: https://api.github.com)
            verify_ssl: Whether to verify SSL certificates (default: True)
            config_path: Path to quality scoring configuration file
        """
        self.token = token
        self.org = org
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = api_url
        self.verify_ssl = verify_ssl
        self.quality_config = self._load_quality_config(config_path)
        
        # Code type mappings
        self.code_type_mappings = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React',
            '.tsx': 'React',
            '.java': 'Java',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.go': 'Go',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.cc': 'C++',
            '.cxx': 'C++',
            '.c': 'C',
            '.h': 'C/C++',
            '.hpp': 'C++',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.m': 'Objective-C',
            '.mm': 'Objective-C++',
            '.r': 'R',
            '.R': 'R',
            '.pl': 'Perl',
            '.pm': 'Perl',
            '.sh': 'Shell',
            '.bash': 'Shell',
            '.zsh': 'Shell',
            '.fish': 'Shell',
            '.ps1': 'PowerShell',
            '.psm1': 'PowerShell',
            '.tf': 'Terraform',
            '.hcl': 'HCL',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.html': 'HTML',
            '.htm': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'SASS',
            '.less': 'LESS',
            '.vue': 'Vue.js',
            '.svelte': 'Svelte',
            '.dart': 'Dart',
            '.lua': 'Lua',
            '.sql': 'SQL',
            '.dockerfile': 'Docker',
            '.dockerignore': 'Docker',
            '.gitignore': 'Git',
            '.gitattributes': 'Git',
            '.md': 'Markdown',
            '.rst': 'reStructuredText',
            '.tex': 'LaTeX',
            '.ipynb': 'Jupyter',
            '.proto': 'Protocol Buffers',
            '.graphql': 'GraphQL',
            '.gql': 'GraphQL',
            '.clj': 'Clojure',
            '.cljs': 'ClojureScript',
            '.ex': 'Elixir',
            '.exs': 'Elixir',
            '.erl': 'Erlang',
            '.hrl': 'Erlang',
            '.elm': 'Elm',
            '.hs': 'Haskell',
            '.lhs': 'Haskell',
            '.ml': 'OCaml',
            '.mli': 'OCaml',
            '.fs': 'F#',
            '.fsx': 'F#',
            '.fsi': 'F#',
            '.nim': 'Nim',
            '.nims': 'Nim',
            '.cr': 'Crystal',
            '.d': 'D',
            '.zig': 'Zig',
            '.jl': 'Julia',
            '.pas': 'Pascal',
            '.pp': 'Pascal',
            '.ada': 'Ada',
            '.adb': 'Ada',
            '.ads': 'Ada',
            '.cob': 'COBOL',
            '.cbl': 'COBOL',
            '.for': 'Fortran',
            '.f90': 'Fortran',
            '.f95': 'Fortran',
            '.f03': 'Fortran',
            '.f08': 'Fortran'
        }
    
    def _load_quality_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load quality scoring configuration from JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('quality_scoring', {})
            else:
                print(f"⚠️  Quality config file not found: {config_path}, using defaults")
                return self._get_default_quality_config()
        except Exception as e:
            print(f"⚠️  Error loading quality config: {e}, using defaults")
            return self._get_default_quality_config()
    
    def _get_default_quality_config(self) -> Dict[str, Any]:
        """Get default quality scoring configuration."""
        return {
            "base_score": 100,
            "penalties": {
                "no_prs": {"penalty_percent": 50, "message": "No pull requests found"},
                "no_pr_descriptions": {"penalty_percent": 10, "threshold": 0.5, "message": "Poor PR documentation"},
                "high_self_approval": {"penalty_percent": 25, "threshold": 0.5, "message": "High self-approval rate"},
                "low_external_review": {"penalty_percent": 15, "threshold": 0.3, "message": "Insufficient external review"},
                "high_direct_pushes": {"penalty_percent": 20, "threshold": 0.5, "message": "Poor branch discipline"},
                "single_contributor": {"penalty_percent": 10, "message": "Single contributor"},
                "inactive_repository": {"penalty_percent": 5, "days_threshold": 365, "message": "Repository inactive"},
                "no_commits": {"penalty_percent": 10, "message": "No commits found"}
            }
        }
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages."""
        return sorted(list(set(self.code_type_mappings.values())))
    
    def _wait_for_rate_limit_reset(self, reset_time: int, api_type: str = "Core"):
        """
        Wait for rate limit to reset with progress bar.
        
        Args:
            reset_time: Unix timestamp when rate limit resets
            api_type: Type of API (Core, Search, etc.)
        """
        current_time = int(time.time())
        wait_time = max(0, reset_time - current_time + 5)  # Add 5 seconds buffer
        
        if wait_time > 0:
            print(f"\n⚠️  {api_type} API rate limit exceeded!")
            print(f"⏳ Waiting {wait_time} seconds for quota to reset...")
            
            # Progress bar for wait time
            with tqdm(total=wait_time, desc=f"Rate limit cooldown ({api_type})", 
                     unit="s", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
                for _ in range(wait_time):
                    time.sleep(1)
                    pbar.update(1)
            
            print("✅ Rate limit reset, resuming...")

    def _check_rate_limit(self, response: requests.Response) -> bool:
        """
        Check if response indicates rate limit exceeded and handle it.
        
        Args:
            response: HTTP response object
            
        Returns:
            True if rate limit was hit and handled, False otherwise
        """
        if response.status_code == 403:
            # Check if it's a rate limit error
            rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', '0')
            rate_limit_reset = response.headers.get('X-RateLimit-Reset')
            
            if rate_limit_remaining == '0' and rate_limit_reset:
                api_type = "Search" if "/search/" in response.url else "Core"
                self._wait_for_rate_limit_reset(int(rate_limit_reset), api_type)
                return True
        
        return False

    def make_request(self, url: str, params: Optional[Dict] = None, max_retries: int = 3) -> Optional[Dict]:
        """
        Make a request to the GitHub API with rate limit handling and retry logic.
        
        Args:
            url: API endpoint URL
            params: Optional query parameters
            max_retries: Maximum number of retries for rate limit
            
        Returns:
            JSON response data or None if request failed
        """
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(url, headers=self.headers, params=params, verify=self.verify_ssl)
                
                # Check for rate limit before raising for status
                if self._check_rate_limit(response):
                    if attempt < max_retries:
                        continue  # Retry after waiting
                    else:
                        print(f"❌ Max retries exceeded for rate limit on {url}")
                        return None
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 404:
                    # Silent handling of 404 errors (empty repos, private repos, etc.)
                    return None
                elif response.status_code == 409:
                    # Handle 409 Conflict errors (usually branch/commit issues)
                    print(f"Conflict error accessing {url} - repository may be empty or have branch issues")
                    return None
                elif response.status_code == 403 and attempt < max_retries:
                    # Rate limit might not have proper headers, wait and retry
                    print(f"⚠️  403 error, waiting 60 seconds before retry {attempt + 1}/{max_retries}")
                    time.sleep(60)
                    continue
                else:
                    print(f"HTTP Error making request to {url}: {e}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"Error making request to {url}: {e}")
                return None
        
        return None
    
    def get_all_repos(self, languages: List[str] = None) -> List[Dict]:
        """
        Get all repositories for the organization, optionally filtered by languages.
        
        Args:
            languages: Optional list of programming languages to filter by
            
        Returns:
            List of repository dictionaries
        """
        if languages:
            return self._get_repos_by_language(languages)
        else:
            return self._get_all_org_repos()
    
    def _get_all_org_repos(self) -> List[Dict]:
        """
        Get all repositories for the organization using the org repos API.
        
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
                
            repos.extend(data)
            print(f"Fetched {len(data)} repositories (page {page})")
            
            if len(data) < per_page:  # Last page
                break
                
            page += 1
        
        print(f"Total repositories found: {len(repos)}")
        return repos
    
    def _get_repos_by_language(self, languages: List[str]) -> List[Dict]:
        """
        Get repositories filtered by programming languages using GitHub search API.
        
        Args:
            languages: List of programming languages to filter by
            
        Returns:
            List of repository dictionaries
        """
        repos = []
        
        # Build search query with language filters
        lang_queries = [f"lang:{lang}" for lang in languages]
        query = f"org:{self.org} " + " OR ".join(lang_queries)
        
        print(f"Searching repositories for organization: {self.org} with languages: {', '.join(languages)}")
        
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.base_url}/search/repositories"
            params = {
                'q': query,
                'page': page,
                'per_page': per_page,
                'sort': 'updated',
                'order': 'desc'
            }
            
            data = self.make_request(url, params)
            if not data or 'items' not in data:
                break
            
            items = data['items']
            repos.extend(items)
            print(f"Fetched {len(items)} repositories (page {page})")
            
            if len(items) < per_page:  # Last page
                break
                
            page += 1
            
            # GitHub search API has a limit of 1000 results
            if len(repos) >= 1000:
                print("Reached GitHub search API limit of 1000 results")
                break
        
        print(f"Total repositories found with language filter: {len(repos)}")
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
        
        return {
            'open': open_count,
            'closed': closed_count
        }
    
    def get_contributors_count(self, repo_name: str) -> int:
        """
        Get the number of contributors to a repository.
        
        Args:
            repo_name: Repository name
            
        Returns:
            Number of contributors
        """
        url = f"{self.base_url}/repos/{self.org}/{repo_name}/contributors"
        contributors = []
        page = 1
        per_page = 100
        
        while True:
            params = {'page': page, 'per_page': per_page}
            data = self.make_request(url, params)
            
            if not data:
                break
            
            contributors.extend(data)
            
            if len(data) < per_page:
                break
            
            page += 1
        
        return len(contributors)
    
    def get_direct_pushes_count(self, repo_name: str, default_branch: str) -> int:
        """
        Get count of direct pushes to default branch (commits not associated with PRs).
        
        Args:
            repo_name: Repository name
            default_branch: Default branch name
            
        Returns:
            Number of direct pushes
        """
        # Get recent commits from default branch
        commits_url = f"{self.base_url}/repos/{self.org}/{repo_name}/commits"
        commits_params = {
            'sha': default_branch,
            'per_page': 100  # Check last 100 commits
        }
        
        commits_response = requests.get(commits_url, headers=self.headers, params=commits_params, verify=self.verify_ssl)
        if commits_response.status_code != 200:
            return 0
        
        commits_data = commits_response.json()
        direct_pushes = 0
        
        # For each commit, check if it's associated with a PR
        for commit in commits_data:
            commit_sha = commit['sha']
            
            # Search for PRs that reference this commit
            search_url = f"{self.base_url}/search/issues"
            search_params = {
                'q': f'repo:{self.org}/{repo_name} type:pr {commit_sha}',
                'per_page': 1
            }
            
            search_response = requests.get(search_url, headers=self.headers, params=search_params, verify=self.verify_ssl)
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data.get('total_count', 0) == 0:
                    # Commit not associated with any PR
                    direct_pushes += 1
        
        return direct_pushes
    
    def get_commit_stats(self, repo_name: str, default_branch: str) -> Dict[str, Any]:
        """
        Get commit statistics for the repository with improved error handling.
        
        Args:
            repo_name: Repository name
            default_branch: Default branch name
            
        Returns:
            Dictionary with commit statistics
        """
        total_commits = 0
        last_commit_date = None
        
        # Try to get commit count from contributors API (most reliable)
        contributors_data = self.make_request(f"{self.base_url}/repos/{self.org}/{repo_name}/stats/contributors")
        if contributors_data and isinstance(contributors_data, list):
            # Sum up all commits from all contributors
            total_commits = sum(contributor.get('total', 0) for contributor in contributors_data)
        # Fallback to pagination method if contributors API fails
        if total_commits == 0:
            total_commits, last_commit_date = self._get_commits_via_pagination(repo_name, default_branch)
        
        # Get last commit date if not already retrieved
        if not last_commit_date:
            last_commit_date = self._get_last_commit_date(repo_name, default_branch)
        
        # Get direct pushes to default branch
        direct_pushes = self.get_direct_pushes_count(repo_name, default_branch)
        
        return {
            'total_commits': total_commits,
            'last_commit_date': last_commit_date,
            'direct_pushes_to_default': direct_pushes
        }
    
    def _get_commits_via_pagination(self, repo_name: str, default_branch: str) -> tuple[int, Optional[str]]:
        """
        Get commit count and last commit date via pagination with improved error handling.
        
        Args:
            repo_name: Repository name
            default_branch: Default branch name
            
        Returns:
            Tuple of (total_commits, last_commit_date)
        """
        total_commits = 0
        last_commit_date = None
        page = 1
        
        # Try different branch names if default branch fails
        branches_to_try = [default_branch, 'master', 'main', 'develop']
        if default_branch not in branches_to_try:
            branches_to_try.insert(0, default_branch)
        
        for branch in branches_to_try:
            commits_url = f"{self.base_url}/repos/{self.org}/{repo_name}/commits"
            commits_params = {'sha': branch, 'per_page': 100, 'page': 1}
            
            commits_data = self.make_request(commits_url, commits_params)
            if commits_data:
                # Successfully got commits from this branch
                total_commits = len(commits_data)
                
                # Get last commit date from first commit
                if commits_data:
                    last_commit_date = commits_data[0]['commit']['committer']['date']
                
                # Continue pagination to get total count
                page = 2
                while True:
                    commits_params['page'] = page
                    more_commits = self.make_request(commits_url, commits_params)
                    
                    if not more_commits or len(more_commits) == 0:
                        break
                    
                    total_commits += len(more_commits)
                    
                    # Stop if we got less than full page (last page)
                    if len(more_commits) < 100:
                        break
                    
                    page += 1
                    
                    # Safety limit to avoid infinite loops
                    if page > 100:  # Max 10,000 commits
                        break
                
                break  # Successfully processed this branch, no need to try others
        
        return total_commits, last_commit_date
    
    def _get_last_commit_date(self, repo_name: str, default_branch: str) -> Optional[str]:
        """
        Get the last commit date with fallback branch handling.
        
        Args:
            repo_name: Repository name
            default_branch: Default branch name
            
        Returns:
            Last commit date or None
        """
        branches_to_try = [default_branch, 'master', 'main', 'develop']
        if default_branch not in branches_to_try:
            branches_to_try.insert(0, default_branch)
        
        for branch in branches_to_try:
            commits_url = f"{self.base_url}/repos/{self.org}/{repo_name}/commits"
            commits_params = {'sha': branch, 'per_page': 1}
            
            commits_data = self.make_request(commits_url, commits_params)
            if commits_data and len(commits_data) > 0:
                return commits_data[0]['commit']['committer']['date']
        
        return None
    
    def get_pr_review_analysis(self, repo_name: str) -> Dict[str, Any]:
        """
        Analyze PR review patterns and quality with detailed closed PR analysis.
        
        Args:
            repo_name: Repository name
            
        Returns:
            Dictionary with comprehensive PR review analysis
        """
        # First try to get closed PRs via search API
        search_url = f"{self.base_url}/search/issues"
        search_params = {
            'q': f'repo:{self.org}/{repo_name} is:pr is:closed',
            'per_page': 100,  # Analyze last 100 closed PRs
            'sort': 'updated',
            'order': 'desc'
        }
        
        search_data = self.make_request(search_url, search_params)
        
        if search_data:
            prs = search_data.get('items', [])
            
            if prs:
                print(f"Found {len(prs)} closed PRs for {repo_name} via search API")
                return self._analyze_closed_prs(repo_name, prs)
            else:
                print(f"No closed PRs found via search API for {repo_name}")
        else:
            print(f"Search API failed for {repo_name}")
        
        # Fallback: try direct pulls API with proper pagination
        print(f"Trying direct pulls API for {repo_name}...")
        pulls_url = f"{self.base_url}/repos/{self.org}/{repo_name}/pulls"
        
        # Get closed PRs with pagination
        all_closed_prs = []
        page = 1
        max_pages = 5  # Limit to first 500 PRs (5 pages * 100 per page)
        
        while page <= max_pages:
            closed_params = {
                'state': 'closed', 
                'per_page': 100, 
                'sort': 'updated', 
                'direction': 'desc',
                'page': page
            }
            closed_data = self.make_request(pulls_url, closed_params)
            
            if closed_data:
                if not closed_data:  # No more PRs
                    break
                    
                all_closed_prs.extend(closed_data)
                print(f"Found {len(closed_data)} closed PRs on page {page} for {repo_name}")
                
                if len(closed_data) < 100:  # Last page
                    break
                    
                page += 1
            else:
                print(f"Pulls API failed on page {page} for {repo_name}")
                break
        
        if all_closed_prs:
            print(f"Total: {len(all_closed_prs)} closed PRs found via pulls API for {repo_name}")
            # Convert pulls API format to search API format for compatibility
            formatted_prs = []
            for pr in all_closed_prs:
                formatted_pr = {
                    'number': pr['number'],
                    'title': pr['title'],
                    'body': pr['body'],
                    'user': pr['user'],
                    'created_at': pr['created_at'],
                    'updated_at': pr['updated_at'],
                    'pull_request': {
                        'merged_at': pr.get('merged_at')
                    }
                }
                formatted_prs.append(formatted_pr)
            
            return self._analyze_closed_prs(repo_name, formatted_prs)
        else:
            print(f"No closed PRs found via pulls API for {repo_name}")
        
        # If both methods fail, return empty analysis
        print(f"No PRs found for analysis in {repo_name}")
        return self._empty_pr_analysis()
    
    def _empty_pr_analysis(self) -> Dict[str, Any]:
        """Return empty PR analysis structure."""
        return {
            'self_approved_prs': 0,
            'total_analyzed_prs': 0,
            'prs_with_description': 0,
            'prs_reviewed_by_others': 0,
            'merged_prs': 0,
            'closed_without_merge': 0,
            'avg_time_to_merge_hours': 0,
            'avg_comments_per_pr': 0,
            'prs_with_multiple_reviewers': 0,
            'hotfix_prs': 0,
            'feature_prs': 0,
            'bugfix_prs': 0,
            'avg_files_changed': 0,
            'avg_lines_added': 0,
            'avg_lines_deleted': 0
        }
    
    def _analyze_closed_prs(self, repo_name: str, prs: List[Dict]) -> Dict[str, Any]:
        """
        Perform detailed analysis of closed PRs.
        
        Args:
            repo_name: Repository name
            prs: List of PR data from GitHub API
            
        Returns:
            Dictionary with detailed PR analysis
        """
        analysis = self._empty_pr_analysis()
        analysis['total_analyzed_prs'] = len(prs)
        
        if not prs:
            return analysis
        
        total_merge_time = 0
        total_comments = 0
        total_files_changed = 0
        total_lines_added = 0
        total_lines_deleted = 0
        merged_count = 0
        large_prs_count = 0
        slow_reviews_count = 0
        
        print(f"📊 Analyzing {len(prs)} PRs in detail...")
        
        # Progress bar for PR analysis
        pr_progress = tqdm(prs, desc="Analyzing PRs", unit="PR", leave=False)
        
        for pr in pr_progress:
            pr_number = pr['number']
            pr_author = pr['user']['login']
            pr_title = pr.get('title', '').lower()
            
            # Check if PR has description
            if pr.get('body') and len(pr['body'].strip()) > 10:
                analysis['prs_with_description'] += 1
            
            # Determine PR type based on title/labels
            if any(keyword in pr_title for keyword in ['hotfix', 'urgent', 'critical']):
                analysis['hotfix_prs'] += 1
            elif any(keyword in pr_title for keyword in ['feature', 'feat', 'add']):
                analysis['feature_prs'] += 1
            elif any(keyword in pr_title for keyword in ['fix', 'bug', 'issue']):
                analysis['bugfix_prs'] += 1
            
            # Check if PR was merged
            if pr.get('pull_request', {}).get('merged_at'):
                analysis['merged_prs'] += 1
                merged_count += 1
                
                # Calculate time to merge
                created_at = pr['created_at']
                merged_at = pr['pull_request']['merged_at']
                if created_at and merged_at:
                    from datetime import datetime
                    created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    merged = datetime.fromisoformat(merged_at.replace('Z', '+00:00'))
                    merge_time_hours = (merged - created).total_seconds() / 3600
                    total_merge_time += merge_time_hours
            else:
                analysis['closed_without_merge'] += 1
            
            # Update progress bar with current PR
            pr_progress.set_postfix(PR=f"#{pr_number}")
            
            # Get detailed PR information
            pr_details = self._get_pr_details(repo_name, pr_number)
            if pr_details:
                # Count comments
                total_comments += pr_details.get('comments', 0) + pr_details.get('review_comments', 0)
                
                # Count files and lines changed
                files_changed = pr_details.get('changed_files', 0)
                total_files_changed += files_changed
                total_lines_added += pr_details.get('additions', 0)
                total_lines_deleted += pr_details.get('deletions', 0)
                
                # Check for large PRs (more than 15 files changed)
                if files_changed > 15:
                    large_prs_count += 1
                
                # Check for slow review response (more than 7 days to first review)
                if pr.get('created_at'):
                    try:
                        created_at = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
                        # Get reviews for this PR
                        reviews_url = f"{self.base_url}/repos/{self.org}/{repo_name}/pulls/{pr_number}/reviews"
                        reviews_response = self.make_request(reviews_url)
                        if reviews_response and reviews_response.get('data'):
                            reviews = reviews_response['data']
                            if reviews:
                                first_review = min(reviews, key=lambda r: r['submitted_at'])
                                first_review_date = datetime.fromisoformat(first_review['submitted_at'].replace('Z', '+00:00'))
                                days_to_review = (first_review_date - created_at).days
                                if days_to_review > 7:
                                    slow_reviews_count += 1
                    except Exception:
                        # Skip if we can't parse dates or get reviews
                        pass
            
            # Analyze reviews
            review_analysis = self._analyze_pr_reviews(repo_name, pr_number, pr_author)
            if review_analysis['approved_by_author']:
                analysis['self_approved_prs'] += 1
            if review_analysis['approved_by_others']:
                analysis['prs_reviewed_by_others'] += 1
            if review_analysis['multiple_reviewers']:
                analysis['prs_with_multiple_reviewers'] += 1
        
        # Close progress bar
        pr_progress.close()
        
        # Calculate averages
        if analysis['total_analyzed_prs'] > 0:
            analysis['avg_comments_per_pr'] = round(total_comments / analysis['total_analyzed_prs'], 1)
            analysis['avg_files_changed'] = round(total_files_changed / analysis['total_analyzed_prs'], 1)
            analysis['avg_lines_added'] = round(total_lines_added / analysis['total_analyzed_prs'], 1)
            analysis['avg_lines_deleted'] = round(total_lines_deleted / analysis['total_analyzed_prs'], 1)
        
        if merged_count > 0:
            analysis['avg_time_to_merge_hours'] = round(total_merge_time / merged_count, 1)
        
        # Add new metrics to analysis
        analysis['large_prs_count'] = large_prs_count
        analysis['slow_reviews_count'] = slow_reviews_count
        
        print(f"✅ PR analysis completed: {analysis['total_analyzed_prs']} PRs processed")
        return analysis
    
    def _get_pr_details(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific PR.
        
        Args:
            repo_name: Repository name
            pr_number: PR number
            
        Returns:
            Dictionary with PR details
        """
        url = f"{self.base_url}/repos/{self.org}/{repo_name}/pulls/{pr_number}"
        return self.make_request(url) or {}
    
    def _analyze_pr_reviews(self, repo_name: str, pr_number: int, pr_author: str) -> Dict[str, Any]:
        """
        Analyze reviews for a specific PR.
        
        Args:
            repo_name: Repository name
            pr_number: PR number
            pr_author: PR author username
            
        Returns:
            Dictionary with review analysis
        """
        reviews_url = f"{self.base_url}/repos/{self.org}/{repo_name}/pulls/{pr_number}/reviews"
        reviews_data = self.make_request(reviews_url) or []
        
        approved_by_author = False
        approved_by_others = False
        reviewers = set()
        
        for review in reviews_data:
            if review['state'] == 'APPROVED':
                reviewer = review['user']['login']
                reviewers.add(reviewer)
                
                if reviewer == pr_author:
                    approved_by_author = True
                else:
                    approved_by_others = True
        
        return {
            'approved_by_author': approved_by_author,
            'approved_by_others': approved_by_others,
            'multiple_reviewers': len(reviewers) > 1,
            'reviewer_count': len(reviewers)
        }
    
    def calculate_quality_score(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate a quality score for the repository based on configuration rules.
        
        Args:
            repo_data: Repository data dictionary
            
        Returns:
            Dictionary with quality score and justification
        """
        config = self.quality_config
        score = config.get('base_score', 100)
        justifications = []
        penalties = config.get('penalties', {})
        
        # Check for no PRs (major penalty)
        total_prs = repo_data.get('total_analyzed_prs', 0)
        if total_prs == 0:
            no_prs_config = penalties.get('no_prs', {})
            penalty = no_prs_config.get('penalty_percent', 50)
            score -= penalty
            message = no_prs_config.get('message', 'No pull requests found')
            justifications.append(f"{message} - reduces score by {penalty} points")
        else:
            # PR Review Quality Analysis
            self_approved = repo_data.get('self_approved_prs', 0)
            reviewed_by_others = repo_data.get('prs_reviewed_by_others', 0)
            prs_with_desc = repo_data.get('prs_with_description', 0)
            
            self_approval_ratio = self_approved / total_prs
            external_review_ratio = reviewed_by_others / total_prs
            description_ratio = prs_with_desc / total_prs
            
            # High self-approval penalty
            self_approval_config = penalties.get('high_self_approval', {})
            threshold = self_approval_config.get('threshold', 0.5)
            if self_approval_ratio > threshold:
                penalty = min(self_approval_config.get('penalty_percent', 25), 
                            int(self_approval_ratio * 30))
                score -= penalty
                message = self_approval_config.get('message', 'High self-approval rate')
                justifications.append(f"{message} ({self_approval_ratio:.1%}) reduces score by {penalty} points")
            
            # Low external review penalty
            ext_review_config = penalties.get('low_external_review', {})
            threshold = ext_review_config.get('threshold', 0.3)
            if external_review_ratio < threshold:
                penalty = min(ext_review_config.get('penalty_percent', 15), 
                            int((threshold - external_review_ratio) * 50))
                score -= penalty
                message = ext_review_config.get('message', 'Insufficient external review')
                justifications.append(f"{message} ({external_review_ratio:.1%}) reduces score by {penalty} points")
            elif external_review_ratio > 0.7:
                justifications.append(f"Good external review rate ({external_review_ratio:.1%}) maintains high score")
            
            # Poor PR descriptions penalty
            desc_config = penalties.get('no_pr_descriptions', {})
            threshold = desc_config.get('threshold', 0.5)
            if description_ratio < threshold:
                penalty = min(desc_config.get('penalty_percent', 10), 
                            int((threshold - description_ratio) * 20))
                score -= penalty
                message = desc_config.get('message', 'Poor PR documentation')
                justifications.append(f"{message} ({description_ratio:.1%} with descriptions) reduces score by {penalty} points")
            else:
                justifications.append(f"Good documentation with {description_ratio:.1%} of PRs having descriptions")
        
        # Branch Discipline
        total_commits = repo_data.get('total_commits', 0)
        direct_pushes = repo_data.get('direct_pushes_to_default', 0)
        
        if total_commits > 0:
            direct_push_ratio = direct_pushes / total_commits
            direct_push_config = penalties.get('high_direct_pushes', {})
            threshold = direct_push_config.get('threshold', 0.5)
            
            if direct_push_ratio > threshold:
                penalty = min(direct_push_config.get('penalty_percent', 20), 
                            int(direct_push_ratio * 25))
                score -= penalty
                message = direct_push_config.get('message', 'Poor branch discipline')
                justifications.append(f"{message} ({direct_push_ratio:.1%}) reduces score by {penalty} points")
            elif direct_push_ratio < 0.2:
                justifications.append(f"Good branch discipline with low direct push ratio ({direct_push_ratio:.1%})")
        
        # Collaboration Level
        contributors = repo_data.get('contributors_count', 0)
        single_contrib_config = penalties.get('single_contributor', {})
        
        if contributors == 1:
            penalty = single_contrib_config.get('penalty_percent', 10)
            score -= penalty
            message = single_contrib_config.get('message', 'Single contributor')
            justifications.append(f"{message} reduces collaboration score by {penalty} points")
        elif contributors >= 5:
            justifications.append(f"Good collaboration with {contributors} contributors")
        elif contributors >= 3:
            justifications.append(f"Moderate collaboration with {contributors} contributors")
        
        # Activity Level
        no_commits_config = penalties.get('no_commits', {})
        inactive_config = penalties.get('inactive_repository', {})
        
        if repo_data.get('total_commits', 0) == 0:
            penalty = no_commits_config.get('penalty_percent', 10)
            score -= penalty
            message = no_commits_config.get('message', 'No commits found')
            justifications.append(f"{message} reduces score by {penalty} points")
        elif repo_data.get('last_commit_date'):
            # Check if last commit is recent
            try:
                last_commit = datetime.fromisoformat(repo_data['last_commit_date'].replace('Z', '+00:00'))
                days_since_last_commit = (datetime.now(last_commit.tzinfo) - last_commit).days
                days_threshold = inactive_config.get('days_threshold', 365)
                
                if days_since_last_commit > days_threshold:
                    penalty = inactive_config.get('penalty_percent', 5)
                    score -= penalty
                    message = inactive_config.get('message', 'Repository inactive')
                    justifications.append(f"{message} ({days_since_last_commit} days ago) reduces score by {penalty} points")
                elif days_since_last_commit <= 30:
                    justifications.append("Recent activity maintains score")
            except:
                pass
        
        # New metrics: Large PRs penalty
        if total_prs > 0:
            large_prs_config = penalties.get('large_prs', {})
            files_threshold = large_prs_config.get('files_threshold', 15)
            large_prs_count = repo_data.get('large_prs_count', 0)
            
            if large_prs_count > 0:
                large_prs_ratio = large_prs_count / total_prs
                if large_prs_ratio > 0.3:  # More than 30% of PRs are large
                    penalty = min(large_prs_config.get('penalty_percent', 5), 
                                int(large_prs_ratio * 10))
                    score -= penalty
                    message = large_prs_config.get('message', 'Large PRs detected')
                    justifications.append(f"{message} ({large_prs_count}/{total_prs} PRs) reduces score by {penalty} points")
        
        # New metrics: Slow review response penalty
        if total_prs > 0:
            slow_review_config = penalties.get('slow_review_response', {})
            days_threshold = slow_review_config.get('days_threshold', 7)
            slow_reviews_count = repo_data.get('slow_reviews_count', 0)
            
            if slow_reviews_count > 0:
                slow_reviews_ratio = slow_reviews_count / total_prs
                if slow_reviews_ratio > 0.4:  # More than 40% of PRs have slow reviews
                    penalty = min(slow_review_config.get('penalty_percent', 5), 
                                int(slow_reviews_ratio * 8))
                    score -= penalty
                    message = slow_review_config.get('message', 'Slow review response')
                    justifications.append(f"{message} ({slow_reviews_count}/{total_prs} PRs) reduces score by {penalty} points")
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        # Create justification text
        if justifications:
            justification = ". ".join(justifications) + "."
        else:
            justification = "Repository meets basic quality standards."
        
        return {
            'quality_score': score,
            'quality_justification': justification
        }
    
    def fetch_repositories_data(self, repos: List[Dict[str, Any]], show_progress: bool = True, repo_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch raw data from GitHub API without performing quality analysis.
        Used for --fetch-only mode to cache data for later analysis.
        """
        if repo_filter:
            repos = [repo for repo in repos if repo['name'] in repo_filter]
        
        repo_data = []
        
        if show_progress:
            repos = tqdm(repos, desc="Fetching repository data")
        
        for repo in repos:
            try:
                # Fetch basic repository info
                basic_info = {
                    'name': repo['name'],
                    'org': self.org,
                    'full_name': repo['full_name'],
                    'description': repo.get('description', ''),
                    'language': repo.get('language'),
                    'created_at': repo.get('created_at'),
                    'updated_at': repo.get('updated_at'),
                    'size': repo.get('size', 0),
                    'stargazers_count': repo.get('stargazers_count', 0),
                    'watchers_count': repo.get('watchers_count', 0),
                    'forks_count': repo.get('forks_count', 0),
                    'open_issues_count': repo.get('open_issues_count', 0),
                    'private': repo.get('private', False),
                    'archived': repo.get('archived', False),
                    'disabled': repo.get('disabled', False),
                    'default_branch': repo.get('default_branch', 'main')
                }
                
                # Fetch PR analysis data
                pr_analysis = self.get_pr_review_analysis(repo['name'])
                
                # Fetch commit statistics
                commit_stats = self.get_commit_stats(repo['name'], repo.get('default_branch', 'main'))
                
                # Fetch contributors
                contributors_count = self.get_contributors_count(repo['name'])
                
                # Fetch direct pushes count
                direct_pushes = self.get_direct_pushes_count(repo['name'], repo.get('default_branch', 'main'))
                
                # Combine all data
                repo_info = {
                    **basic_info,
                    **pr_analysis,
                    **commit_stats,
                    'contributors_count': contributors_count,
                    'direct_pushes_to_default': direct_pushes,
                    'fetch_timestamp': datetime.now().isoformat()
                }
                
                repo_data.append(repo_info)
                
            except Exception as e:
                print(f"Error fetching data for {repo['name']}: {str(e)}")
                continue
        
        return repo_data
        
    def analyze_repositories(self, repos: List[Dict[str, Any]], show_progress: bool = True, repo_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Analyze repositories with quality scoring. Can work with fresh GitHub data or cached data.
        """
        # If repos is cached data (contains quality scores), re-analyze with current config
        if repos and isinstance(repos[0], dict) and 'fetch_timestamp' in repos[0]:
            return self._reanalyze_cached_data(repos, show_progress, repo_filter)
        
        # Otherwise, fetch fresh data and analyze
        return self._analyze_fresh_repos(repos, show_progress, repo_filter)
    
    def _analyze_fresh_repos(self, repos: List[Dict[str, Any]], show_progress: bool = True, repo_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Analyze fresh repositories from GitHub API with quality scoring."""
        if repo_filter:
            repos = [repo for repo in repos if repo['name'] in repo_filter]
        
        repo_data = []
        
        if show_progress:
            repos = tqdm(repos, desc="Analyzing repositories")
        
        for repo in repos:
            try:
                repo_info = self.analyze_repository(repo, show_progress=False)
                repo_data.append(repo_info)
                
            except Exception as e:
                print(f"Error analyzing {repo['name']}: {str(e)}")
                continue
        
        return repo_data
    
    def _reanalyze_cached_data(self, cached_repos: List[Dict[str, Any]], show_progress: bool = True, repo_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Re-analyze cached repository data with current quality configuration."""
        if repo_filter:
            cached_repos = [repo for repo in cached_repos if repo['name'] in repo_filter]
        
        repo_data = []
        
        if show_progress:
            cached_repos = tqdm(cached_repos, desc="Re-analyzing cached data")
        
        for repo in cached_repos:
            try:
                # Calculate quality score with current config
                quality_data = self.calculate_quality_score(repo)
                
                # Update repo data with new quality score
                repo_info = {**repo, **quality_data}
                repo_data.append(repo_info)
                
            except Exception as e:
                print(f"Error re-analyzing {repo.get('name', 'unknown')}: {str(e)}")
                continue
        
        return repo_data
    
    def save_cached_data(self, repo_data: List[Dict[str, Any]], cache_file: str) -> None:
        """Save repository data to a JSON cache file."""
        try:
            cache_data = {
                'metadata': {
                    'org': self.org,
                    'fetch_timestamp': datetime.now().isoformat(),
                    'total_repos': len(repo_data),
                    'analyzer_version': '2.0'
                },
                'repositories': repo_data
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving cache file {cache_file}: {str(e)}")
            raise
    
    def load_cached_data(self, cache_file: str) -> List[Dict[str, Any]]:
        """Load repository data from a JSON cache file."""
        try:
            if not os.path.exists(cache_file):
                print(f"Cache file not found: {cache_file}")
                return []
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Handle both old format (direct list) and new format (with metadata)
            if isinstance(cache_data, list):
                # Old format - direct list of repositories
                return cache_data
            elif isinstance(cache_data, dict) and 'repositories' in cache_data:
                # New format - with metadata wrapper
                metadata = cache_data.get('metadata', {})
                print(f"📅 Cache from: {metadata.get('fetch_timestamp', 'unknown')}")
                print(f"🏢 Organization: {metadata.get('org', 'unknown')}")
                return cache_data['repositories']
            else:
                print("Invalid cache file format")
                return []
                
        except json.JSONDecodeError as e:
            print(f"Error parsing cache file {cache_file}: {str(e)}")
            return []
        except Exception as e:
            print(f"Error loading cache file {cache_file}: {str(e)}")
            return []
    
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
