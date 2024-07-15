import sys
import os
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

def find_csv_file():
    # Start from the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Go up to the parent directory of 'shared-scripts'
    while os.path.basename(current_dir) != 'shared-scripts':
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # We've reached the root directory
            return None
        current_dir = parent_dir
    
    # Go up one more level to the parent of 'shared-scripts'
    parent_of_shared_scripts = os.path.dirname(current_dir)
    
    # Look for the CSV file
    csv_file_path = os.path.join(parent_of_shared_scripts, 'autoCommitArtifact.csv')
    return csv_file_path if os.path.exists(csv_file_path) else None

def main():
    print_step(1, "Initializing integrator script")
    if len(sys.argv) != 2:
        print_error("Error: Incorrect number of arguments")
        print("Usage: python integrator.py <ticketName>")
        sys.exit(1)

    ticket_name = sys.argv[1]
    print(f"Ticket name: {ticket_name}")

    print_step(2, "Detecting changes in the repository")
    changes_detected = process_git_changes(ticket_name)

    if not changes_detected:
        print_error("No changes detected in the repository. Exiting.")
        sys.exit(0)

    print_success("Changes detected in the repository.")

    print_step(3, "Locating CSV file")
    csv_file_path = find_csv_file()
    
    if csv_file_path:
        print_success(f"CSV file found: {csv_file_path}")
    else:
        print_error("Error: CSV file 'autoCommitArtifact.csv' not found in the parent folder of shared-scripts")
        sys.exit(1)

    print_step(4, "Generating commit message")
    commit_message = generate_commit_message(ticket_name, csv_file_path)

    if commit_message:
        print_success("Commit message generated successfully.")
        print("\nGenerated commit message:")
        print(f"{GREEN}{commit_message}{RESET}")
    else:
        print_error("Failed to generate commit message.")

    print_step(5, "Integration process complete")

if __name__ == "__main__":
    main()