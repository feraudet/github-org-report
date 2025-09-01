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
import os
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
    parser.add_argument(
        '--fetch-only',
        action='store_true',
        help='Only fetch data from GitHub API and save to cache file (no analysis)'
    )
    parser.add_argument(
        '--analyze-only',
        type=str,
        metavar='CACHE_FILE',
        help='Analyze data from existing cache file instead of fetching from GitHub'
    )
    parser.add_argument(
        '--cache-file',
        type=str,
        help='Specify cache file path (default: auto-generated based on org and timestamp)'
    )
    
    args = parser.parse_args()
    
    # Get token and org from args or environment variables
    token, org = get_env_variables()
    token = args.token or token
    org = args.org or org
    
    # Validate mode-specific arguments
    if args.analyze_only:
        # For analyze-only mode, we don't need token/org validation
        if not os.path.exists(args.analyze_only):
            print(f"❌ Cache file not found: {args.analyze_only}")
            return
        print(f"📊 Analyze-only mode: using cache file {args.analyze_only}")
    else:
        # For fetch modes, validate token and org
        validate_required_args(token, org)
        
    if args.fetch_only and args.analyze_only:
        print("❌ Cannot use --fetch-only and --analyze-only together")
        return
    
    # Setup SSL warnings
    setup_ssl_warnings(not args.no_ssl_verify)
    
    start_time = datetime.now()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        if args.analyze_only:
            # Mode 2: Analyze existing cached data
            print(f"📊 Loading cached data from: {args.analyze_only}")
            # Create a temporary analyzer just for loading data
            temp_analyzer = GitHubRepoAnalyzer("dummy", "dummy")
            cached_data = temp_analyzer.load_cached_data(args.analyze_only)
            
            if not cached_data:
                print("❌ No data found in cache file or invalid format.")
                return
                
            print(f"✅ Loaded {len(cached_data)} repositories from cache")
            org = cached_data[0].get('org', 'unknown') if cached_data else 'unknown'
            
            # Re-analyze cached data with current quality configuration (no API calls)
            print("🔄 Re-analyzing with current quality configuration...")
            repo_data = temp_analyzer._reanalyze_cached_data(cached_data, show_progress=should_show_progress(args.no_progress))
            
        else:
            # Mode 1: Fetch data from GitHub
            analyzer = GitHubRepoAnalyzer(token, org, api_url=args.api_url, verify_ssl=not args.no_ssl_verify)
            
            print(f"🔍 Fetching repositories for organization: {org}")
            show_progress = should_show_progress(args.no_progress)
            
            # Get repositories (with optional language filtering via GitHub API)
            repos = analyzer.get_all_repos(languages=args.languages)
            
            # Limit number of repositories if specified
            if args.limit and args.limit < len(repos):
                repos = repos[:args.limit]
                print(f"Limited analysis to first {args.limit} repositories")
            
            if args.fetch_only:
                # Mode 1a: Fetch-only mode - collect data and save to cache
                print("📥 Fetch-only mode: collecting data from GitHub...")
                repo_data = analyzer.fetch_repositories_data(repos, show_progress=show_progress, repo_filter=args.repos)
                
                if not repo_data:
                    print("No repositories found or fetched.")
                    return
                
                # Save to cache file
                cache_file = args.cache_file or f"{org}_cache_{timestamp}.json"
                analyzer.save_cached_data(repo_data, cache_file)
                
                print(f"✅ Data cached to: {cache_file}")
                print(f"📊 Fetched {len(repo_data)} repositories")
                print(f"🔄 To analyze: python main.py --analyze-only {cache_file}")
                return
                
            else:
                # Mode 1b: Full mode - fetch and analyze
                print(f"🔍 Full mode: fetching and analyzing repositories...")
                repo_data = analyzer.analyze_repositories(repos, show_progress=show_progress, repo_filter=args.repos)
        
        if not repo_data:
            print("No repositories found or analyzed.")
            return
        
        # Generate output files
        base_filename = f"{org}_repos_{timestamp}"
        
        # Save to different formats
        generate_all_outputs(repo_data, base_filename, args.output_dir)
        
        # Print summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n✅ Analysis completed!")
        print(f"📊 Analyzed {len(repo_data)} repositories in {duration}")
        print(f"📁 Files saved in directory: {args.output_dir}")
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
    except Exception as e:
        raise e


if __name__ == "__main__":
    main()
