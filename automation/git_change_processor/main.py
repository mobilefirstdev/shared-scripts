import sys
import subprocess
import os
import csv
import fnmatch

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
RESET = '\033[0m'

def print_error(message):
    print(f"{RED}{message}{RESET}")

def print_success(message):
    print(f"{GREEN}{message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}{message}{RESET}")

def run_command(command):
    print(f"Executing command: {command}")
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print_error(f"Error executing command: {command}")
        print_error(f"Error message: {result.stderr}")
        return None
    return result

def branch_exists(branch_name):
    result = run_command(f"git branch --list {branch_name}")
    return result is not None and branch_name in result.stdout

def generate_branch_name(base_name):
    if not branch_exists(base_name):
        return base_name
    
    count = 2
    while True:
        new_name = f"{base_name}-{count}"
        if not branch_exists(new_name):
            return new_name
        count += 1

def get_changed_files():
    print("Checking for changed files...")
    staged = run_command("git diff --cached --name-status")
    unstaged = run_command("git diff --name-status")
    untracked = run_command("git ls-files --others --exclude-standard")

    files = set()
    if staged:
        files.update(parse_git_status(staged.stdout))
    if unstaged:
        files.update(parse_git_status(unstaged.stdout))
    if untracked:
        files.update((file, '?') for file in untracked.stdout.splitlines())

    return list(files)

def parse_git_status(status_output):
    files = []
    for line in status_output.splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            status, file = parts
            files.append((file, status))
    return files

def is_binary_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            chunk = file.read(1024)
            return b'\0' in chunk
    except IOError:
        print_warning(f"Unable to read file: {file_path}")
        return False

def parse_gitignore(gitignore_path):
    if not os.path.exists(gitignore_path):
        return []
    with open(gitignore_path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def should_ignore_file(file_path, repo_root):
    gitignore_path = os.path.join(repo_root, '.gitignore')
    ignore_patterns = parse_gitignore(gitignore_path)
    ignore_patterns.append('.git/**')
    
    relative_path = os.path.relpath(file_path, repo_root)
    
    for pattern in ignore_patterns:
        if pattern.endswith('/'):
            if fnmatch.fnmatch(relative_path, f"{pattern}*"):
                return True
        elif fnmatch.fnmatch(relative_path, pattern):
            return True
        elif '/' not in pattern and fnmatch.fnmatch(os.path.basename(relative_path), pattern):
            return True
    return False

def process_file(file_path, status, repo_root):
    try:
        full_path = os.path.join(repo_root, file_path)
        if should_ignore_file(full_path, repo_root):
            print_warning(f"Ignoring file: {file_path}")
            return False
        if status != 'D' and is_binary_file(full_path):
            print_warning(f"Skipping binary file: {file_path}")
            return False
        print_success(f"Processing file: {file_path} (Status: {status})")
        return True
    except Exception as e:
        print_error(f"Error processing file {file_path}: {str(e)}")
        return False

def process_git_changes(ticket_name):
    git_root = run_command("git rev-parse --show-toplevel")
    if not git_root:
        return False
    git_root = git_root.stdout.strip()
    os.chdir(git_root)

    repo_name = os.path.basename(git_root)
    print(f"Current repository: {repo_name}")

    current_branch = run_command("git rev-parse --abbrev-ref HEAD")
    if not current_branch:
        return False
    current_branch = current_branch.stdout.strip()
    print(f"Current branch: {current_branch}")

    changed_files = get_changed_files()
    if not changed_files:
        print("No changes detected in the current branch.")
        return False

    print("Changes detected in the current branch.")
    
    print("\nStaging all changes...")
    if not run_command("git add -A"):
        return False
    print_success("All changes have been staged.")

    new_branch_name = generate_branch_name(ticket_name)
    print(f"\nCreating new branch '{new_branch_name}' from '{current_branch}'...")
    if not run_command(f"git checkout -b {new_branch_name}"):
        return False
    print_success(f"Successfully created and checked out branch '{new_branch_name}'.")

    print("\nCommitting changes in the new branch...")
    if not run_command(f"git commit -m 'Initial commit for {new_branch_name}'"):
        return False
    print_success("Changes committed successfully.")

    csv_filename = "autoCommitArtifact.csv"
    csv_path = os.path.join(git_root, csv_filename)
    print(f"\nCreating {csv_filename}...")
    with open(csv_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["File Path", "Status"])
        for file, status in changed_files:
            if process_file(file, status, git_root):
                absolute_path = os.path.abspath(os.path.join(git_root, file))
                csv_writer.writerow([absolute_path, status])
    print_success(f"{csv_filename} created successfully.")

    print(f"\nSwitching back to '{current_branch}'...")
    if not run_command(f"git checkout {current_branch}"):
        return False

    print_success(f"\nScript completed. You are now on branch '{current_branch}'.")
    print_success(f"A new branch '{new_branch_name}' has been created with all changes.")
    print_success(f"The {csv_filename} has been created in the '{current_branch}' branch but is not committed.")

    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <ticketName>")
        sys.exit(1)
    
    ticket_name = sys.argv[1]
    result = process_git_changes(ticket_name)
    sys.exit(0 if result else 1)