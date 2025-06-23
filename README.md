# GitHub Commit Calculator

A powerful command-line tool to analyze commit history in GitHub repositories. It focuses on **unique contributions** to provide fair and accurate statistics, filtering out duplicate and merge commits by default.

## Features

-   **Unique Commit Analysis**: Counts only unique commits (based on message and code changes) to measure true contributions.
-   **Multi-Repository Support**: Analyze multiple repositories within the same organization in a single run.
-   **Time Range Analysis**: Define custom time periods for detailed sprint or milestone analysis.
-   **Detailed Statistics**: Provides a comprehensive breakdown of commits per user and per branch.
-   **Merge Commit Filtering**: Excludes merge commits by default for cleaner, more meaningful stats.
-   **Rich Console Output**: Displays results in clean, easy-to-read tables.
-   **Flexible Configuration**: Configure via `config.yaml`, `.env`, or command-line arguments.
-   **JSON Export**: Save the full analysis results to a JSON file.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/calculate_commit_github.git
    cd calculate_commit_github
    ```

2.  **Install dependencies:**
    ```bash
    pip3 install -r requirements.txt
    ```

## Configuration

1.  **Set up your GitHub Token:**
    -   Copy the example `.env` file:
        ```bash
        cp env_example.txt .env
        ```
    -   Open the `.env` file and add your [GitHub Personal Access Token](https://github.com/settings/tokens). The token needs `repo` scope for private repositories or `public_repo` for public ones.
        ```
        GITHUB_TOKEN=your_github_token_here
        ```

2.  **Configure your Repository(ies):**
    -   Open `config.yaml` and set the `organization` and `repositories` you want to analyze.
    -   For single repository analysis:
        ```yaml
        organization: your_org_name
        repositories:
          - your_repo_name
        ```
    -   For multi-repository analysis:
        ```yaml
        organization: your_org_name
        repositories:
          - repo1_name
          - repo2_name
          - repo3_name
        ```

3.  **Time Range Analysis (Optional):**
    -   To analyze specific periods, define `time_ranges` in `config.yaml`. The tool will run a separate analysis for each range across all repositories.
    -   If this section is empty or removed, the tool will analyze the entire commit history.
        ```yaml
        time_ranges:
          - name: "Sprint 1"
            start_date: "2025-03-17"
            end_date: "2025-05-03"
          - name: "Sprint 2"
            start_date: "2025-05-05"
            end_date: "2025-06-07"
        ```

## How to Run

The tool is designed to be simple to use. By default, it will use the settings from your `config.yaml` and count only unique commits, excluding merges.

If `time_ranges` are defined in `config.yaml`, the script will automatically run a separate analysis for each time period across all configured repositories.

### **Basic Analysis**

To run a standard analysis on the repository(ies) defined in `config.yaml`:

```bash
python3 commit_calculator.py
```

### **Detailed Branch Statistics**

To see a detailed breakdown of commits per branch for each user:

```bash
python3 commit_calculator.py --detailed
```

### **Including Merge Commits**

If you want to include merge commits in the analysis (not recommended for performance evaluation):

```bash
python3 commit_calculator.py --include-merge-commits
```

### **Saving Results to a File**

To save the complete analysis results to a JSON file:

```bash
python3 commit_calculator.py --output results.json
```

### **Analyzing Different Repository(ies)**

You can override the `config.yaml` settings using command-line options:

```bash
# Single repository
python3 commit_calculator.py --org another-org --repo another-repo

# Multiple repositories (comma-separated)
python3 commit_calculator.py --org another-org --repos repo1,repo2,repo3
```

## Output Format

The tool provides comprehensive output including:

- **Console Display**: Clean tables showing unique commit counts per user for each repository and time range
- **JSON Export**: Complete analysis data including:
  - Per-repository statistics
  - Per-time-range breakdowns
  - Detailed commit information
  - Branch-specific data
  - User contribution summaries

## Example Output

```
GitHub Commit Calculator - Multi-Repository Analysis
==================================================

Organization: your-org
Repositories: ['repo1', 'repo2', 'repo3']
Time Ranges: ['Sprint 1', 'Sprint 2']

Repository: repo1
Sprint 1 (2025-03-17 to 2025-05-03)
┌─────────────┬─────────────────┐
│ User        │ Unique Commits  │
├─────────────┼─────────────────┤
│ user1       │ 45              │
│ user2       │ 23              │
│ user3       │ 12              │
└─────────────┴─────────────────┘

Sprint 2 (2025-05-05 to 2025-06-07)
┌─────────────┬─────────────────┐
│ User        │ Unique Commits  │
├─────────────┼─────────────────┤
│ user1       │ 38              │
│ user2       │ 31              │
│ user3       │ 19              │
└─────────────┴─────────────────┘

[... continues for all repositories and time ranges ...]