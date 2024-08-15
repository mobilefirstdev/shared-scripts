import subprocess
import csv
import os

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

def run_git_command(command):
    print_warning(f"Executing Git command: {command}")
    try:
        output = subprocess.check_output(command, shell=True).decode('utf-8').strip()
        print_success(f"Command executed successfully")
        return output
    except subprocess.CalledProcessError as e:
        print_error(f"Error executing Git command: {e}")
        raise

def get_current_branch():
    print_warning("Determining current branch...")
    branch = run_git_command("git rev-parse --abbrev-ref HEAD")
    print_success(f"Current branch: {branch}")
    return branch

def get_parent_branch(current_branch):
    print_warning(f"Attempting to determine parent branch for '{current_branch}'...")
    try:
        # Try to get the explicitly configured parent branch
        parent = run_git_command(f"git config branch.{current_branch}.merge")
        if parent.startswith("refs/heads/"):
            parent = parent.replace("refs/heads/", "")
            print_success(f"Parent branch explicitly configured as: {parent}")
            return parent
    except subprocess.CalledProcessError:
        print_warning("No explicitly configured parent branch found")

    # If not explicitly configured, try to find the most likely parent
    try:
        print_warning("Searching for most likely parent branch...")
        branches = run_git_command("git branch -r --merged").split('\n')
        for branch in branches:
            branch = branch.strip()
            if branch and not branch.endswith(f"/{current_branch}"):
                parent = branch.split('/')[-1]
                print_success(f"Most likely parent branch found: {parent}")
                return parent
    except subprocess.CalledProcessError:
        print_warning("Could not determine parent from merged branches")

    # If all else fails, check for 'main', 'master', or 'dev'
    print_warning("Attempting to use 'main', 'master', or 'dev' as parent branch...")
    for default_branch in ['main', 'master', 'dev']:
        try:
            run_git_command(f"git rev-parse --verify {default_branch}")
            print_success(f"Using '{default_branch}' as parent branch")
            return default_branch
        except subprocess.CalledProcessError:
            print_warning(f"'{default_branch}' not found")

    print_error("Could not determine parent branch")
    raise Exception("Could not determine parent branch")

def get_merge_base(current_branch, parent_branch):
    print_warning(f"Finding merge base between '{current_branch}' and '{parent_branch}'...")
    merge_base = run_git_command(f"git merge-base {current_branch} {parent_branch}")
    print_success(f"Merge base found: {merge_base}")
    return merge_base

def get_changed_files(merge_base):
    print_warning(f"Retrieving changed files since merge base {merge_base}...")
    output = run_git_command(f"git diff --name-status {merge_base}")
    changed_files = []
    for line in output.split('\n'):
        if line:
            status, file_path = line.split('\t', 1)
            status_map = {'M': 'modified', 'A': 'added', 'D': 'deleted', 'R': 'renamed'}
            status = status_map.get(status[0], 'unknown')
            changed_files.append((file_path, status))
            print_warning(f"Found {status} file: {file_path}")
    print_success(f"Total changed files: {len(changed_files)}")
    return changed_files

def is_ignored(file_path):
    try:
        run_git_command(f"git check-ignore -q {file_path}")
        print_warning(f"File is ignored: {file_path}")
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    try:
        print_warning("Starting git branch processor...")
        git_root = run_git_command("git rev-parse --show-toplevel")
        print_success(f"Git root directory: {git_root}")
        os.chdir(git_root)

        current_branch = get_current_branch()
        parent_branch = get_parent_branch(current_branch)
        merge_base = get_merge_base(current_branch, parent_branch)
        changed_files = get_changed_files(merge_base)

        csv_filename = "autoCommitArtifact.csv"
        csv_path = os.path.join(git_root, csv_filename)
        
        print_warning(f"Creating {csv_filename}...")
        with open(csv_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["File Path", "Status"])
            
            files_written = 0
            for file, status in changed_files:
                if not is_ignored(file):
                    absolute_path = os.path.abspath(os.path.join(git_root, file))
                    csv_writer.writerow([absolute_path, status])
                    files_written += 1
                    print_warning(f"Added to CSV: {absolute_path} ({status})")
        
        print_success(f"{csv_filename} created successfully with {files_written} files.")

    except subprocess.CalledProcessError as e:
        print_error(f"Error executing Git command: {e}")
    except Exception as e:
        print_error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()