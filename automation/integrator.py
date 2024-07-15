import sys
import os
import subprocess
from git_change_processor.main import process_git_changes
from llm_handler.main import generate_commit_message

# ANSI color codes for colorful output
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
RED = '\033[0;31m'
RESET = '\033[0m'

def print_step(step_num, message):
    print(f"\n{YELLOW}Step {step_num}: {message}{RESET}")

def print_success(message):
    print(f"{GREEN}{message}{RESET}")

def print_error(message):
    print(f"{RED}{message}{RESET}")

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

def main():
    print_step(1, "Initializing integrator script")
    if len(sys.argv) != 2:
        print_error("Error: Incorrect number of arguments")
        print("Usage: python integrator.py <ticketName>")
        sys.exit(1)

    ticket_name = sys.argv[1]
    print(f"Ticket name: {ticket_name}")

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
    commit_message = generate_commit_message(ticket_name, csv_file_path)

    if commit_message:
        print_success("Commit message generated successfully.")
        print("\nGenerated commit message:")
        print(f"{GREEN}{commit_message}{RESET}")
    else:
        print_error("Failed to generate commit message.")

    print_step(6, "Integration process complete")

if __name__ == "__main__":
    main()