# LLM Handler

## Overview

The LLM Handler is a Python script designed to automate the process of generating commit messages for changes in a Git repository. It uses Large Language Models (LLMs) to analyze file changes and create meaningful commit messages. This tool is particularly useful for developers working with ticket-based workflows and wanting to streamline their commit message creation process.

## Features

- Processes multiple files associated with a ticket or branch
- Compares file content between the current branch and a specified ticket branch
- Generates individual commit messages for each changed file
- Combines individual messages into a cohesive final commit message
- Handles new, modified, and deleted files
- Supports CSV input for specifying files to process
- Uses color-coded console output for better readability

## Requirements

- Python 3.x
- Git
- Required Python packages:
  - `sys`
  - `subprocess`
  - `os`
  - `csv`
  - `requests`
  - `json`

## Installation

1. Clone the repository or download the `main.py` file.
2. Ensure you have Python 3.x installed on your system.
3. Install the required packages:

```
pip install requests
```

## Usage

Run the script from the command line, providing the ticket number as an argument:

```
python llm_handler/main.py <ticketNumber>
```

For example:

```
python llm_handler/main.py TICKET-123
```

## Configuration

- The script expects a CSV file named `autoCommitArtifact.csv` in the root of your Git repository. This file should contain the paths of the files to be processed.
- You can specify a different CSV file by modifying the `csv_file_path` variable in the `generate_commit_message` function.

## How It Works

1. The script reads file paths from the CSV file.
2. For each file, it retrieves the content from both the current branch and the ticket branch.
3. It creates a merged file containing both the original and new content.
4. The merged content is sent to an LLM API to generate a commit message for each file.
5. All individual commit messages are combined and sent to the LLM API again to create a final, cohesive commit message.
6. The final commit message is saved and displayed.

## Functions

- `print_error(message)`: Prints error messages in red.
- `run_command(command)`: Executes a shell command and returns its output.
- `get_file_content(file_path, branch)`: Retrieves file content from a specific branch.
- `create_merged_file(original_content, new_content, output_file)`: Creates a file with both original and new content.
- `get_commit_message(file_content, is_new_file, file_name)`: Generates a commit message for a single file using an LLM API.
- `combine_commit_messages(temp_folder)`: Combines individual commit messages into one.
- `get_final_commit_message(combined_content)`: Generates the final commit message using an LLM API.
- `process_file(file_path, current_branch, ticket_number, temp_folder, index)`: Processes a single file and generates its commit message.
- `generate_commit_message(ticket_number, csv_file_path=None)`: Main function that orchestrates the entire process.

## API Integration

The script uses an external API for generating commit messages. The API endpoint and token are hardcoded in the script. Ensure you have the necessary permissions to use this API.

## Output

The script generates several output files in a `TEMP` folder within your Git repository:

- Individual merged file contents (`new_X.txt`, `modified_X.txt`, `deleted_X.txt`)
- Individual commit messages (`new_X_llm.txt`, `modified_X_llm.txt`)
- Final commit message (`final_commit_message.txt`)

## Error Handling

The script includes error handling for common issues such as file not found, API request failures, and command execution errors. Error messages are displayed in red for better visibility.

## Limitations

- The script assumes a specific API endpoint for LLM-based commit message generation.
- It requires a pre-existing CSV file with file paths to process.
- The script does not handle merge conflicts or complex Git scenarios.
