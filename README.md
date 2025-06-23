# GitHub Commit Calculator

A powerful command-line tool to analyze commit history in a GitHub repository. It focuses on **unique contributions** to provide fair and accurate statistics, filtering out duplicate and merge commits by default.

## Features

-   **Unique Commit Analysis**: Counts only unique commits (based on message and code changes) to measure true contributions.
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

2.  **Configure your Repository:**
    -   Open `config.yaml` and set the `organization` and `repository` you want to analyze.
        ```yaml
        organization: your_org_name
        repository: your_repo_name
        ```

## How to Run

The tool is designed to be simple to use. By default, it will use the settings from your `config.yaml` and count only unique commits, excluding merges.

### **Basic Analysis**

To run a standard analysis on the repository defined in `config.yaml`:

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

### **Analyzing a Different Repository**

You can override the `config.yaml` settings using command-line options:

```bash
python3 commit_calculator.py --org another-org --repo another-repo
```