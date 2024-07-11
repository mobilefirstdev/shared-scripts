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

def is_binary_file(file_path):
    """Check if a file is binary."""
    try:
        with open(file_path, 'tr') as check_file:
            check_file.read()
            return False
    except UnicodeDecodeError:
        return True

def should_ignore_file(file_path):
    """Check if the file should be ignored based on typical Python .gitignore rules."""
    ignore_patterns = [
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.Python',
        'build',
        'develop-eggs',
        'dist',
        'downloads',
        'eggs',
        '.eggs',
        'lib',
        'lib64',
        'parts',
        'sdist',
        'var',
        '*.egg-info',
        '.installed.cfg',
        '*.egg',
        '*.manifest',
        '*.spec',
        'pip-log.txt',
        'pip-delete-this-directory.txt',
        '.pytest_cache',
        '.coverage',
        '.DS_Store',
        '.vscode',
        '.idea',
        '*.log',
        '.env',
        'venv',
        'ENV',
    ]

    file_name = os.path.basename(file_path)
    dir_path = os.path.dirname(file_path)

    for pattern in ignore_patterns:
        if pattern.startswith('*'):
            if file_name.endswith(pattern[1:]):
                return True
        elif pattern in file_path:
            return True

    return False

def filter_csv_file(csv_path, repo_root):
    """Filter the CSV file to remove binary and ignored files."""
    temp_csv_path = csv_path + '.temp'
    filtered_count = 0

    with open(csv_path, 'r') as input_file, open(temp_csv_path, 'w', newline='') as output_file:
        reader = csv.reader(input_file)
        writer = csv.writer(output_file)

        # Write the header
        header = next(reader)
        writer.writerow(header)

        for row in reader:
            file_path = row[0]
            full_path = os.path.join(repo_root, file_path.split('/', 1)[1])  # Remove repo name from path
            
            if not should_ignore_file(file_path) and not is_binary_file(full_path):
                writer.writerow(row)
            else:
                filtered_count += 1
                print(f"Filtered out: {file_path}")

    # Replace the original CSV with the filtered one
    os.replace(temp_csv_path, csv_path)
    print(f"Filtered out {filtered_count} files from the CSV.")

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

        # Filter the CSV file
        print("\nFiltering CSV file...")
        filter_csv_file(csv_path, git_root)

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
    print("The CSV file has been filtered to remove binary and ignored files.")

if __name__ == "__main__":
    main()