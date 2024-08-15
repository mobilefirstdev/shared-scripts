import sys
import subprocess
import os
import re
import json
import shutil

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

def run_git_branch_processor():
    """Run the git_branch_processor/main.py script and extract the merge base hash."""
    print_step(1, "Running git_branch_processor/main.py")
    output = run_command("python3 shared-scripts/automation/git_branch_processor/main.py")
    if output is None:
        raise Exception("Failed to run git_branch_processor/main.py")
    
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
    
    print_info("Reading commit message from TEMP/final_commit_message.txt")
    try:
        with open('TEMP/final_commit_message.txt', 'r') as file:
            content = file.read().strip()
        
        # Parse the JSON content
        message_obj = json.loads(content)
        commit_message = message_obj.get("response", "").strip()
        
        if commit_message:
            print_success(f"Commit message extracted successfully")
            return commit_message
        else:
            print_error("Failed to extract commit message from the file")
            raise Exception("Commit message not found in the file")
    except FileNotFoundError:
        print_error("Failed to find TEMP/final_commit_message.txt")
        raise Exception("Commit message file not found")
    except json.JSONDecodeError:
        print_error("Failed to parse JSON content in TEMP/final_commit_message.txt")
        raise Exception("Invalid JSON format in commit message file")
    except IOError:
        print_error("Failed to read TEMP/final_commit_message.txt")
        raise Exception("Error reading commit message file")

def run_auto_pr(ticket_number, base_branch, commit_message):
    """Run the auto_pr/main.py script with the given parameters."""
    print_step(3, f"Running auto_pr/main.py")
    escaped_commit_message = json.dumps(commit_message)  # This escapes special characters
    command = f"python shared-scripts/automation/auto_pr/main.py {ticket_number} {base_branch} {escaped_commit_message}"
    output = run_command(command)
    if output is None:
        raise Exception("Failed to run auto_pr/main.py")
    
    print_info("Extracting pull request URL from output")
    match = re.search(r"Pull request created: (https://.*)", output)
    if match:
        pr_url = match.group(1)
        print_success(f"Pull request created: {pr_url}")
        return pr_url
    else:
        print_error("Failed to extract pull request URL from output")
        raise Exception("Pull request URL not found in output")

def cleanup_artifacts():
    """Delete temporary artifacts generated during the integration process."""
    print_step(4, "Cleaning up artifacts")

    # Delete TEMP folder
    temp_folder = os.path.join(os.getcwd(), "TEMP")
    if os.path.exists(temp_folder):
        try:
            print_info(f"Attempting to delete TEMP folder: {temp_folder}")
            shutil.rmtree(temp_folder)
            print_success(f"Successfully deleted TEMP folder: {temp_folder}")
        except Exception as e:
            print_error(f"Failed to delete TEMP folder: {str(e)}")
    else:
        print_info(f"TEMP folder not found: {temp_folder}")

    # Delete autoCommitArtifact.csv
    csv_file = os.path.join(os.getcwd(), "autoCommitArtifact.csv")
    if os.path.exists(csv_file):
        try:
            print_info(f"Attempting to delete file: {csv_file}")
            os.remove(csv_file)
            print_success(f"Successfully deleted file: {csv_file}")
        except Exception as e:
            print_error(f"Failed to delete file {csv_file}: {str(e)}")
    else:
        print_info(f"CSV file not found: {csv_file}")

    print_success("Cleanup process completed.")

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
    finally:
        # Perform cleanup
        cleanup_artifacts()

if __name__ == "__main__":
    main()