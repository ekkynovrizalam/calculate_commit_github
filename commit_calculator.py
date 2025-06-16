#!/usr/bin/env python3
"""
GitHub Commit Calculator
Calculate user commits across all branches in a GitHub repository.
"""

import os
import sys
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import click
from github import Github, GithubException
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv()

console = Console()


class GitHubCommitCalculator:
    """Calculate user commits across all branches in a GitHub repository."""
    
    def __init__(self, token: str, org_name: str, repo_name: str, exclude_merge_commits: bool = True, count_unique_commits: bool = False):
        """
        Initialize the calculator.
        
        Args:
            token: GitHub personal access token
            org_name: GitHub organization name
            repo_name: Repository name
            exclude_merge_commits: Whether to exclude merge commits from analysis
            count_unique_commits: Whether to count only unique commits (based on message and changes)
        """
        self.github = Github(token)
        self.org_name = org_name
        self.repo_name = repo_name
        self.exclude_merge_commits = exclude_merge_commits
        self.count_unique_commits = count_unique_commits
        self.repo = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with GitHub and get repository."""
        try:
            # Try to get organization repository
            org = self.github.get_organization(self.org_name)
            self.repo = org.get_repo(self.repo_name)
            console.print(f"✅ Successfully connected to {self.org_name}/{self.repo_name}", style="green")
        except GithubException as e:
            if e.status == 404:
                console.print(f"❌ Repository {self.org_name}/{self.repo_name} not found", style="red")
                sys.exit(1)
            elif e.status == 401:
                console.print("❌ Authentication failed. Please check your GitHub token.", style="red")
                sys.exit(1)
            else:
                console.print(f"❌ Error: {e}", style="red")
                sys.exit(1)
    
    def get_all_branches(self) -> List[str]:
        """Get all branches in the repository."""
        branches = []
        try:
            for branch in self.repo.get_branches():
                branches.append(branch.name)
            console.print(f"📋 Found {len(branches)} branches", style="blue")
            return branches
        except GithubException as e:
            console.print(f"❌ Error fetching branches: {e}", style="red")
            return []
    
    def is_merge_commit(self, commit) -> bool:
        """Check if a commit is a merge commit."""
        # Check if commit has multiple parents (merge commit)
        if len(commit.parents) > 1:
            return True
        
        # Check commit message for merge indicators
        message = commit.commit.message.lower()
        merge_indicators = [
            'merge pull request',
            'merge branch',
            'merge remote',
            'merge from',
            'merge into',
            'merge:',
            'merged',
            'merging'
        ]
        
        return any(indicator in message for indicator in merge_indicators)
    
    def get_commits_for_branch(self, branch_name: str) -> List[Dict]:
        """Get all commits for a specific branch, excluding merge commits if configured."""
        commits = []
        merge_commits_excluded = 0
        
        try:
            for commit in self.repo.get_commits(sha=branch_name):
                # Skip merge commits if configured to exclude them
                if self.exclude_merge_commits and self.is_merge_commit(commit):
                    merge_commits_excluded += 1
                    continue
                
                # Get commit details for uniqueness checking
                commit_data = {
                    'sha': commit.sha[:8],
                    'full_sha': commit.sha,
                    'author': commit.author.login if commit.author else 'Unknown',
                    'author_name': commit.commit.author.name,
                    'date': commit.commit.author.date,
                    'message': commit.commit.message,
                    'message_short': commit.commit.message.split('\n')[0][:50] + '...' if len(commit.commit.message) > 50 else commit.commit.message,
                    'branch': branch_name,
                    'parents': [p.sha for p in commit.parents]
                }
                
                # If counting unique commits, get the tree SHA (represents the actual changes)
                if self.count_unique_commits:
                    commit_data['tree_sha'] = commit.commit.tree.sha
                
                commits.append(commit_data)
            
            if self.exclude_merge_commits and merge_commits_excluded > 0:
                console.print(f"📝 Branch {branch_name}: Excluded {merge_commits_excluded} merge commits", style="dim")
            
            return commits
        except GithubException as e:
            console.print(f"⚠️  Error fetching commits for branch {branch_name}: {e}", style="yellow")
            return []
    
    def calculate_commits(self, branches: Optional[List[str]] = None) -> Dict:
        """
        Calculate commits across all branches or specified branches.
        
        Args:
            branches: List of branch names to analyze. If None, analyze all branches.
        
        Returns:
            Dictionary with commit statistics
        """
        if branches is None:
            branches = self.get_all_branches()
        
        all_commits = []
        user_stats = defaultdict(lambda: {
            'total_commits': 0,
            'unique_commits': 0,
            'branches': set(),
            'commits_by_branch': defaultdict(int),
            'unique_commits_by_branch': defaultdict(int),
            'first_commit': None,
            'last_commit': None
        })
        
        # Track unique commits across all users
        seen_commits = set()  # (author, message, tree_sha) tuples
        duplicate_commits = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing commits...", total=len(branches))
            
            for branch in branches:
                progress.update(task, description=f"Processing branch: {branch}")
                commits = self.get_commits_for_branch(branch)
                
                for commit in commits:
                    author = commit['author']
                    message = commit['message']
                    tree_sha = commit.get('tree_sha', '') if self.count_unique_commits else ''
                    
                    # Create unique identifier for the commit
                    if self.count_unique_commits:
                        commit_key = (author, message, tree_sha)
                    else:
                        commit_key = (author, message, commit['full_sha'])
                    
                    # Check if this is a unique commit
                    is_unique = commit_key not in seen_commits
                    if is_unique:
                        seen_commits.add(commit_key)
                        user_stats[author]['unique_commits'] += 1
                        user_stats[author]['unique_commits_by_branch'][branch] += 1
                    else:
                        duplicate_commits += 1
                    
                    # Always count total commits
                    user_stats[author]['total_commits'] += 1
                    user_stats[author]['branches'].add(branch)
                    user_stats[author]['commits_by_branch'][branch] += 1
                    
                    # Track first and last commit dates
                    commit_date = commit['date']
                    if user_stats[author]['first_commit'] is None or commit_date < user_stats[author]['first_commit']:
                        user_stats[author]['first_commit'] = commit_date
                    if user_stats[author]['last_commit'] is None or commit_date > user_stats[author]['last_commit']:
                        user_stats[author]['last_commit'] = commit_date
                
                all_commits.extend(commits)
                progress.advance(task)
        
        # Convert sets to lists for JSON serialization
        for user in user_stats:
            user_stats[user]['branches'] = list(user_stats[user]['branches'])
            user_stats[user]['commits_by_branch'] = dict(user_stats[user]['commits_by_branch'])
            user_stats[user]['unique_commits_by_branch'] = dict(user_stats[user]['unique_commits_by_branch'])
        
        if self.count_unique_commits and duplicate_commits > 0:
            console.print(f"🔍 Found {duplicate_commits} duplicate commits across all users", style="blue")
        
        return {
            'total_commits': len(all_commits),
            'unique_commits': len(seen_commits),
            'duplicate_commits': duplicate_commits,
            'total_branches': len(branches),
            'user_stats': dict(user_stats),
            'all_commits': all_commits
        }
    
    def display_summary(self, stats: Dict):
        """Display a summary of commit statistics."""
        console.print("\n📊 COMMIT SUMMARY", style="bold blue")
        console.print("=" * 50)
        
        summary_table = Table(title="Repository Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")
        
        summary_table.add_row("Total Commits", str(stats['total_commits']))
        if self.count_unique_commits:
            summary_table.add_row("Unique Commits", str(stats['unique_commits']))
            summary_table.add_row("Duplicate Commits", str(stats['duplicate_commits']))
        summary_table.add_row("Total Branches", str(stats['total_branches']))
        summary_table.add_row("Active Contributors", str(len(stats['user_stats'])))
        
        console.print(summary_table)
    
    def display_user_stats(self, stats: Dict, detailed: bool = False):
        """Display user commit statistics."""
        console.print("\n👥 USER COMMIT STATISTICS", style="bold blue")
        console.print("=" * 50)
        
        # Sort users by unique commits if enabled, otherwise by total commits
        if self.count_unique_commits:
            sort_key = lambda x: x[1]['unique_commits']
            commit_column = "Unique Commits"
        else:
            sort_key = lambda x: x[1]['total_commits']
            commit_column = "Total Commits"
        
        sorted_users = sorted(
            stats['user_stats'].items(),
            key=sort_key,
            reverse=True
        )
        
        user_table = Table(title="User Commit Statistics")
        user_table.add_column("Rank", style="cyan", justify="center")
        user_table.add_column("User", style="green")
        user_table.add_column(commit_column, style="magenta", justify="center")
        if self.count_unique_commits:
            user_table.add_column("Total Commits", style="yellow", justify="center")
        user_table.add_column("Branches", style="yellow", justify="center")
        user_table.add_column("First Commit", style="blue")
        user_table.add_column("Last Commit", style="blue")
        
        for rank, (user, user_data) in enumerate(sorted_users, 1):
            first_commit = user_data['first_commit'].strftime('%Y-%m-%d') if user_data['first_commit'] else 'N/A'
            last_commit = user_data['last_commit'].strftime('%Y-%m-%d') if user_data['last_commit'] else 'N/A'
            
            row_data = [
                str(rank),
                user,
                str(user_data['unique_commits'] if self.count_unique_commits else user_data['total_commits']),
                str(len(user_data['branches'])),
                first_commit,
                last_commit
            ]
            
            if self.count_unique_commits:
                row_data.insert(3, str(user_data['total_commits']))
            
            user_table.add_row(*row_data)
        
        console.print(user_table)
        
        if detailed:
            self.display_detailed_branch_stats(stats)
    
    def display_detailed_branch_stats(self, stats: Dict):
        """Display detailed branch statistics for each user."""
        console.print("\n🌿 DETAILED BRANCH STATISTICS", style="bold blue")
        console.print("=" * 50)
        
        # Sort users by unique commits if enabled, otherwise by total commits
        if self.count_unique_commits:
            sort_key = lambda x: x[1]['unique_commits']
            commit_type = "unique commits"
        else:
            sort_key = lambda x: x[1]['total_commits']
            commit_type = "commits"
        
        for user, user_data in sorted(
            stats['user_stats'].items(),
            key=sort_key,
            reverse=True
        ):
            commit_count = user_data['unique_commits'] if self.count_unique_commits else user_data['total_commits']
            console.print(f"\n👤 {user} ({commit_count} {commit_type})", style="bold green")
            
            branch_table = Table(title=f"Branch Activity for {user}")
            branch_table.add_column("Branch", style="cyan")
            if self.count_unique_commits:
                branch_table.add_column("Unique Commits", style="magenta", justify="center")
                branch_table.add_column("Total Commits", style="yellow", justify="center")
            else:
                branch_table.add_column("Commits", style="magenta", justify="center")
            branch_table.add_column("Percentage", style="yellow", justify="center")
            
            # Get the appropriate commit data
            if self.count_unique_commits:
                branch_data = user_data['unique_commits_by_branch']
                total_commits = user_data['unique_commits']
            else:
                branch_data = user_data['commits_by_branch']
                total_commits = user_data['total_commits']
            
            for branch, commits in sorted(
                branch_data.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                percentage = (commits / total_commits) * 100
                
                if self.count_unique_commits:
                    total_branch_commits = user_data['commits_by_branch'].get(branch, 0)
                    branch_table.add_row(
                        branch,
                        str(commits),
                        str(total_branch_commits),
                        f"{percentage:.1f}%"
                    )
                else:
                    branch_table.add_row(
                        branch,
                        str(commits),
                        f"{percentage:.1f}%"
                    )
            
            console.print(branch_table)


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        console.print(f"⚠️  Config file {config_path} not found. Using CLI options only.", style="yellow")
        return {}
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}


@click.command()
@click.option('--config', '-c', default='config.yaml', help='Path to config YAML file')
@click.option('--org', '-o', help='GitHub organization name')
@click.option('--repo', '-r', help='Repository name')
@click.option('--token', '-t', envvar='GITHUB_TOKEN', help='GitHub personal access token')
@click.option('--branches', '-b', multiple=True, help='Specific branches to analyze (can be used multiple times)')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed branch statistics for each user')
@click.option('--include-merge-commits', is_flag=True, help='Include merge commits in the analysis (default: exclude)')
@click.option('--unique-only', is_flag=True, help='Count only unique commits (exclude duplicates across branches)')
@click.option('--output', '-O', type=click.Path(), help='Output file for results (JSON format)')
def main(config, org, repo, token, branches, detailed, include_merge_commits, unique_only, output):
    """
    Calculate user commits across all branches in a GitHub repository.
    """
    # Load config file
    config_data = load_config(config)
    
    # Use config values as defaults, CLI overrides if provided
    org = org or config_data.get('organization')
    repo = repo or config_data.get('repository')
    token = token or os.getenv('GITHUB_TOKEN')
    branch_list = list(branches) if branches else config_data.get('branches')
    if branch_list == []:
        branch_list = None
    
    # Determine whether to exclude merge commits (default: exclude)
    exclude_merge_commits = not include_merge_commits
    
    if not token:
        console.print("❌ GitHub token is required. Set GITHUB_TOKEN environment variable, .env file, or use --token option.", style="red")
        sys.exit(1)
    if not org or not repo:
        console.print("❌ Organization and repository are required. Set in config.yaml or use --org/--repo options.", style="red")
        sys.exit(1)
    
    try:
        calculator = GitHubCommitCalculator(token, org, repo, exclude_merge_commits, unique_only)
        console.print(f"🚀 Starting commit analysis for {org}/{repo}", style="bold green")
        if exclude_merge_commits:
            console.print("🔍 Merge commits will be excluded from analysis", style="blue")
        else:
            console.print("🔍 Including merge commits in analysis", style="blue")
        if unique_only:
            console.print("🔍 Counting only unique commits (excluding duplicates across branches)", style="blue")
        stats = calculator.calculate_commits(branch_list)
        calculator.display_summary(stats)
        calculator.display_user_stats(stats, detailed)
        if output:
            import json
            serializable_stats = stats.copy()
            for user_data in serializable_stats['user_stats'].values():
                if user_data['first_commit']:
                    user_data['first_commit'] = user_data['first_commit'].isoformat()
                if user_data['last_commit']:
                    user_data['last_commit'] = user_data['last_commit'].isoformat()
            with open(output, 'w') as f:
                json.dump(serializable_stats, f, indent=2)
            console.print(f"💾 Results saved to {output}", style="green")
        console.print("\n✅ Analysis complete!", style="bold green")
    except KeyboardInterrupt:
        console.print("\n⚠️  Analysis interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main() 