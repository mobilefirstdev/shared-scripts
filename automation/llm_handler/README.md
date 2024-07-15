# LLM Commit Message Generator

## Overview

This script, located in `llm_handler/main.py`, is designed to automatically generate meaningful commit messages for changes in a Git repository. It uses an AI-powered service to analyze file changes and create descriptive commit messages.

## Purpose

The main purpose of this script is to:
1. Analyze changes between two Git branches (typically a feature branch and the main branch).
2. Generate individual commit messages for each changed file.
3. Combine these messages into a comprehensive, coherent commit message for the entire change set.

This tool is particularly useful in CI/CD pipelines or for developers who want to automate the process of writing detailed commit messages.

## Inputs

The script primarily requires one input:

1. `ticket_number` (string): This is typically a branch name or ticket identifier that contains the changes to be analyzed.

Optional input:
2. `csv_file_path` (string): Path to a CSV file containing the list of changed files. If not provided, the script will look for a file named `autoCommitArtifact.csv` in the root of the Git repository.

## Outputs

The script returns a string containing the generated commit message.

Additionally, it creates several files in a `TEMP` directory within the Git repository:
- Individual merged content files for each changed file.
- Individual commit message files for each changed file.
- A final commit message file (`final_commit_message.txt`).

## Side Effects

1. Creates a `TEMP` directory in the Git repository root.
2. Writes temporary files to the `TEMP` directory.
3. Makes HTTP requests to an external AI service for generating commit messages.

## Usage

### As a module in a pipeline

```python
from llm_handler.main import generate_commit_message

ticket_number = "TICKET-123"
commit_message = generate_commit_message(ticket_number)

if commit_message:
    print("Generated commit message:")
    print(commit_message)
else:
    print("Failed to generate commit message.")
```

### As a standalone script

```bash
python llm_handler/main.py TICKET-123
```

## Dependencies

- Python 3.x
- `requests` library
- Git (must be installed and accessible in the system path)



## Error Handling

- The script will print error messages in red to the console.
- If critical errors occur, the `generate_commit_message` function will return `None`.

## Limitations

- Requires access to the specified AI service.
- Assumes the Git repository is in a clean state.
- Large repositories or extensive changes may increase processing time.

