# automation/auto_pr/main.py
import os
import subprocess
import requests
import json
from dotenv import load_dotenv

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

def run_command(command):
    """Run a shell command and return its output."""
    print_info(f"Running command: {command}")
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

def get_commit_message(ticket_name):
    """Get the commit message from the latest commit."""
    print_info(f"Fetching commit message for branch {ticket_name}...")
    result = run_command(f"git log -1 --pretty=%B {ticket_name}")
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
    print_info(f"Pushing branch {branch_name} to remote...")
    result = run_command(f"git push -u origin {branch_name}")
    if result is None:
        raise ValueError(f"Failed to push branch {branch_name} to remote.")
    print_success(f"Branch {branch_name} pushed to remote successfully.")

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
        # Push the branch to the remote repository
        push_branch(ticket_name)

        # Get the default branch name
        default_branch = get_default_branch()

        # Get repository information
        owner, repo = get_repo_info()

        # Get the commit message
        commit_message = get_commit_message(ticket_name)

        # # Create the pull request
        first_line = commit_message.split('\n')[0]
        pr_title = f"[{ticket_name}] {first_line}"  # Use first line of commit message as PR title
        pr_body = commit_message  # Use full commit message as PR description
        

        pr_url = create_pull_request(owner, repo, pr_title, pr_body, ticket_name, default_branch, github_token)

        print_success("Auto PR process completed successfully.")
        return pr_url
    except Exception as e:
        print_error(f"Error in create_auto_pr: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print_error("Usage: python auto_pr_script.py <ticketName>")
        sys.exit(1)
    
    ticket_name = sys.argv[1]
    try:
        pr_url = create_auto_pr(ticket_name)
        print(f"Pull request created: {pr_url}")
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)