
# Git Change Processor

## Purpose

This script automates the process of handling changes in a Git repository. It's designed to be used in a CI/CD pipeline or as part of a larger automation workflow. The script performs the following tasks:

1. Detects changes in the current Git repository
2. Creates a new branch with a given ticket name
3. Commits all changes to this new branch
4. Generates a CSV file with information about the changed files
5. Returns to the original branch

## Usage

### As a module in another Python script

```python
from git_change_processor.main import process_git_changes

ticket_name = "TICKET-123"
result = process_git_changes(ticket_name)

if result:
    print("Changes were processed successfully.")
    # Continue with your pipeline
else:
    print("No changes were made or an error occurred.")
    # Handle the case where no changes were made or an error occurred
```

### As a standalone script

```bash
python git_change_processor.main <ticketName>
```

## Inputs

- `ticket_name` (string): The name of the ticket or issue, used for naming the new branch.

## Outputs

- Returns `True` if changes were detected and processed successfully.
- Returns `False` if no changes were detected or if an error occurred during processing.

## Side Effects

1. Creates a new Git branch named after the provided ticket name.
2. Stages and commits all changes to this new branch.
3. Creates a CSV file named `autoCommitArtifact.csv` in the repository root, containing information about changed files.
4. Switches back to the original branch after processing.

## Requirements

- Python 3.6+
- Git command-line tool installed and accessible in the system PATH
- Script must be run from within a Git repository

## Notes

- The script will ignore binary files and files matching patterns in the `.gitignore` file.
- The CSV file is created in the original branch but is not committed.
- If the script fails at any point, it will attempt to return to the original branch.

## Error Handling

- The script uses colored output to distinguish between errors (red), warnings (yellow), and success messages (green).
- Any Git command failures or file processing errors will cause the script to return `False`.

## Customization

The script can be modified to change the CSV filename or adjust the commit message format. Refer to the script's comments for details on each function.
