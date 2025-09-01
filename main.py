#!/usr/bin/env python3
"""
GitHub Repository Analyzer

This script analyzes all repositories in a GitHub organization and generates reports
in JSON, Excel, and CSV formats with comprehensive repository information.

Usage:
    python main.py --org <organization_name> --token <github_token>
    
Environment variables:
    GITHUB_TOKEN: GitHub Personal Access Token
    GITHUB_ORG: GitHub organization name
"""

import argparse
from datetime import datetime
from analyzer import GitHubRepoAnalyzer
from output import generate_all_outputs
from utils import setup_ssl_warnings, get_env_variables, validate_required_args, should_show_progress

def main():
    """Main function to run the GitHub repository analyzer."""
    # Create argument parser
    parser = argparse.ArgumentParser(
        description='Analyze GitHub repositories for an organization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --org myorg --token ghp_xxxxxxxxxxxx
  %(prog)s --org myorg --token ghp_xxxxxxxxxxxx --limit 10
  %(prog)s --org myorg --token ghp_xxxxxxxxxxxx --languages Python JavaScript
  %(prog)s --org myorg --token ghp_xxxxxxxxxxxx --repos repo1 repo2 repo3
  %(prog)s --org myorg --token ghp_xxxxxxxxxxxx --no-ssl-verify --api-url https://github.enterprise.com/api/v3

Environment Variables:
  GITHUB_TOKEN    GitHub Personal Access Token
  GITHUB_ORG      GitHub organization name
        """
    )
    
    parser.add_argument(
        '--org',
        type=str,
        help='GitHub organization name (can also use GITHUB_ORG environment variable)'
    )
    parser.add_argument(
        '--token',
        type=str,
        help='GitHub Personal Access Token (can also use GITHUB_TOKEN environment variable)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Output directory for generated files (default: current directory)'
    )
    def validate_positive_int(value):
        """Validate that the value is a positive integer."""
        try:
            ivalue = int(value)
            if ivalue <= 0:
                raise argparse.ArgumentTypeError(f"'{value}' must be a positive integer")
            return ivalue
        except ValueError:
            raise argparse.ArgumentTypeError(f"'{value}' is not a valid integer (check for special characters like Ø)")
    
    parser.add_argument(
        '--limit',
        type=validate_positive_int,
        help='Maximum number of repositories to analyze (must be a positive integer)'
    )
    
    # Create temporary analyzer to get supported languages list
    temp_analyzer = GitHubRepoAnalyzer('dummy', 'dummy')
    supported_langs = temp_analyzer.get_supported_languages()
    
    parser.add_argument(
        '--languages',
        nargs='+',
        help=f'Filter repositories by programming languages. Supported: {", ".join(supported_langs[:10])}... (e.g., --languages Python JavaScript Java)'
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
    token, org = get_env_variables()
    token = args.token or token
    org = args.org or org
    
    # Validate required arguments
    validate_required_args(token, org)
    
    # Setup SSL warnings
    setup_ssl_warnings(not args.no_ssl_verify)
    
    # Initialize analyzer
    analyzer = GitHubRepoAnalyzer(token, org, api_url=args.api_url, verify_ssl=not args.no_ssl_verify)
    
    # Analyze repositories
    print(f"Starting analysis of repositories for organization: {org}")
    start_time = datetime.now()
    
    try:
        # Detect if running in a terminal
        show_progress = should_show_progress(args.no_progress)
        
        # Get repositories (with optional language filtering via GitHub API)
        repos = analyzer.get_all_repos(languages=args.languages)
        
        # Limit number of repositories if specified
        if args.limit and args.limit < len(repos):
            repos = repos[:args.limit]
            print(f"Limited analysis to first {args.limit} repositories")
        
        # Analyze repositories
        repo_data = analyzer.analyze_repositories(repos, show_progress=show_progress, repo_filter=args.repos)
        
        if not repo_data:
            print("No repositories found or analyzed.")
            return
        
        # Generate output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"{org}_repos_{timestamp}"
        
        # Save to different formats
        generate_all_outputs(repo_data, base_filename, args.output_dir)
        
        # Print summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\nAnalysis completed!")
        print(f"Analyzed {len(repo_data)} repositories in {duration}")
        print(f"Files saved in directory: {args.output_dir}")
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
    except Exception as e:
        raise e


if __name__ == "__main__":
    main()
