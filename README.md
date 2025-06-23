# calculate_commit_github
# Count only unique commits (recommended for fair evaluation)
python3 commit_calculator.py --unique-only

# Show detailed breakdown
python3 commit_calculator.py --unique-only --detailed

# Include merge commits in unique counting
python3 commit_calculator.py --unique-only --include-merge-commits

# Save results to JSON
python3 commit_calculator.py --unique-only --output unique_commits.json