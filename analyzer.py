#!/usr/bin/env python3
"""
GitHub Repository Analyzer Module

Contains the main GitHubRepoAnalyzer class for analyzing GitHub repositories.
"""

import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
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
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Repo-Analyzer'
        }
        self.base_url = api_url
        self.verify_ssl = verify_ssl
        
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
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages."""
        return sorted(list(set(self.code_type_mappings.values())))
    
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
            elif response.status_code == 409:
                # Handle 409 Conflict errors (usually branch/commit issues)
                print(f"Conflict error accessing {url} - repository may be empty or have branch issues")
                return None
            else:
                print(f"HTTP Error making request to {url}: {e}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
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
<<<<<<< Updated upstream
        
        # Try to get commit count from contributors API (most reliable)
        contributors_data = self.make_request(f"{self.base_url}/repos/{self.org}/{repo_name}/stats/contributors")
        if contributors_data and isinstance(contributors_data, list):
            # Sum up all commits from all contributors
            total_commits = sum(contributor.get('total', 0) for contributor in contributors_data)
        
=======
        
        # Try to get commit count from contributors API (most reliable)
        contributors_data = self.make_request(f"{self.base_url}/repos/{self.org}/{repo_name}/stats/contributors")
        if contributors_data and isinstance(contributors_data, list):
            # Sum up all commits from all contributors
            total_commits = sum(contributor.get('total', 0) for contributor in contributors_data)
        
>>>>>>> Stashed changes
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
        
        search_response = requests.get(search_url, headers=self.headers, params=search_params, verify=self.verify_ssl)
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            prs = search_data.get('items', [])
            
            if prs:
                print(f"Found {len(prs)} closed PRs for {repo_name} via search API")
                return self._analyze_closed_prs(repo_name, prs)
            else:
                print(f"No closed PRs found via search API for {repo_name}")
        else:
            print(f"Search API failed for {repo_name}: {search_response.status_code} - {search_response.text[:200]}")
        
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
            closed_response = requests.get(pulls_url, headers=self.headers, params=closed_params, verify=self.verify_ssl)
            
            if closed_response.status_code == 200:
                closed_prs = closed_response.json()
                if not closed_prs:  # No more PRs
                    break
                    
                all_closed_prs.extend(closed_prs)
                print(f"Found {len(closed_prs)} closed PRs on page {page} for {repo_name}")
                
                if len(closed_prs) < 100:  # Last page
                    break
                    
                page += 1
            else:
                print(f"Pulls API failed on page {page} for {repo_name}: {closed_response.status_code}")
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
        
        for pr in prs:
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
            
            # Get detailed PR information
            pr_details = self._get_pr_details(repo_name, pr_number)
            if pr_details:
                # Count comments
                total_comments += pr_details.get('comments', 0) + pr_details.get('review_comments', 0)
                
                # Count files and lines changed
                total_files_changed += pr_details.get('changed_files', 0)
                total_lines_added += pr_details.get('additions', 0)
                total_lines_deleted += pr_details.get('deletions', 0)
            
            # Analyze reviews
            review_analysis = self._analyze_pr_reviews(repo_name, pr_number, pr_author)
            if review_analysis['approved_by_author']:
                analysis['self_approved_prs'] += 1
            if review_analysis['approved_by_others']:
                analysis['prs_reviewed_by_others'] += 1
            if review_analysis['multiple_reviewers']:
                analysis['prs_with_multiple_reviewers'] += 1
        
        # Calculate averages
        if analysis['total_analyzed_prs'] > 0:
            analysis['avg_comments_per_pr'] = round(total_comments / analysis['total_analyzed_prs'], 1)
            analysis['avg_files_changed'] = round(total_files_changed / analysis['total_analyzed_prs'], 1)
            analysis['avg_lines_added'] = round(total_lines_added / analysis['total_analyzed_prs'], 1)
            analysis['avg_lines_deleted'] = round(total_lines_deleted / analysis['total_analyzed_prs'], 1)
        
        if merged_count > 0:
            analysis['avg_time_to_merge_hours'] = round(total_merge_time / merged_count, 1)
        
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
        Calculate a quality score for the repository based on various metrics.
{{ ... }}
        
        Args:
            repo_data: Repository data dictionary
            
        Returns:
            Dictionary with quality score and justification
        """
        score = 100  # Start with perfect score
        justifications = []
        
        # PR Review Quality (30 points max)
        total_prs = repo_data.get('total_analyzed_prs', 0)
        if total_prs > 0:
            self_approved = repo_data.get('self_approved_prs', 0)
            reviewed_by_others = repo_data.get('prs_reviewed_by_others', 0)
            
            self_approval_ratio = self_approved / total_prs
            external_review_ratio = reviewed_by_others / total_prs
            
            if self_approval_ratio > 0.5:
                penalty = min(25, int(self_approval_ratio * 30))
                score -= penalty
                justifications.append(f"High self-approval rate ({self_approval_ratio:.1%}) reduces score by {penalty} points")
            
            if external_review_ratio > 0.7:
                bonus = min(10, int(external_review_ratio * 15))
                justifications.append(f"Good external review rate ({external_review_ratio:.1%}) maintains high score")
            elif external_review_ratio < 0.3:
                penalty = min(15, int((0.3 - external_review_ratio) * 50))
                score -= penalty
                justifications.append(f"Low external review rate ({external_review_ratio:.1%}) reduces score by {penalty} points")
        else:
            justifications.append("No PRs to analyze for review quality")
        
        # Branch Discipline (25 points max)
        total_commits = repo_data.get('total_commits', 0)
        direct_pushes = repo_data.get('direct_pushes_to_default', 0)
        
        if total_commits > 0:
            direct_push_ratio = direct_pushes / total_commits
            if direct_push_ratio > 0.5:
                penalty = min(20, int(direct_push_ratio * 25))
                score -= penalty
                justifications.append(f"High direct push ratio ({direct_push_ratio:.1%}) reduces score by {penalty} points")
            elif direct_push_ratio < 0.2:
                justifications.append(f"Good branch discipline with low direct push ratio ({direct_push_ratio:.1%})")
        
        # Documentation Quality (20 points max)
        if total_prs > 0:
            prs_with_desc = repo_data.get('prs_with_description', 0)
            description_ratio = prs_with_desc / total_prs
            
            if description_ratio < 0.5:
                penalty = min(15, int((0.5 - description_ratio) * 30))
                score -= penalty
                justifications.append(f"Low PR description rate ({description_ratio:.1%}) reduces score by {penalty} points")
            else:
                justifications.append(f"Good documentation with {description_ratio:.1%} of PRs having descriptions")
        
        # Collaboration Level (15 points max)
        contributors = repo_data.get('contributors_count', 0)
        if contributors == 1:
            score -= 10
            justifications.append("Single contributor reduces collaboration score by 10 points")
        elif contributors >= 5:
            justifications.append(f"Good collaboration with {contributors} contributors")
        elif contributors >= 3:
            justifications.append(f"Moderate collaboration with {contributors} contributors")
        
        # Activity Level (10 points max)
        if repo_data.get('total_commits', 0) == 0:
            score -= 10
            justifications.append("No commits found reduces score by 10 points")
        elif repo_data.get('last_commit_date'):
            # Check if last commit is recent (within 6 months)
            try:
                last_commit = datetime.fromisoformat(repo_data['last_commit_date'].replace('Z', '+00:00'))
                days_since_last_commit = (datetime.now(last_commit.tzinfo) - last_commit).days
                
                if days_since_last_commit > 365:
                    score -= 5
                    justifications.append(f"Last commit was {days_since_last_commit} days ago, reducing score by 5 points")
                elif days_since_last_commit <= 30:
                    justifications.append("Recent activity maintains score")
            except:
                pass
        
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
