# Auto PR Creator

## Overview

The Auto PR Creator is a Python script designed to automate the process of creating pull requests (PRs) on GitHub. It's particularly useful for development workflows where you want to streamline the PR creation process, especially when integrated into CI/CD pipelines.

## Location

- Folder: `auto_pr`
- Main Script: `main.py`

## Purpose

This script automates several steps in the pull request creation process:
1. Fetches the default branch name from the remote repository
2. Retrieves repository information
3. Gets the latest commit message from a specified branch
4. Creates a pull request using the GitHub API

## Usage

### As a standalone script

```bash
python main.py <ticket_name>
```

### As an imported function

```python
from auto_pr.main import create_auto_pr

pr_url = create_auto_pr("TICKET-123")
print(f"Pull request created: {pr_url}")
```

## Inputs

### Command-line Usage
- `ticket_name`: The name of the ticket/branch for which to create a PR.

### Function Usage
- `ticket_name` (str): The name of the ticket/branch for which to create a PR.
- `github_token` (str, optional): GitHub API token. If not provided, it will be read from environment variables.

## Outputs

- Returns the URL of the created pull request as a string.

## Side Effects

1. Creates a new pull request on GitHub.
2. Prints colored status messages to the console.

## Dependencies

- Python 3.x
- Required Python packages:
  - `requests`
  - `python-dotenv`

Install dependencies using:
```
pip install requests python-dotenv
```

## Environment Variables

- `GITHUB_TOKEN`: Your GitHub personal access token. Required if not provided as an argument to the function.

## Configuration

- The repository owner is currently hardcoded as "mobilefirstdev". Modify this in the `get_repo_info()` function if needed.

## Error Handling

- The script raises `ValueError` exceptions for various error conditions (e.g., failing to fetch branch information, commit messages, or create the PR).
- When used as a standalone script, error messages are printed to the console, and the script exits with a non-zero status code.
- When used as an imported function, exceptions are raised and should be handled by the calling code.

## Functions

1. `create_auto_pr(ticket_name, github_token=None)`: Main function to create an automatic pull request.
2. `get_default_branch()`: Fetches the default branch name from the remote.
3. `get_repo_info()`: Retrieves repository information.
4. `get_commit_message(ticket_name)`: Gets the latest commit message for the specified branch.
5. `create_pull_request(owner, repo, title, body, head, base, github_token)`: Creates the pull request using the GitHub API.

## Limitations

- The script assumes it's being run from within a Git repository.
- It requires proper Git configuration (remote URL set up correctly).
- The GitHub API token must have appropriate permissions to create pull requests in the repository.

## Example Integration

```python
from auto_pr.main import create_auto_pr

def my_pipeline():
    try:
        ticket_name = "FEATURE-789"
        pr_url = create_auto_pr(ticket_name)
        print(f"Pull request created successfully: {pr_url}")
        # Further processing with pr_url
    except ValueError as e:
        print(f"Failed to create pull request: {str(e)}")
        # Handle the error appropriately
```
