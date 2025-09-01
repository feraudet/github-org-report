#!/usr/bin/env python3
"""
Utility Module for GitHub Repository Analyzer

Contains utility functions and configuration.
"""

import os
import sys
import warnings
import urllib3


def setup_ssl_warnings(verify_ssl: bool) -> None:
    """
    Configure SSL warning handling.
    
    Args:
        verify_ssl: Whether SSL verification is enabled
    """
    if not verify_ssl:
        # Suppress SSL warnings when verification is disabled
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')


def get_env_variables() -> tuple:
    """
    Get GitHub token and organization from environment variables.
    
    Returns:
        Tuple of (token, org) from environment variables
    """
    token = os.getenv('GITHUB_TOKEN')
    org = os.getenv('GITHUB_ORG')
    return token, org


def validate_required_args(token: str, org: str) -> None:
    """
    Validate that required arguments are provided.
    
    Args:
        token: GitHub token
        org: GitHub organization name
        
    Raises:
        SystemExit: If required arguments are missing
    """
    if not token:
        print("Error: GitHub token is required. Use --token argument or set GITHUB_TOKEN environment variable.")
        sys.exit(1)
    
    if not org:
        print("Error: GitHub organization is required. Use --org argument or set GITHUB_ORG environment variable.")
        sys.exit(1)


def should_show_progress(no_progress_flag: bool) -> bool:
    """
    Determine if progress bar should be shown.
    
    Args:
        no_progress_flag: Whether --no-progress flag was set
        
    Returns:
        Boolean indicating if progress should be shown
    """
    return sys.stdout.isatty() and not no_progress_flag
