import subprocess
from datetime import datetime, timedelta
from collections import defaultdict
import sys
import argparse

def get_git_stats(directories, time_period):
    cmd = ["git", "log", "--all", "--format=%at", "--numstat", "--"] + directories
    output = subprocess.check_output(cmd).decode('utf-8')

    commits = []
    current_commit = None

    for line in output.split('\n'):
        if line.strip().isdigit():
            if current_commit:
                commits.append(current_commit)
            current_commit = {
                'timestamp': int(line.strip()),
                'added': 0,
                'modified': 0,
                'files': 0
            }
        elif line.strip() and current_commit:
            parts = line.split()
            if len(parts) >= 2:
                added, deleted = int(parts[0] if parts[0] != '-' else 0), int(parts[1] if parts[1] != '-' else 0)
                # New logic: added = actually new lines, modified = deleted/changed lines
                actual_added = max(0, added - deleted)
                modified = deleted
                
                current_commit['added'] += actual_added
                current_commit['modified'] = modified if 'modified' not in current_commit else current_commit['modified'] + modified
                current_commit['files'] += 1

    if current_commit:
        commits.append(current_commit)

    periods = defaultdict(lambda: {'added': 0, 'modified': 0, 'files': 0, 'commits': 0})
    for commit in commits:
        date = datetime.fromtimestamp(commit['timestamp'])
        if time_period == 'day':
            period_key = date.strftime('%Y-%m-%d')
        elif time_period == 'week':
            period_key = (date - timedelta(days=date.weekday())).strftime('%Y-%m-%d')
        else:  # month
            period_key = date.strftime('%Y-%m')
        
        periods[period_key]['added'] += commit['added']
        periods[period_key]['modified'] += commit['modified']
        periods[period_key]['files'] += commit['files']
        periods[period_key]['commits'] += 1

    return periods

def print_stats(periods, directories, time_period):
    print(f"Git statistics for directories: {', '.join(directories)}")
    print(f"Time period: {time_period}")
    
    if time_period == 'day':
        print("\n| Date       | Commits | Lines Added | Lines Modified | Files Changed |")
    elif time_period == 'week':
        print("\n| Week       | Commits | Lines Added | Lines Modified | Files Changed |")
    else:  # month
        print("\n| Month      | Commits | Lines Added | Lines Modified | Files Changed |")
    
    print("|------------|---------|-------------|----------------|---------------|")
    
    for period in sorted(periods.keys(), reverse=True):
        stats = periods[period]
        print(f"| {period} | {stats['commits']:7,d} | {stats['added']:11,d} | {stats['modified']:14,d} | {stats['files']:13,d} |")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Git statistics for specified directories.")
    parser.add_argument('directories', nargs='+', help='Directories to analyze')
    parser.add_argument('-p', '--period', choices=['day', 'week', 'month'], default='week',
                        help='Time period for grouping statistics (default: week)')
    
    args = parser.parse_args()

    periods = get_git_stats(args.directories, args.period)
    print_stats(periods, args.directories, args.period)