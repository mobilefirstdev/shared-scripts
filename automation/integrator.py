import sys
import os
import subprocess
import json
from git_change_processor.main import process_git_changes
from llm_handler.main import generate_commit_message
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ANSI color codes for colorful output
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
RESET = '\033[0m'

def print_step(step_num, message):
    print(f"\n{YELLOW}Step {step_num}: {message}{RESET}")

def print_success(message):
    print(f"{GREEN}{message}{RESET}")

def print_error(message):
    print(f"{RED}{message}{RESET}")

def print_info(message):
    print(f"{BLUE}{message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}{message}{RESET}")

def run_command(command):
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print_error(f"Error executing command: {command}")
        print_error(f"Error message: {result.stderr}")
    return result

def find_repo_root():
    result = run_command("git rev-parse --show-toplevel")
    return result.stdout.strip() if result.returncode == 0 else None

def find_csv_file(repo_root):
    csv_file_path = os.path.join(repo_root, 'autoCommitArtifact.csv')
    return csv_file_path if os.path.exists(csv_file_path) else None

def parse_commit_message(json_message):
    try:
        message_obj = json.loads(json_message)
        return message_obj.get("response", "").strip().strip('"')
    except json.JSONDecodeError:
        print_error("Failed to parse commit message JSON")
        return None

def create_pull_request(ticket_name):
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
    result = run_command(f"python {auto_pr_script} {ticket_name}")
    
    if result.returncode == 0:
        print_success("Pull request created successfully")
        print(result.stdout)
        return True
    else:
        print_error("Failed to create pull request")
        print(f"Return code: {result.returncode}")
        print(f"Error output: {result.stderr}")
        print(f"Standard output: {result.stdout}")
        return False

def main():
    print_step(1, "Initializing integrator script")
    if len(sys.argv) < 2:
        print_error("Error: Incorrect number of arguments")
        print("Usage: python integrator.py <ticketName> [PR=true]")
        sys.exit(1)

    ticket_name = sys.argv[1]
    create_pr = any(arg.lower() == "pr=true" for arg in sys.argv[2:])
    print(f"Ticket name: {ticket_name}")
    print(f"Create PR: {'Yes' if create_pr else 'No'}")

    print_step(2, "Detecting repository root")
    repo_root = find_repo_root()
    if not repo_root:
        print_error("Error: Unable to determine repository root")
        sys.exit(1)
    print_success(f"Repository root found: {repo_root}")

    print_step(3, "Detecting changes in the repository")
    os.chdir(repo_root)  # Change to repo root before processing changes
    changes_detected = process_git_changes(ticket_name)

    if not changes_detected:
        print_error("No changes detected in the repository. Exiting.")
        sys.exit(0)

    print_success("Changes detected in the repository.")

    print_step(4, "Locating CSV file")
    csv_file_path = find_csv_file(repo_root)
    
    if csv_file_path:
        print_success(f"CSV file found: {csv_file_path}")
    else:
        print_error("Error: CSV file 'autoCommitArtifact.csv' not found in the repository root")
        sys.exit(1)

    print_step(5, "Generating commit message")
    commit_message_json = generate_commit_message(ticket_name, csv_file_path)

    if commit_message_json:
        commit_message = parse_commit_message(commit_message_json)
        if commit_message:
            print_success("Commit message generated successfully.")
            print("\nGenerated commit message:")
            print(f"{GREEN}{commit_message}{RESET}")
            
            print_step(6, "Updating commit message")
            
            # Switch to the ticket branch
            switch_result = run_command(f"git checkout {ticket_name}")
            if switch_result.returncode != 0:
                print_error(f"Failed to switch to branch {ticket_name}")
                sys.exit(1)
            
            # Amend the commit with the new message
            amend_result = run_command(f'git commit --amend -m "{commit_message}"')
            if amend_result.returncode == 0:
                print_success("Commit message updated successfully.")
            else:
                print_error("Failed to update commit message.")
                sys.exit(1)
            
            if create_pr:
                pr_created = create_pull_request(ticket_name)
                if not pr_created:
                    print_warning("Pull request creation failed, but other steps completed successfully.")
        else:
            print_error("Failed to parse commit message.")
    else:
        print_error("Failed to generate commit message.")

    print_step(8, "Integration process complete")

if __name__ == "__main__":
    main()