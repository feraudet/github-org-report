"""Unit tests for the utils module."""

import unittest
from unittest.mock import patch, Mock
import os
import sys
from utils import setup_ssl_warnings, get_env_variables, validate_required_args, should_show_progress


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""

    @patch('utils.urllib3.disable_warnings')
    def test_setup_ssl_warnings_disabled(self, mock_disable_warnings):
        """Test SSL warnings setup when SSL verification is disabled."""
        setup_ssl_warnings(False)
        mock_disable_warnings.assert_called_once()

    @patch('utils.urllib3.disable_warnings')
    def test_setup_ssl_warnings_enabled(self, mock_disable_warnings):
        """Test SSL warnings setup when SSL verification is enabled."""
        setup_ssl_warnings(True)
        mock_disable_warnings.assert_not_called()

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'env_token', 'GITHUB_ORG': 'env_org'})
    def test_get_env_variables_from_env(self):
        """Test getting environment variables when they exist."""
        token, org = get_env_variables()
        self.assertEqual(token, 'env_token')
        self.assertEqual(org, 'env_org')

    @patch.dict(os.environ, {}, clear=True)
    def test_get_env_variables_missing(self):
        """Test getting environment variables when they don't exist."""
        token, org = get_env_variables()
        self.assertIsNone(token)
        self.assertIsNone(org)

    def test_validate_required_args_valid(self):
        """Test validation with valid arguments."""
        # Should not raise any exception
        validate_required_args("valid_token", "valid_org")

    def test_validate_required_args_missing_token(self):
        """Test validation with missing token."""
        with self.assertRaises(SystemExit):
            validate_required_args(None, "valid_org")

    def test_validate_required_args_missing_org(self):
        """Test validation with missing organization."""
        with self.assertRaises(SystemExit):
            validate_required_args("valid_token", None)

    def test_validate_required_args_empty_token(self):
        """Test validation with empty token."""
        with self.assertRaises(SystemExit):
            validate_required_args("", "valid_org")

    def test_validate_required_args_empty_org(self):
        """Test validation with empty organization."""
        with self.assertRaises(SystemExit):
            validate_required_args("valid_token", "")

    @patch('sys.stdout.isatty', return_value=True)
    def test_should_show_progress_terminal_no_flag(self, mock_isatty):
        """Test progress bar display in terminal without no-progress flag."""
        result = should_show_progress(False)
        self.assertTrue(result)

    @patch('sys.stdout.isatty', return_value=True)
    def test_should_show_progress_terminal_with_flag(self, mock_isatty):
        """Test progress bar display in terminal with no-progress flag."""
        result = should_show_progress(True)
        self.assertFalse(result)

    @patch('sys.stdout.isatty', return_value=False)
    def test_should_show_progress_non_terminal(self, mock_isatty):
        """Test progress bar display in non-terminal environment."""
        result = should_show_progress(False)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
