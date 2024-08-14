# integrator.py
import sys
import os
import subprocess
import json
import shutil
from git_change_processor.main import process_git_changes
from llm_handler.main import generate_commit_message
from dotenv import load_dotenv
import shlex

# Load environment variables from .env file
load_dotenv()

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

def run_command(command, shell=True):
    """
    Execute a shell command and return the result.
    If the command fails, print an error message.
    """
    try:
        if isinstance(command, list):
            result = subprocess.run(command, capture_output=True, text=True, check=True)
        else:
            result = subprocess.run(shlex.split(command), capture_output=True, text=True, check=True)
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Error executing command: {command}")
        print_error(f"Return code: {e.returncode}")
        print_error(f"Error message: {e.stderr}")
        print_error(f"Output: {e.stdout}")
        return None

def find_repo_root():
    """
    Find the root directory of the git repository.
    Returns the path if successful, None otherwise.
    """
    result = run_command("git rev-parse --show-toplevel")
    return result.stdout.strip() if result.returncode == 0 else None

def find_csv_file(repo_root):
    """
    Look for the 'autoCommitArtifact.csv' file in the repository root.
    Returns the file path if found, None otherwise.
    """
    csv_file_path = os.path.join(repo_root, 'autoCommitArtifact.csv')
    return csv_file_path if os.path.exists(csv_file_path) else None

def parse_commit_message(json_message):
    """
    Parse the JSON-formatted commit message.
    Returns the 'response' field if successful, None otherwise.
    """
    try:
        message_obj = json.loads(json_message)
        return message_obj.get("response", "").strip().strip('"')
    except json.JSONDecodeError:
        print_error("Failed to parse commit message JSON")
        return None

def create_pull_request(ticket_name, base_branch):
    """
    Create a pull request using the auto_pr script.
    Returns True if successful, False otherwise.
    """
    print_step(7, "Creating pull request")
    auto_pr_script = os.path.join(os.path.dirname(__file__), 'auto_pr', 'main.py')

    if not os.path.exists(auto_pr_script):
        print_error(f"Error: auto_pr script not found at {auto_pr_script}")
        return False

    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print_error("GitHub token not found. Please set the GITHUB_TOKEN environment variable.")
        return False

    print_info(f"Running auto_pr script: {auto_pr_script}")
    result = run_command(f"python3 {auto_pr_script} {ticket_name} {base_branch}")

    if result.returncode == 0:
        print_success("Pull request created successfully")
        print(result.stdout)
        return True
    else:
        print_error("Failed to create pull request")
        print(f"Return code: {result.returncode}")
        print(f"Error output: {result.stderr}")
        print(f"Standard output: {result.stdout}")

        if "422" in result.stdout:
            print_warning("It seems the branch already exists on the remote. You may need to update the existing pull request or create a new one manually.")
        elif "404" in result.stdout:
            print_warning("The repository might not exist or you may not have the necessary permissions. Please check your GitHub access and repository settings.")

        return False

def rollback_changes(ticket_name, original_branch):
    """
    Rollback all changes made during the integration process and restore them to the original branch.
    """
    print_step("Rollback", "Rolling back changes due to error")

    # Check if the ticket branch exists
    branch_exists = run_command(f"git rev-parse --verify {ticket_name}")
    if branch_exists.returncode != 0:
        print_warning(f"Branch {ticket_name} does not exist. No rollback needed.")
        return

    # Switch to the ticket branch
    switch_result = run_command(f"git checkout {ticket_name}")
    if switch_result.returncode != 0:
        print_error(f"Failed to switch to branch {ticket_name}")
        return

    # Check if there's a commit on the ticket branch
    commit_exists = run_command(f"git rev-list -n 1 {ticket_name}")
    if commit_exists.returncode == 0 and commit_exists.stdout.strip():
        # If there's a commit, cherry-pick it to the original branch
        print_info("Commit found on ticket branch. Cherry-picking to original branch.")
        run_command(f"git checkout {original_branch}")
        cherry_pick_result = run_command(f"git cherry-pick {ticket_name}")
        if cherry_pick_result.returncode != 0:
            print_error("Failed to cherry-pick commit to original branch")
            print_warning("You may need to manually merge changes")
        else:
            print_success("Successfully cherry-picked commit to original branch")
    else:
        # If there's no commit, stash changes and apply to original branch
        print_info("No commit found on ticket branch. Stashing changes.")
        stash_result = run_command("git stash push -u")
        if stash_result.returncode != 0:
            print_error("Failed to stash changes")
            return

        # Switch back to the original branch
        switch_result = run_command(f"git checkout {original_branch}")
        if switch_result.returncode != 0:
            print_error(f"Failed to switch back to branch {original_branch}")
            return

        # Apply the stashed changes
        apply_result = run_command("git stash pop")
        if apply_result.returncode != 0:
            print_error("Failed to apply stashed changes")
            print_warning("You may need to manually resolve conflicts")
        else:
            print_success("Successfully restored changes to the original branch")

    # Delete the ticket branch
    delete_result = run_command(f"git branch -D {ticket_name}")
    if delete_result.returncode == 0:
        print_success(f"Successfully deleted the {ticket_name} branch")
    else:
        print_error(f"Failed to delete the {ticket_name} branch")

    print_warning("All changes have been rolled back and restored to the original branch.")

def get_current_branch():
    """
    Get the name of the current Git branch.
    """
    result = run_command("git rev-parse --abbrev-ref HEAD")
    return result.stdout.strip() if result.returncode == 0 else None

def switch_to_branch(branch_name):
    """
    Switch to the specified Git branch.
    """
    result = run_command(f"git checkout {branch_name}")
    return result.returncode == 0

def get_matching_branch_names(ticket_name):
    """
    Get all branch names that start with the given ticket name.
    This handles cases where multiple branches might exist for a single ticket.
    """
    result = run_command(f"git branch --list '{ticket_name}*'")
    if result and result.returncode == 0:
        branches = result.stdout.strip().split('\n')
        # Return all branch names that match, removing the leading '* ' if present
        return [branch.strip('* ') for branch in branches if branch.strip()]
    return []

def cleanup_artifacts(repo_root, ticket_name, original_branch, create_pr):
    """
    Delete temporary artifacts generated during the integration process.
    """
    print_step("Cleanup", "Removing temporary artifacts")

    # Delete TEMP folder
    temp_folder = os.path.join(repo_root, "TEMP")
    if os.path.exists(temp_folder):
        try:
            shutil.rmtree(temp_folder)
            print_success(f"Successfully deleted TEMP folder: {temp_folder}")
        except Exception as e:
            print_error(f"Failed to delete TEMP folder: {str(e)}")

    # Delete autoCommitArtifact.csv
    csv_file = os.path.join(repo_root, "autoCommitArtifact.csv")
    if os.path.exists(csv_file):
        try:
            os.remove(csv_file)
            print_success(f"Successfully deleted file: {csv_file}")
        except Exception as e:
            print_error(f"Failed to delete file {csv_file}: {str(e)}")

    # Switch back to the original branch
    switch_result = run_command(f"git checkout {original_branch}")
    if switch_result and switch_result.returncode == 0:
        print_success(f"Switched back to original branch: {original_branch}")
    else:
        print_error(f"Failed to switch to original branch: {original_branch}")

    # Delete ticket branches only if PR=true
    if create_pr:
        print_step("Branch Cleanup", "Removing ticket branches")
        matching_branches = get_matching_branch_names(ticket_name)
        if matching_branches:
            for branch in matching_branches:
                delete_branch_result = run_command(f"git branch -D {branch}")
                if delete_branch_result and delete_branch_result.returncode == 0:
                    print_success(f"Successfully deleted branch: {branch}")
                else:
                    print_error(f"Failed to delete branch: {branch}")
        else:
            print_error(f"Could not find any branches starting with: {ticket_name}")
    else:
        print_info("Skipping ticket branch deletion as PR creation was not requested.")

def update_commit_message(ticket_name, commit_message):
    """
    Update the commit message for the given ticket branch.
    """
    print_step(6, "Updating commit message")

    # Switch to the ticket branch
    switch_result = run_command(f"git checkout {ticket_name}")
    if switch_result is None:
        raise Exception(f"Failed to switch to branch {ticket_name}")

    # Amend the commit with the new message
    amend_command = ["git", "commit", "--amend", "-m", commit_message]
    amend_result = run_command(amend_command, shell=False)
    if amend_result is None:
        raise Exception("Failed to update commit message")

    print_success("Commit message updated successfully.")

def main():
    """
    Main function to orchestrate the integration process.
    """
    print_step(1, "Initializing integrator script")

    if len(sys.argv) < 2:
        print_error("Error: Incorrect number of arguments")
        print("Usage: python integrator.py <ticketName> [PR=true]")
        sys.exit(1)

    ticket_name = sys.argv[1]
    create_pr = any(arg.lower() == "pr=true" for arg in sys.argv[2:])
    print(f"Ticket name: {ticket_name}")
    print(f"Create PR: {'Yes' if create_pr else 'No'}")

    # Store the original branch
    original_branch = get_current_branch()
    if not original_branch:
        print_error("Failed to determine the current branch")
        sys.exit(1)
    print_info(f"Starting from branch: {original_branch}")

    try:
        # Find the repository root
        print_step(2, "Detecting repository root")
        repo_root = find_repo_root()
        if not repo_root:
            raise Exception("Unable to determine repository root")
        print_success(f"Repository root found: {repo_root}")

        # Detect changes in the repository
        print_step(3, "Detecting changes in the repository")
        os.chdir(repo_root)
        changes_detected = process_git_changes(ticket_name)

        if not changes_detected:
            raise Exception("No changes detected in the repository")

        print_success("Changes detected in the repository.")

        # Find the CSV file
        print_step(4, "Locating CSV file")
        csv_file_path = find_csv_file(repo_root)

        if not csv_file_path:
            raise Exception("CSV file 'autoCommitArtifact.csv' not found in the repository root")

        print_success(f"CSV file found: {csv_file_path}")

        # Generate commit message
        print_step(5, "Generating commit message")
        commit_message_json = generate_commit_message(ticket_name, csv_file_path)

        if not commit_message_json:
            raise Exception("Failed to generate commit message")

        commit_message = parse_commit_message(commit_message_json)
        if not commit_message:
            raise Exception("Failed to parse commit message")

        print_success("Commit message generated successfully.")
        print("\nGenerated commit message:")
        print(f"{GREEN}{commit_message}{RESET}")

        # Update the commit message
        update_commit_message(ticket_name, commit_message)

        # Create pull request if requested
        if create_pr:
            pr_created = create_pull_request(ticket_name, original_branch)
            if not pr_created:
                raise Exception("Pull request creation failed")

        print_step(8, "Integration process complete")

    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        rollback_changes(ticket_name, original_branch)
        sys.exit(1)

    finally:
        # Perform cleanup
        cleanup_artifacts(repo_root, ticket_name, original_branch, create_pr)
        
        # Check if we're on the original branch, if not, switch to it
        current_branch = get_current_branch()
        if current_branch != original_branch:
            print_step(9, f"Returning to original branch: {original_branch}")
            if switch_to_branch(original_branch):
                print_success(f"Successfully returned to branch: {original_branch}")
            else:
                print_error(f"Failed to return to branch: {original_branch}")

if __name__ == "__main__":
    main()