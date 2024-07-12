import sys
import subprocess
import os
import csv
import requests
import json

# ANSI color codes
RED = '\033[0;31m'
RESET = '\033[0m'

def print_error(message):
    """Print an error message in red."""
    print(f"{RED}{message}{RESET}")

def run_command(command):
    """Run a shell command and return its output."""
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print_error(f"Error executing command: {command}")
        print_error(f"Error message: {result.stderr}")
    return result

def get_file_content(file_path, branch):
    """Get the content of a file from a specific branch."""
    print(f"Attempting to retrieve content of file '{file_path}' from branch '{branch}'")
    try:
        git_path = file_path[len('shared-scripts/'):] if file_path.startswith('shared-scripts/') else file_path
        content = subprocess.check_output(['git', 'show', f'{branch}:{git_path}'], stderr=subprocess.PIPE)
        print(f"Successfully retrieved content from '{branch}'")
        return content
    except subprocess.CalledProcessError as e:
        print_error(f"File '{file_path}' does not exist in branch '{branch}' or error occurred: {e}")
        return None

def create_merged_file(original_content, new_content, output_file):
    """Create a merged file with original and new content."""
    print(f"Creating merged file: {output_file}")
    try:
        with open(output_file, 'wb') as f:
            if original_content is not None:
                f.write(b"===== ORIGINAL CONTENT =====\n\n")
                f.write(original_content)
                f.write(b"\n\n===== NEW CONTENT =====\n\n")
            if new_content is not None:
                f.write(new_content)
            else:
                f.write(b"File does not exist in the new branch.")
        print(f"Successfully created merged file: {output_file}")
        return output_file
    except IOError as e:
        print_error(f"Error creating merged file: {e}")
        return None

def get_commit_message(file_content, is_new_file, file_name):
    url = "https://budbot.mybudsense.com/chat?token=9d41ed1c-1b89-41e7-845a-21bd6cb29277"
    
    if is_new_file:
        system_prompt = f"You must generate a succinct commit message from the text you are provided. The commit message should include the file name '{file_name}' and describe what this new file does."
    else:
        system_prompt = f"You will be provided with text that contains the original and modified content of a file. Based on this, you must create a commit message. The commit message should include the file name '{file_name}' and describe the changes made to this file."

    payload = {
        "user_query": file_content,
        "system_prompt": system_prompt
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print_error(f"Error making POST request: {e}")
        return None

def combine_commit_messages(temp_folder):
    print("Combining individual commit messages...")
    combined_content = ""
    for filename in os.listdir(temp_folder):
        if filename.endswith("_llm.txt"):
            with open(os.path.join(temp_folder, filename), 'r') as f:
                combined_content += f.read() + "\n-------------\n"
    return combined_content.strip()

def get_final_commit_message(combined_content):
    url = "https://budbot.mybudsense.com/chat?token=9d41ed1c-1b89-41e7-845a-21bd6cb29277"
    
    system_prompt = "You will be given a list of commit messages. Your job is to combine them into a cohesive and easy to understand commit message and just return the commit message without any preamble or other text."

    payload = {
        "user_query": combined_content,
        "system_prompt": system_prompt
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print_error(f"Error making POST request: {e}")
        return None

def process_file(file_path, current_branch, ticket_number, temp_folder, index):
    try:
        print(f"\nProcessing file {index}: {file_path}")
        
        original_content = get_file_content(file_path, current_branch)
        new_content = get_file_content(file_path, ticket_number)
        
        if original_content is not None or new_content is not None:
            if original_content is None:
                file_prefix = 'new'
            elif new_content is None:
                file_prefix = 'deleted'
            else:
                file_prefix = 'modified'
            
            output_file = os.path.join(temp_folder, f'{file_prefix}_{index}.txt')
            merged_file = create_merged_file(original_content, new_content, output_file)
            
            if merged_file and file_prefix in ['new', 'modified']:
                with open(merged_file, 'r', encoding='utf-8') as f:
                    merged_content = f.read()
                
                commit_message = get_commit_message(merged_content, file_prefix == 'new', file_path)
                if commit_message:
                    commit_file = os.path.join(temp_folder, f'{file_prefix}_{index}_llm.txt')
                    with open(commit_file, 'w') as f:
                        f.write(commit_message)
                    print(f"Created commit message file: {commit_file}")
        else:
            print(f"Skipping file '{file_path}' as it doesn't exist in either branch.")
    
    except Exception as e:
        print_error(f"Error processing file {file_path}: {str(e)}")
        print("Skipping this file and continuing with the next one.")

def main(ticket_number):
    print(f"Starting script with ticket number: {ticket_number}")
    
    repo_root = run_command("git rev-parse --show-toplevel").stdout.strip()
    print(f"Git repository root: {repo_root}")
    
    csv_file_path = os.path.join(repo_root, 'autoCommitArtifact.csv')
    file_paths = []
    print(f"Reading CSV file: {csv_file_path}")
    try:
        with open(csv_file_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                file_paths.append(row['File Path'])
        print(f"Successfully read {len(file_paths)} file path(s) from the CSV.")
    except FileNotFoundError:
        print_error(f"Error: CSV file '{csv_file_path}' not found.")
        sys.exit(1)
    except csv.Error as e:
        print_error(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    current_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()
    print(f"Current git branch (base branch): {current_branch}")
    
    temp_folder = os.path.join(repo_root, 'TEMP')
    os.makedirs(temp_folder, exist_ok=True)
    print(f"Created TEMP folder at: {temp_folder}")
    
    for index, file_path in enumerate(file_paths, start=1):
        process_file(file_path, current_branch, ticket_number, temp_folder, index)
    
    combined_content = combine_commit_messages(temp_folder)
    
    final_commit_message = get_final_commit_message(combined_content)
    if final_commit_message:
        final_commit_file = os.path.join(temp_folder, 'final_commit_message.txt')
        with open(final_commit_file, 'w') as f:
            f.write(final_commit_message)
        print(f"Created final commit message file: {final_commit_file}")
    
    print("\nScript execution completed.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script_name.py <ticketNumber>")
        sys.exit(1)
    
    ticket_number = sys.argv[1]
    main(ticket_number)