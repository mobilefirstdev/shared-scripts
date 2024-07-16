# Git Change Processor

## Overview

Git Change Processor is a Python script that automates the process of managing changes in a Git repository. It creates a new branch, stages all changes, commits them, and generates a CSV file with details about the modified files. This tool is particularly useful for organizing changes related to specific tickets or issues.

## Features

- Detects changed files in the current Git branch
- Creates a new branch based on a provided ticket name
- Stages and commits all changes to the new branch
- Generates a CSV file with information about changed files
- Handles binary files and respects `.gitignore` rules
- Provides colorful console output for better readability

## Requirements

- Python 3.x
- Git (installed and configured)

## Installation

1. Clone this repository or download the `main.py` file.
2. Place the script in a folder named `git_change_processor`.

## Usage

Run the script from the command line with a ticket name as an argument:

```
python git_change_processor/main.py <ticketName>
```

Replace `<ticketName>` with your desired branch/ticket name.

## How It Works

1. The script first determines the Git repository's root directory.
2. It identifies all changed files (staged, unstaged, and untracked).
3. A new branch is created with the provided ticket name.
4. All changes are staged and committed to the new branch.
5. A CSV file named `autoCommitArtifact.csv` is generated in the repository root, containing information about the changed files.
6. The script switches back to the original branch.

## Output

- Console messages with color-coded information about the process.
- A CSV file (`autoCommitArtifact.csv`) in the repository root, containing:
  - File paths (absolute)
  - File status (modified, added, deleted, etc.)

## Functions

- `run_command(command)`: Executes a shell command and returns the result.
- `get_changed_files()`: Retrieves a list of changed files in the repository.
- `parse_git_status(status_output)`: Parses Git status output.
- `is_binary_file(file_path)`: Checks if a file is binary.
- `parse_gitignore(gitignore_path)`: Parses the `.gitignore` file.
- `should_ignore_file(file_path, repo_root)`: Determines if a file should be ignored based on `.gitignore` rules.
- `process_file(file_path, status, repo_root)`: Processes individual files, checking for binary content and ignore rules.
- `process_git_changes(ticket_name)`: Main function that orchestrates the entire process.

## Error Handling

The script includes error handling for various scenarios:
- Invalid Git commands
- File reading errors
- Branch creation issues
- Commit failures

Errors are displayed in red text in the console.

## Limitations

- The script assumes it's being run from within a Git repository.
- It does not handle merge conflicts or complex Git scenarios.
- The CSV file is created in the original branch and is not committed.

