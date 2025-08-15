#!/usr/bin/env python3
"""
GitHub Organization Statistics Script
Counts repositories and total stars for specified GitHub organizations.
"""

import requests
import sys
from typing import List, Dict, Tuple
import argparse


def get_org_stats(org_name: str, github_token: str = None) -> Tuple[int, int]:
    """
    Get repository count and total stars for a GitHub organization or user.
    
    Args:
        org_name: GitHub organization or user name
        github_token: Optional GitHub personal access token for higher rate limits
    
    Returns:
        Tuple of (repo_count, total_stars)
    """
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    repo_count = 0
    total_stars = 0
    page = 1
    per_page = 100
    
    # Try organization first
    while True:
        url = f'https://api.github.com/orgs/{org_name}/repos'
        params = {'page': page, 'per_page': per_page, 'type': 'all'}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 404:
            # Organization not found, try as user
            return get_user_stats(org_name, github_token)
        elif response.status_code != 200:
            print(f"Error fetching data for {org_name}: {response.status_code}")
            return 0, 0
        
        repos = response.json()
        
        if not repos:
            break
        
        repo_count += len(repos)
        total_stars += sum(repo['stargazers_count'] for repo in repos)
        
        page += 1
    
    return repo_count, total_stars


def get_user_stats(user_name: str, github_token: str = None) -> Tuple[int, int]:
    """
    Get repository count and total stars for a GitHub user.
    
    Args:
        user_name: GitHub user name
        github_token: Optional GitHub personal access token for higher rate limits
    
    Returns:
        Tuple of (repo_count, total_stars)
    """
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    repo_count = 0
    total_stars = 0
    page = 1
    per_page = 100
    
    while True:
        url = f'https://api.github.com/users/{user_name}/repos'
        params = {'page': page, 'per_page': per_page, 'type': 'all'}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 404:
            print(f"User '{user_name}' not found")
            return 0, 0
        elif response.status_code != 200:
            print(f"Error fetching data for {user_name}: {response.status_code}")
            return 0, 0
        
        repos = response.json()
        
        if not repos:
            break
        
        repo_count += len(repos)
        total_stars += sum(repo['stargazers_count'] for repo in repos)
        
        page += 1
    
    return repo_count, total_stars


def read_orgs_from_file(filename: str) -> List[Tuple[str, str]]:
    """Read organization names and display names from a tab-delimited file."""
    try:
        orgs = []
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        orgs.append((parts[0], parts[1]))
                    else:
                        orgs.append((parts[0], parts[0]))
        return orgs
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Count GitHub organization repositories and stars')
    parser.add_argument('organizations', nargs='*', help='GitHub organization names')
    parser.add_argument('--file', '-f', help='Tab-delimited file with organization names and display names')
    parser.add_argument('--token', help='GitHub personal access token (optional)')
    
    args = parser.parse_args()
    
    if args.file:
        org_data = read_orgs_from_file(args.file)
        orgs = [org for org, display in org_data]
    elif args.organizations:
        org_data = [(org, org) for org in args.organizations]
        orgs = args.organizations
    else:
        parser.error('Must specify either organization names or --file')
    
    if not orgs:
        print("No organizations specified")
        sys.exit(1)
    
    # Group stats by display name
    display_stats = {}
    
    for org_name, display_name in org_data:
        if display_name not in display_stats:
            display_stats[display_name] = {'repos': 0, 'stars': 0}
        
        repo_count, star_count = get_org_stats(org_name, args.token)
        display_stats[display_name]['repos'] += repo_count
        display_stats[display_name]['stars'] += star_count
    
    # Sort by total stars descending, then by repositories descending
    sorted_stats = sorted(display_stats.items(), key=lambda x: (x[1]['stars'], x[1]['repos']), reverse=True)
    
    print(f"{'Organization':<20} {'Repositories':<15} {'Total Stars':<15}")
    print("-" * 50)
    
    total_repos = 0
    total_stars = 0
    
    for display_name, stats in sorted_stats:
        print(f"{display_name:<20} {stats['repos']:<15} {stats['stars']:<15}")
        total_repos += stats['repos']
        total_stars += stats['stars']
    
    print("-" * 50)
    print(f"{'TOTAL':<20} {total_repos:<15} {total_stars:<15}")


if __name__ == '__main__':
    main()