#!/usr/bin/env python3
"""
Investigate suspicious commit patterns for a specific user.
"""

import os
import sys
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import click
from github import Github, GithubException
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

console = Console()


class CommitInvestigator:
    """Investigate suspicious commit patterns for a specific user."""
    
    def __init__(self, token: str, org_name: str, repo_name: str):
        """Initialize the investigator."""
        self.github = Github(token)
        self.org_name = org_name
        self.repo_name = repo_name
        self.repo = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with GitHub and get repository."""
        try:
            org = self.github.get_organization(self.org_name)
            self.repo = org.get_repo(self.repo_name)
            console.print(f"✅ Successfully connected to {self.org_name}/{self.repo_name}", style="green")
        except GithubException as e:
            console.print(f"❌ Error: {e}", style="red")
            sys.exit(1)
    
    def investigate_user_commits(self, username: str) -> Dict:
        """Investigate commits for a specific user."""
        console.print(f"🔍 Investigating commits for user: {username}", style="bold blue")
        
        user_commits = []
        commit_messages = []
        commit_times = []
        branches_analyzed = set()
        
        # Get all branches
        branches = [branch.name for branch in self.repo.get_branches()]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing user commits...", total=len(branches))
            
            for branch in branches:
                progress.update(task, description=f"Processing branch: {branch}")
                
                try:
                    for commit in self.repo.get_commits(sha=branch):
                        if commit.author and commit.author.login == username:
                            commit_data = {
                                'sha': commit.sha[:8],
                                'message': commit.commit.message,
                                'date': commit.commit.author.date,
                                'branch': branch,
                                'parents': len(commit.parents)
                            }
                            user_commits.append(commit_data)
                            commit_messages.append(commit.commit.message)
                            commit_times.append(commit.commit.author.date)
                            branches_analyzed.add(branch)
                except GithubException as e:
                    console.print(f"⚠️  Error on branch {branch}: {e}", style="yellow")
                
                progress.advance(task)
        
        # Analyze patterns
        analysis = self._analyze_commit_patterns(user_commits, commit_messages, commit_times)
        
        return {
            'total_commits': len(user_commits),
            'branches_contributed': len(branches_analyzed),
            'commit_details': user_commits,
            'analysis': analysis
        }
    
    def _analyze_commit_patterns(self, commits: List[Dict], messages: List[str], times: List[datetime]) -> Dict:
        """Analyze commit patterns for suspicious activity."""
        
        # Message analysis
        message_counter = Counter(messages)
        duplicate_messages = {msg: count for msg, count in message_counter.items() if count > 1}
        
        # Time analysis
        times.sort()
        time_diffs = []
        for i in range(1, len(times)):
            diff = times[i] - times[i-1]
            time_diffs.append(diff.total_seconds())
        
        # Branch distribution
        branch_counter = Counter([commit['branch'] for commit in commits])
        
        # Commit frequency by hour
        hour_counter = Counter([time.hour for time in times])
        
        # Commit frequency by day of week
        day_counter = Counter([time.weekday() for time in times])
        
        return {
            'duplicate_messages': duplicate_messages,
            'total_duplicates': sum(count - 1 for count in duplicate_messages.values()),
            'time_analysis': {
                'total_commits': len(commits),
                'time_span_days': (times[-1] - times[0]).days if times else 0,
                'avg_commits_per_day': len(commits) / ((times[-1] - times[0]).days + 1) if times else 0,
                'min_time_diff_seconds': min(time_diffs) if time_diffs else 0,
                'max_time_diff_seconds': max(time_diffs) if time_diffs else 0,
                'avg_time_diff_seconds': sum(time_diffs) / len(time_diffs) if time_diffs else 0
            },
            'branch_distribution': dict(branch_counter),
            'hour_distribution': dict(hour_counter),
            'day_distribution': dict(day_counter)
        }
    
    def display_investigation_results(self, username: str, results: Dict):
        """Display investigation results."""
        console.print(f"\n🔍 INVESTIGATION RESULTS FOR {username.upper()}", style="bold red")
        console.print("=" * 60)
        
        # Summary
        summary_table = Table(title="User Commit Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")
        
        summary_table.add_row("Total Commits", str(results['total_commits']))
        summary_table.add_row("Branches Contributed", str(results['branches_contributed']))
        summary_table.add_row("Duplicate Messages", str(results['analysis']['total_duplicates']))
        summary_table.add_row("Time Span (Days)", str(results['analysis']['time_analysis']['time_span_days']))
        summary_table.add_row("Avg Commits/Day", f"{results['analysis']['time_analysis']['avg_commits_per_day']:.1f}")
        summary_table.add_row("Min Time Between Commits", f"{results['analysis']['time_analysis']['min_time_diff_seconds']:.1f}s")
        
        console.print(summary_table)
        
        # Suspicious indicators
        console.print("\n🚨 SUSPICIOUS INDICATORS", style="bold red")
        console.print("=" * 60)
        
        suspicious_count = 0
        
        # Check for duplicate messages
        if results['analysis']['total_duplicates'] > 0:
            console.print(f"⚠️  {results['analysis']['total_duplicates']} duplicate commit messages found", style="red")
            suspicious_count += 1
        
        # Check for very high daily commit rate
        daily_rate = results['analysis']['time_analysis']['avg_commits_per_day']
        if daily_rate > 20:
            console.print(f"⚠️  Very high daily commit rate: {daily_rate:.1f} commits/day", style="red")
            suspicious_count += 1
        
        # Check for very short time between commits
        min_diff = results['analysis']['time_analysis']['min_time_diff_seconds']
        if min_diff < 60:  # Less than 1 minute
            console.print(f"⚠️  Very short time between commits: {min_diff:.1f} seconds", style="red")
            suspicious_count += 1
        
        # Check for uniform branch distribution
        branch_dist = results['analysis']['branch_distribution']
        if len(branch_dist) > 10:
            avg_per_branch = results['total_commits'] / len(branch_dist)
            variance = sum((count - avg_per_branch) ** 2 for count in branch_dist.values()) / len(branch_dist)
            if variance < 100:  # Very uniform distribution
                console.print(f"⚠️  Suspiciously uniform distribution across {len(branch_dist)} branches", style="red")
                suspicious_count += 1
        
        if suspicious_count == 0:
            console.print("✅ No obvious suspicious patterns detected", style="green")
        
        # Show duplicate messages
        if results['analysis']['duplicate_messages']:
            console.print(f"\n📝 DUPLICATE MESSAGES ({len(results['analysis']['duplicate_messages'])} unique messages):", style="yellow")
            for msg, count in list(results['analysis']['duplicate_messages'].items())[:5]:  # Show first 5
                console.print(f"  • '{msg[:50]}...' (appears {count} times)", style="dim")
            if len(results['analysis']['duplicate_messages']) > 5:
                console.print(f"  ... and {len(results['analysis']['duplicate_messages']) - 5} more", style="dim")
        
        # Show branch distribution
        console.print(f"\n🌿 BRANCH DISTRIBUTION:", style="blue")
        for branch, count in sorted(branch_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
            console.print(f"  • {branch}: {count} commits", style="dim")


@click.command()
@click.option('--org', '-o', required=True, help='GitHub organization name')
@click.option('--repo', '-r', required=True, help='Repository name')
@click.option('--user', '-u', required=True, help='Username to investigate')
@click.option('--token', '-t', envvar='GITHUB_TOKEN', help='GitHub personal access token')
def main(org, repo, user, token):
    """Investigate suspicious commit patterns for a specific user."""
    if not token:
        console.print("❌ GitHub token is required. Set GITHUB_TOKEN environment variable or use --token option.", style="red")
        sys.exit(1)
    
    try:
        investigator = CommitInvestigator(token, org, repo)
        results = investigator.investigate_user_commits(user)
        investigator.display_investigation_results(user, results)
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main() 