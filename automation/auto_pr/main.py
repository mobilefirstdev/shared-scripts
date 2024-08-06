import os
import subprocess
import requests
import json
from dotenv import load_dotenv
import sys
import re
# Add the parent directory of 'automation' to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from automation.jira_ticket_helper.main import get_jira_issue_info

# Load environment variables from .env file
load_dotenv()

# ANSI color codes
BLUE = '\033[0;34m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
RED = '\033[0;31m'
RESET = '\033[0m'

def print_info(message):
    print(f"{BLUE}{message}{RESET}")

def print_success(message):
    print(f"{GREEN}{message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}{message}{RESET}")

def print_error(message):
    print(f"{RED}{message}{RESET}")

def print_verbose(message):
    print(f"{BLUE}[VERBOSE] {message}{RESET}")

def run_command(command):
    """Run a shell command and return its output."""
    print_verbose(f"Running command: {command}")
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print_error(f"Error executing command: {command}")
        print_error(f"Error message: {result.stderr}")
        return None
    return result.stdout.strip()

def get_default_branch():
    """Fetch and return the default branch name from origin."""
    print_info("Fetching default branch name from origin...")
    result = run_command("git remote show origin | grep 'HEAD branch' | cut -d' ' -f5")
    if result is None:
        raise ValueError("Failed to fetch default branch name.")
    print_success(f"Default branch: {result}")
    return result

def get_repo_info():
    """Get the GitHub repository information."""
    print_info("Fetching repository information...")
    remote_url = run_command("git config --get remote.origin.url")
    if remote_url is None:
        raise ValueError("Failed to get remote URL.")
    
    # Extract repo from the URL
    parts = remote_url.split('/')
    repo = parts[-1].replace('.git', '')
    
    owner = "mobilefirstdev"
    
    print_success(f"Repository: {owner}/{repo}")
    return owner, repo

def get_commit_message(branch_name):
    """Get the commit message from the latest commit."""
    print_info(f"Fetching commit message for branch {branch_name}...")
    result = run_command(f"git log -1 --pretty=%B {branch_name}")
    if result is None:
        raise ValueError("Failed to fetch commit message.")
    print_success("Commit message fetched successfully.")
    return result

def create_pull_request(owner, repo, title, body, head, base, github_token):
    """Create a pull request using GitHub API."""
    print_info("Creating pull request...")
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "body": body,
        "head": head,
        "base": base
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 201:
        pr_data = response.json()
        print_success(f"Pull request created successfully. PR URL: {pr_data['html_url']}")
        return pr_data['html_url']
    else:
        raise ValueError(f"Failed to create pull request. Status code: {response.status_code}. Response: {response.text}")

def push_branch(branch_name):
    """Push the branch to the remote repository."""
    print_verbose(f"Pushing branch {branch_name} to remote...")
    result = run_command(f"git push -u origin {branch_name}")
    if result is None:
        raise ValueError(f"Failed to push branch {branch_name} to remote.")
    print_success(f"Branch {branch_name} pushed to remote successfully.")

def get_pr_title(ticket_name):
    """Generate PR title based on Jira ticket information."""
    print_info(f"Fetching Jira issue info for {ticket_name}...")
    issue_info = get_jira_issue_info(ticket_name)
    
    if 'error' in issue_info:
        print_error(f"Error fetching Jira issue info: {issue_info['error']}")
        return f"fix({ticket_name}): Update related to {ticket_name}"
    
    main_issue = issue_info.get('main_issue', {})
    issue_type = main_issue.get('type', '').lower()
    issue_title = main_issue.get('title', '')
    
    if issue_type in ['story', 'story subtask']:
        prefix = 'feat'
    elif issue_type == 'bug':
        prefix = 'fix'
    elif issue_type == 'tech debt':
        prefix = 'debt'
    elif issue_type == 'subtask':
        prefix = 'feat' 
    else:
        prefix = 'fix'
    
    return f"{prefix}({ticket_name}): {issue_title}"

def check_existing_pr(owner, repo, branch, github_token):
    """Check if a pull request already exists for the given branch."""
    print_verbose(f"Checking for existing PR for branch: {branch}")
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    params = {
        "head": f"{owner}:{branch}",
        "state": "open"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        prs = response.json()
        if prs:
            print_verbose(f"Found existing PR for branch {branch}")
            return True
    print_verbose(f"No existing PR found for branch {branch}")
    return False

def create_new_branch(base_branch):
    """Create a new branch with an incremented suffix."""
    print_verbose(f"Creating new branch based on: {base_branch}")
    parts = base_branch.split('-')
    if len(parts) > 1 and parts[-1].isdigit():
        # If the last part is a number, increment it
        new_number = int(parts[-1]) + 1
        new_branch = f"{'-'.join(parts[:-1])}-{new_number}"
    else:
        # If there's no number suffix, add -2
        new_branch = f"{base_branch}-2"
    
    print_verbose(f"New branch name: {new_branch}")
    run_command(f"git checkout -b {new_branch} {base_branch}")
    return new_branch

def create_auto_pr(ticket_name, github_token=None):
    """
    Main function to create an automatic pull request.
    
    Args:
        ticket_name (str): The name of the ticket/branch for which to create a PR.
        github_token (str, optional): GitHub API token. If not provided, it will be read from environment variables.
    
    Returns:
        str: The URL of the created pull request.
    
    Raises:
        ValueError: If any step in the process fails.
    """
    print_info(f"Starting auto PR process for ticket: {ticket_name}")

    if not github_token:
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("GitHub token not found. Please provide it as an argument or set the GITHUB_TOKEN environment variable.")

    try:
        owner, repo = get_repo_info()
        default_branch = get_default_branch()

        current_branch = ticket_name
        original_ticket = ticket_name
        pr_exists = check_existing_pr(owner, repo, current_branch, github_token)
        
        while pr_exists:
            print_warning(f"PR already exists for branch {current_branch}. Creating a new branch...")
            current_branch = create_new_branch(current_branch)
            pr_exists = check_existing_pr(owner, repo, current_branch, github_token)

        push_branch(current_branch)

        commit_message = get_commit_message(current_branch)
        pr_title = get_pr_title(original_ticket)
        
        # Prepend the PR title to the commit message
        pr_body = f"{pr_title}\n\n{commit_message}"

        pr_url = create_pull_request(owner, repo, pr_title, pr_body, current_branch, default_branch, github_token)

        print_success("Auto PR process completed successfully.")
        return pr_url
    except Exception as e:
        print_error(f"Error in create_auto_pr: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_error("Usage: python auto_pr_script.py <ticketName>")
        sys.exit(1)
    
    ticket_name = sys.argv[1]
    try:
        print("Starting the auto PR process...")
        pr_url = create_auto_pr(ticket_name)
        print(f"Pull request created: {pr_url}")
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)