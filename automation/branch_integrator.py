import sys
import subprocess
import os
import re

# ANSI color codes for colorful output
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
RESET = '\033[0m'

def print_step(step_num, message):
    """Print a step number and message in yellow."""
    print(f"\n{YELLOW}Step {step_num}: {message}{RESET}")

def print_success(message):
    """Print a success message in green."""
    print(f"{GREEN}{message}{RESET}")

def print_error(message):
    """Print an error message in red."""
    print(f"{RED}{message}{RESET}")

def print_info(message):
    """Print an info message in blue."""
    print(f"{BLUE}{message}{RESET}")

def print_warning(message):
    """Print a warning message in yellow."""
    print(f"{YELLOW}{message}{RESET}")

def run_command(command):
    """Run a shell command and return its output."""
    print_info(f"Executing command: {command}")
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    print_info("Command output:")
    print(result.stdout)
    if result.stderr:
        print_warning("Command stderr:")
        print(result.stderr)
    if result.returncode != 0:
        print_error(f"Error executing command: {command}")
        print_error(f"Error message: {result.stderr}")
        return None
    print_success(f"Command executed successfully")
    return result.stdout.strip()

def get_current_branch():
    """Get the name of the current Git branch."""
    return run_command("git rev-parse --abbrev-ref HEAD")

def get_parent_branch(current_branch):
    """Get the parent branch of the current branch."""
    parent = run_command(f"git config --get branch.{current_branch}.merge")
    if parent:
        return parent.replace("refs/heads/", "")
    return None

def print_parent_branch(current_branch):
    """Print the parent branch of the current branch."""
    parent = get_parent_branch(current_branch)
    if parent:
        print_info(f"Parent branch of {current_branch}: {parent}")
    else:
        print_warning(f"No parent branch found for {current_branch}")

def run_git_branch_processor():
    """Run the git_branch_processor/main.py script and extract the merge base hash."""
    print_step(1, "Running git_branch_processor/main.py")
    output = run_command("python3 shared-scripts/automation/git_branch_processor/main.py")
    if output is None:
        raise Exception("Failed to run git_branch_processor/main.py")
    
    print_parent_branch(get_current_branch())
    
    print_info("Extracting merge base hash from output")
    match = re.search(r"Merge base found: ([a-f0-9]+)", output)
    if match:
        merge_base = match.group(1)
        print_success(f"Merge base hash found: {merge_base}")
        return merge_base
    else:
        print_error("Failed to extract merge base hash from output")
        raise Exception("Merge base hash not found in output")

def run_branch_llm_handler(merge_base):
    """Run the branch_llm_handler/main.py script with the given merge base hash."""
    print_step(2, f"Running branch_llm_handler/main.py with merge base: {merge_base}")
    output = run_command(f"python shared-scripts/automation/branch_llm_handler/main.py {merge_base}")
    if output is None:
        raise Exception("Failed to run branch_llm_handler/main.py")
    
    print_parent_branch(get_current_branch())
    
    print_info("Extracting commit message from output")
    match = re.search(r'"response": "(.*)"', output)
    if match:
        commit_message = match.group(1)
        print_success(f"Commit message generated: {commit_message}")
        return commit_message
    else:
        print_error("Failed to extract commit message from output")
        raise Exception("Commit message not found in output")

def run_auto_pr(ticket_number, base_branch, commit_message):
    """Run the auto_pr/main.py script with the given parameters."""
    print_step(3, f"Running auto_pr/main.py")
    command = f"python shared-scripts/automation/auto_pr/main.py {ticket_number} {base_branch} \"{commit_message}\""
    output = run_command(command)
    if output is None:
        raise Exception("Failed to run auto_pr/main.py")
    
    print_parent_branch(get_current_branch())
    
    print_info("Extracting pull request URL from output")
    match = re.search(r"Pull request created: (https://.*)", output)
    if match:
        pr_url = match.group(1)
        print_success(f"Pull request created: {pr_url}")
        return pr_url
    else:
        print_error("Failed to extract pull request URL from output")
        raise Exception("Pull request URL not found in output")

def main():
    if len(sys.argv) != 2:
        print_error("Usage: python branch_integrator.py <prInto>")
        sys.exit(1)

    pr_into = sys.argv[1]
    print_info(f"Branch to open PR into: {pr_into}")

    try:
        current_branch = get_current_branch()
        print_info(f"Current branch: {current_branch}")

        merge_base = run_git_branch_processor()
        commit_message = run_branch_llm_handler(merge_base)
        pr_url = run_auto_pr(current_branch, pr_into, commit_message)

        print_success(f"Branch integration process completed successfully.")
        print_info(f"Pull request URL: {pr_url}")
    except Exception as e:
        print_error(f"An error occurred during the branch integration process: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()