# auto_commit/main.py

import sys
import subprocess
import os
import csv

def run_command(command):
    """Run a shell command and return its output."""
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"Error executing command: {command}")
        print(f"Error message: {result.stderr}")
        sys.exit(1)
    return result

def print_changes():
    """Print staged and unstaged changes."""
    print("Staged changes:")
    staged = run_command("git diff --cached --name-status")
    print(staged.stdout if staged.stdout else "No staged changes.")

    print("\nUnstaged changes:")
    unstaged = run_command("git diff --name-status")
    print(unstaged.stdout if unstaged.stdout else "No unstaged changes.")

    print("\nUntracked files:")
    untracked = run_command("git ls-files --others --exclude-standard")
    print(untracked.stdout if untracked.stdout else "No untracked files.")

def get_changed_files_from_stash():
    """Get a list of all changed files from the latest stash."""
    stash_files = run_command("git stash show --name-only").stdout.splitlines()
    return stash_files

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <ticketName>")
        sys.exit(1)

    ticket_name = sys.argv[1]

    # Get git root directory
    git_root = run_command("git rev-parse --show-toplevel").stdout.strip()
    os.chdir(git_root)

    # Get current repo name
    repo_name = os.path.basename(git_root)
    print(f"Current repository: {repo_name}")

    # Get current branch name
    current_branch = run_command("git rev-parse --abbrev-ref HEAD")
    current_branch = current_branch.stdout.strip()
    print(f"Current branch: {current_branch}")

    # Check for changes
    changes = run_command("git status --porcelain")
    if changes.stdout:
        print("Changes detected in the current branch.")
        print("Current state of the repository:")
        print_changes()
        
        # Stage all changes, including untracked files
        print("\nStaging all changes...")
        run_command("git add -A")
        print("All changes have been staged.")
        
        # Stash changes
        print("\nStashing changes...")
        run_command("git stash push -m 'Temporary stash for branch creation'")
        print("Changes stashed successfully.")
        
        # Create new branch and switch to it
        print(f"\nCreating new branch '{ticket_name}' from '{current_branch}'...")
        run_command(f"git checkout -b {ticket_name}")
        print(f"Successfully created and checked out branch '{ticket_name}'.")

        # Apply stashed changes
        print("\nApplying stashed changes to the new branch...")
        run_command("git stash apply")
        print("Stashed changes applied successfully.")

        # Commit changes in the new branch
        print("\nCommitting changes in the new branch...")
        run_command("git add -A")
        run_command(f"git commit -m 'Initial commit for {ticket_name}'")
        print("Changes committed successfully.")

        # Switch back to the original branch
        print(f"\nSwitching back to '{current_branch}'...")
        run_command(f"git checkout {current_branch}")

        # Create CSV file from stash
        csv_filename = "autoCommitArtifact.csv"
        csv_path = os.path.join(git_root, csv_filename)
        print(f"\nCreating {csv_filename} from stash...")
        changed_files = get_changed_files_from_stash()
        with open(csv_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["File Path"])  # Header
            for file in changed_files:
                full_path = f"{repo_name}/{file}"
                csv_writer.writerow([full_path])
        print(f"{csv_filename} created successfully.")

        # Clear the stash
        print("\nClearing the stash...")
        run_command("git stash drop")
        print("Stash cleared successfully.")

    else:
        print("No changes detected in the current branch.")
        sys.exit(0)

    print("\nFinal state of the repository:")
    print_changes()

    print(f"\nScript completed. You are now on branch '{current_branch}'.")
    print(f"A new branch '{ticket_name}' has been created with all changes.")
    print(f"The {csv_filename} has been created in the '{current_branch}' branch but is not committed.")

if __name__ == "__main__":
    main()