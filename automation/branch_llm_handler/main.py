# branch_llm_handler/main.py
import sys
import subprocess
import os
import csv
import requests
import json

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
    if result.returncode != 0:
        print_error(f"Error executing command: {command}")
        print_error(f"Error message: {result.stderr}")
    else:
        print_success(f"Command executed successfully")
    return result

def get_file_content(file_path, ref):
    """Get the content of a file from a specific ref (branch or commit)."""
    print_info(f"Attempting to retrieve content of file '{file_path}' from ref '{ref}'")
    try:
        git_path = file_path[len('shared-scripts/'):] if file_path.startswith('shared-scripts/') else file_path
        content = subprocess.check_output(['git', 'show', f'{ref}:{git_path}'], stderr=subprocess.PIPE)
        print_success(f"Successfully retrieved content from '{ref}'")
        return content
    except subprocess.CalledProcessError as e:
        print_error(f"File '{file_path}' does not exist in ref '{ref}' or error occurred: {e}")
        return None

def create_merged_file(original_content, new_content, output_file):
    """Create a merged file with original and new content."""
    print_info(f"Creating merged file: {output_file}")
    try:
        with open(output_file, 'wb') as f:
            if original_content is not None:
                f.write(b"===== ORIGINAL CONTENT =====\n\n")
                f.write(original_content)
                f.write(b"\n\n===== NEW CONTENT =====\n\n")
            if new_content is not None:
                f.write(new_content)
            else:
                f.write(b"File does not exist in the current branch.")
        print_success(f"Successfully created merged file: {output_file}")
        return output_file
    except IOError as e:
        print_error(f"Error creating merged file: {e}")
        return None

def get_commit_message(file_content, is_new_file, file_name):
    url = "https://budbot.mybudsense.com/chat?token=9d41ed1c-1b89-41e7-845a-21bd6cb29277"
    
    if is_new_file:
        system_prompt = f"You must generate a succinct commit message from the text you are provided. The commit message should include the file name '{file_name}' and describe what this new file does."
    elif "===== ORIGINAL CONTENT =====" not in file_content:
        system_prompt = f"You must generate a succinct commit message for the deleted file '{file_name}'. The commit message should mention that the file has been deleted and briefly describe its purpose if possible."
    else:
        system_prompt = f"You will be provided with text that contains the original and modified content of a file. Based on this, you must create a commit message. The commit message should include the file name '{file_name}' and describe the changes made to this file."

    payload = {
        "user_query": file_content,
        "system_prompt": system_prompt
    }
    headers = {'Content-Type': 'application/json'}

    print_info(f"Sending request to AI service for commit message generation")
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        print_success("Successfully received commit message from AI service")
        return response.text
    except requests.RequestException as e:
        print_error(f"Error making POST request: {e}")
        return None

def combine_commit_messages(temp_folder):
    print_step(4, "Combining individual commit messages")
    combined_content = ""
    for filename in os.listdir(temp_folder):
        if filename.endswith("_llm.txt"):
            with open(os.path.join(temp_folder, filename), 'r') as f:
                combined_content += f.read() + "\n-------------\n"
    print_success("Successfully combined all commit messages")
    return combined_content.strip()

def get_final_commit_message(combined_content):
    url = "https://budbot.mybudsense.com/chat?token=9d41ed1c-1b89-41e7-845a-21bd6cb29277"
    
    system_prompt = "You will be given a list of commit messages. Your job is to combine them into a cohesive and easy to understand commit message and just return the commit message without any preamble or other text."

    payload = {
        "user_query": combined_content,
        "system_prompt": system_prompt
    }
    headers = {'Content-Type': 'application/json'}

    print_info("Sending request to AI service for final commit message generation")
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        print_success("Successfully received final commit message from AI service")
        return response.text
    except requests.RequestException as e:
        print_error(f"Error making POST request: {e}")
        return None

def process_file(file_path, commit_hash, temp_folder, index):
    print_step(3, f"Processing file {index}: {file_path}")
    try:
        # Convert to relative path if it's an absolute path
        repo_root = run_command("git rev-parse --show-toplevel").stdout.strip()
        relative_path = os.path.relpath(file_path, repo_root)
        
        original_content = get_file_content(relative_path, commit_hash)
        new_content = get_file_content(relative_path, 'HEAD')
        
        if original_content is not None or new_content is not None:
            if original_content is None:
                file_prefix = 'new'
                print_info(f"File '{relative_path}' is new")
            elif new_content is None:
                file_prefix = 'deleted'
                print_info(f"File '{relative_path}' has been deleted")
            else:
                file_prefix = 'modified'
                print_info(f"File '{relative_path}' has been modified")
            
            output_file = os.path.join(temp_folder, f'{file_prefix}_{index}.txt')
            merged_file = create_merged_file(original_content, new_content, output_file)
            
            if merged_file:
                with open(merged_file, 'r', encoding='utf-8') as f:
                    merged_content = f.read()
                
                commit_message = get_commit_message(merged_content, file_prefix == 'new', relative_path)
                if commit_message:
                    commit_file = os.path.join(temp_folder, f'{file_prefix}_{index}_llm.txt')
                    with open(commit_file, 'w') as f:
                        f.write(commit_message)
                    print_success(f"Created commit message file: {commit_file}")
        else:
            print_warning(f"Skipping file '{file_path}' as it doesn't exist in either the commit or the current branch.")
    
    except Exception as e:
        print_error(f"Error processing file {file_path}: {str(e)}")
        print_warning("Skipping this file and continuing with the next one.")

def generate_commit_message(commit_hash, csv_file_path=None):
    """
    Generate a commit message based on the changes between the current branch and a specific commit.
    
    Args:
    commit_hash (str): The commit hash to compare against.
    csv_file_path (str, optional): Path to the CSV file containing file paths. If not provided,
                                   it will look for 'autoCommitArtifact.csv' in the repo root.
    
    Returns:
    str: The generated commit message.
    """
    print_step(1, f"Starting commit message generation comparing current branch with commit: {commit_hash}")
    
    repo_root = run_command("git rev-parse --show-toplevel").stdout.strip()
    print_info(f"Git repository root: {repo_root}")
    
    if csv_file_path is None:
        csv_file_path = os.path.join(repo_root, 'autoCommitArtifact.csv')
    
    file_paths = []
    print_step(2, f"Reading CSV file: {csv_file_path}")
    try:
        with open(csv_file_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                file_paths.append(row['File Path'])
        print_success(f"Successfully read {len(file_paths)} file path(s) from the CSV.")
    except FileNotFoundError:
        print_error(f"Error: CSV file '{csv_file_path}' not found.")
        return None
    except csv.Error as e:
        print_error(f"Error reading CSV file: {e}")
        return None
    
    temp_folder = os.path.join(repo_root, 'TEMP')
    os.makedirs(temp_folder, exist_ok=True)
    print_info(f"Created TEMP folder at: {temp_folder}")
    
    for index, file_path in enumerate(file_paths, start=1):
        process_file(file_path, commit_hash, temp_folder, index)
    
    combined_content = combine_commit_messages(temp_folder)
    
    print_step(5, "Generating final commit message")
    final_commit_message = get_final_commit_message(combined_content)
    if final_commit_message:
        final_commit_file = os.path.join(temp_folder, 'final_commit_message.txt')
        with open(final_commit_file, 'w') as f:
            f.write(final_commit_message)
        print_success(f"Created final commit message file: {final_commit_file}")
    
    print_success("Commit message generation completed.")
    return final_commit_message

# Example usage:
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_error("Usage: python script_name.py <commit_hash>")
        sys.exit(1)
    
    commit_hash = sys.argv[1]
    commit_message = generate_commit_message(commit_hash)
    if commit_message:
        print_success("Generated commit message:")
        print_info(commit_message)
    else:
        print_error("Failed to generate commit message.")