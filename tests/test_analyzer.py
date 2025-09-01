"""Unit tests for the analyzer module."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from analyzer import GitHubRepoAnalyzer


class TestGitHubRepoAnalyzer(unittest.TestCase):
    """Test cases for GitHubRepoAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = GitHubRepoAnalyzer("test_token", "test_org")

    def test_init(self):
        """Test analyzer initialization."""
        self.assertEqual(self.analyzer.token, "test_token")
        self.assertEqual(self.analyzer.org, "test_org")
        self.assertEqual(self.analyzer.base_url, "https://api.github.com")
        self.assertTrue(self.analyzer.verify_ssl)

    def test_init_with_custom_api_url(self):
        """Test analyzer initialization with custom API URL."""
        analyzer = GitHubRepoAnalyzer("token", "org", api_url="https://github.enterprise.com/api/v3")
        self.assertEqual(analyzer.base_url, "https://github.enterprise.com/api/v3")

    def test_get_supported_languages(self):
        """Test getting supported languages."""
        languages = self.analyzer.get_supported_languages()
        self.assertIsInstance(languages, list)
        self.assertIn("Python", languages)
        self.assertIn("JavaScript", languages)
        self.assertIn("HCL", languages)

    @patch('analyzer.requests.get')
    def test_make_request_success(self, mock_get):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.analyzer.make_request("https://api.github.com/test")
        
        self.assertEqual(result, {"test": "data"})
        mock_get.assert_called_once_with(
            "https://api.github.com/test",
            headers=self.analyzer.headers,
            params=None,
            verify=True
        )

    @patch('analyzer.requests.get')
    def test_make_request_404_error(self, mock_get):
        """Test API request with 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        result = self.analyzer.make_request("https://api.github.com/test")
        
        self.assertIsNone(result)

    @patch('analyzer.requests.get')
    def test_make_request_other_error(self, mock_get):
        """Test API request with non-404 error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("500 Server Error")
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            result = self.analyzer.make_request("https://api.github.com/test")
            
        self.assertIsNone(result)
        mock_print.assert_called()

    @patch.object(GitHubRepoAnalyzer, 'make_request')
    def test_get_all_org_repos(self, mock_request):
        """Test getting all organization repositories."""
        # Mock paginated response
        mock_request.side_effect = [
            [{"name": "repo1"}, {"name": "repo2"}],  # Page 1
            [{"name": "repo3"}],  # Page 2
            []  # Page 3 (empty)
        ]

        with patch('builtins.print'):
            repos = self.analyzer._get_all_org_repos()

        self.assertEqual(len(repos), 3)
        self.assertEqual(repos[0]["name"], "repo1")
        self.assertEqual(repos[2]["name"], "repo3")

    @patch.object(GitHubRepoAnalyzer, 'make_request')
    def test_get_repos_by_language(self, mock_request):
        """Test getting repositories filtered by language."""
        mock_request.return_value = {
            "items": [
                {"name": "python-repo", "language": "Python"},
                {"name": "js-repo", "language": "JavaScript"}
            ]
        }

        with patch('builtins.print'):
            repos = self.analyzer._get_repos_by_language(["Python", "JavaScript"])

        self.assertEqual(len(repos), 2)
        mock_request.assert_called_with(
            "https://api.github.com/search/repositories",
            {
                'q': 'org:test_org lang:Python OR lang:JavaScript',
                'page': 1,
                'per_page': 100,
                'sort': 'updated',
                'order': 'desc'
            }
        )

    @patch.object(GitHubRepoAnalyzer, 'make_request')
    def test_detect_code_types(self, mock_request):
        """Test code type detection."""
        mock_request.return_value = [
            {"type": "file", "name": "main.py"},
            {"type": "file", "name": "script.js"},
            {"type": "file", "name": "config.tf"},
            {"type": "dir", "name": "src"}
        ]

        code_types = self.analyzer.detect_code_types("test-repo")
        
        self.assertIn("Python", code_types)
        self.assertIn("JavaScript", code_types)
        self.assertIn("Terraform", code_types)
        self.assertNotIn("Unknown", code_types)

    @patch.object(GitHubRepoAnalyzer, 'make_request')
    def test_detect_code_types_empty_repo(self, mock_request):
        """Test code type detection for empty repository."""
        mock_request.return_value = None

        code_types = self.analyzer.detect_code_types("empty-repo")
        
        self.assertEqual(code_types, [])

    @patch('analyzer.requests.get')
    def test_get_pull_requests_count(self, mock_get):
        """Test getting pull request counts."""
        # Mock responses for open and closed PRs
        mock_responses = [
            Mock(status_code=200, json=lambda: {"total_count": 5}),  # Open PRs
            Mock(status_code=200, json=lambda: {"total_count": 25})  # Closed PRs
        ]
        mock_get.side_effect = mock_responses

        pr_counts = self.analyzer.get_pull_requests_count("test-repo")
        
        self.assertEqual(pr_counts["open"], 5)
        self.assertEqual(pr_counts["closed"], 25)

    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        repo_data = {
            'total_analyzed_prs': 10,
            'prs_reviewed_by_others': 8,
            'self_approved_prs': 1,
            'total_commits': 100,
            'direct_pushes_to_default': 5,
            'prs_with_description': 9,
            'contributors_count': 5
        }

        result = self.analyzer.calculate_quality_score(repo_data)
        
        self.assertIn('quality_score', result)
        self.assertIn('quality_justification', result)
        self.assertIsInstance(result['quality_score'], int)
        self.assertGreaterEqual(result['quality_score'], 0)
        self.assertLessEqual(result['quality_score'], 100)


if __name__ == '__main__':
    unittest.main()
