import sys
import subprocess
import os
import csv
import fnmatch

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
RESET = '\033[0m'

def print_error(message):
    """Print an error message in red."""
    print(f"{RED}{message}{RESET}")

def print_success(message):
    """Print a success message in green."""
    print(f"{GREEN}{message}{RESET}")

def run_command(command):
    """Run a shell command and return its output."""
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print_error(f"Error executing command: {command}")
        print_error(f"Error message: {result.stderr}")
        return None
    return result

def print_changes():
    """Print staged and unstaged changes."""
    print("Staged changes:")
    staged = run_command("git diff --cached --name-status")
    print(staged.stdout if staged and staged.stdout else "No staged changes.")

    print("\nUnstaged changes:")
    unstaged = run_command("git diff --name-status")
    print(unstaged.stdout if unstaged and unstaged.stdout else "No unstaged changes.")

    print("\nUntracked files:")
    untracked = run_command("git ls-files --others --exclude-standard")
    print(untracked.stdout if untracked and untracked.stdout else "No untracked files.")

def get_changed_files_from_stash():
    """Get a list of all changed files from the latest stash."""
    stash_files = run_command("git stash show --name-only")
    return stash_files.stdout.splitlines() if stash_files else []

def is_binary_file(file_path):
    """Check if a file is binary."""
    try:
        with open(file_path, 'tr') as check_file:
            check_file.read()
            return False
    except UnicodeDecodeError:
        return True
    except Exception as e:
        print_error(f"Error checking if file is binary: {file_path}")
        print_error(str(e))
        return True

def parse_gitignore(gitignore_path):
    """Parse .gitignore file and return a list of patterns."""
    if not os.path.exists(gitignore_path):
        return []
    
    with open(gitignore_path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def should_ignore_file(file_path, repo_root):
    """Check if the file should be ignored based on .gitignore rules."""
    gitignore_path = os.path.join(repo_root, '.gitignore')
    ignore_patterns = parse_gitignore(gitignore_path)
    
    # Always ignore .git directory
    ignore_patterns.append('.git/**')
    
    relative_path = os.path.relpath(file_path, repo_root)
    
    for pattern in ignore_patterns:
        if pattern.endswith('/'):
            # Directory pattern
            if fnmatch.fnmatch(relative_path, f"{pattern}*"):
                return True
        elif fnmatch.fnmatch(relative_path, pattern):
            return True
        elif '/' not in pattern and fnmatch.fnmatch(os.path.basename(relative_path), pattern):
            return True
    
    return False

def process_file(file_path, repo_name, repo_root):
    """Process a single file and return True if it should be included in the CSV."""
    try:
        full_path = os.path.join(repo_root, file_path)
        if should_ignore_file(full_path, repo_root):
            print_error(f"Ignoring file: {file_path}")
            return False
        if is_binary_file(full_path):
            print_error(f"Skipping binary file: {file_path}")
            return False
        return True
    except Exception as e:
        print_error(f"Error processing file {file_path}: {str(e)}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <ticketName>")
        sys.exit(1)

    ticket_name = sys.argv[1]

    # Get git root directory
    git_root = run_command("git rev-parse --show-toplevel")
    if not git_root:
        sys.exit(1)
    git_root = git_root.stdout.strip()
    os.chdir(git_root)

    # Get current repo name
    repo_name = os.path.basename(git_root)
    print(f"Current repository: {repo_name}")

    # Get current branch name
    current_branch = run_command("git rev-parse --abbrev-ref HEAD")
    if not current_branch:
        sys.exit(1)
    current_branch = current_branch.stdout.strip()
    print(f"Current branch: {current_branch}")

    # Check for changes
    changes = run_command("git status --porcelain")
    if changes and changes.stdout:
        print("Changes detected in the current branch.")
        print("Current state of the repository:")
        print_changes()
        
        # Stage all changes, including untracked files
        print("\nStaging all changes...")
        if not run_command("git add -A"):
            sys.exit(1)
        print_success("All changes have been staged.")
        
        # Stash changes
        print("\nStashing changes...")
        if not run_command("git stash push -m 'Temporary stash for branch creation'"):
            sys.exit(1)
        print_success("Changes stashed successfully.")
        
        # Create new branch and switch to it
        print(f"\nCreating new branch '{ticket_name}' from '{current_branch}'...")
        if not run_command(f"git checkout -b {ticket_name}"):
            sys.exit(1)
        print_success(f"Successfully created and checked out branch '{ticket_name}'.")

        # Apply stashed changes
        print("\nApplying stashed changes to the new branch...")
        if not run_command("git stash apply"):
            sys.exit(1)
        print_success("Stashed changes applied successfully.")

        # Commit changes in the new branch
        print("\nCommitting changes in the new branch...")
        if not run_command("git add -A") or not run_command(f"git commit -m 'Initial commit for {ticket_name}'"):
            sys.exit(1)
        print_success("Changes committed successfully.")

        # Switch back to the original branch
        print(f"\nSwitching back to '{current_branch}'...")
        if not run_command(f"git checkout {current_branch}"):
            sys.exit(1)

        # Create CSV file from stash
        csv_filename = "autoCommitArtifact.csv"
        csv_path = os.path.join(git_root, csv_filename)
        print(f"\nCreating {csv_filename} from stash...")
        changed_files = get_changed_files_from_stash()
        with open(csv_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["File Path"])  # Header
            for file in changed_files:
                if process_file(file, repo_name, git_root):
                    full_path = f"{repo_name}/{file}"
                    csv_writer.writerow([full_path])
        print_success(f"{csv_filename} created successfully.")

        # Clear the stash
        print("\nClearing the stash...")
        if not run_command("git stash drop"):
            sys.exit(1)
        print_success("Stash cleared successfully.")

    else:
        print("No changes detected in the current branch.")
        sys.exit(0)

    print("\nFinal state of the repository:")
    print_changes()

    print_success(f"\nScript completed. You are now on branch '{current_branch}'.")
    print_success(f"A new branch '{ticket_name}' has been created with all changes.")
    print_success(f"The {csv_filename} has been created in the '{current_branch}' branch but is not committed.")
    print_success("The CSV file contains only the files that were successfully processed.")

if __name__ == "__main__":
    main()