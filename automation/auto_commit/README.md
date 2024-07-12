# Git Branch Management Script

## Overview

This Python script automates the process of creating a new Git branch for a specific ticket or feature while preserving a record of changed files. It's designed to streamline the workflow for developers working on multiple tickets or features in a single repository.

## Features

- Automatically creates a new branch based on a given ticket name
- Moves all current changes to the new branch
- Creates a CSV file in the original branch listing all changed files
- Maintains a clean state in the original branch

## How It Works

1. **Change Detection**: The script first checks if there are any changes in the current branch.

2. **Stashing Changes**: If changes are detected, all modifications (including untracked files) are staged and then stashed.

3. **New Branch Creation**: A new branch is created with the provided ticket name.

4. **Applying Changes**: The stashed changes are applied to the new branch and committed.

5. **CSV Creation**: The script switches back to the original branch and creates a CSV file (`autoCommitArtifact.csv`) listing all the files that were changed. This CSV is created using information from the stash but is not committed to the repository.

6. **Cleanup**: Finally, the stash is cleared to maintain a clean Git state.

## Why This Approach?

- **Isolation of Changes**: By moving all changes to a new branch, we ensure that the main (or current) branch remains clean and unaffected.
- **Record Keeping**: The CSV file provides a clear record of what files were modified for each ticket/feature.
- **Non-Intrusive**: The CSV file is created but not committed, allowing for flexibility in how this information is used or stored.

## Prerequisites

- Python 3.x
- Git installed and configured on your system

## How to Use

1. Place the `main.py` script in your Git repository.

2. Open a terminal and navigate to your repository.

3. Run the script with a ticket name as an argument:

   ```
   python3 path/to/main.py <ticketName>
   ```

   Replace `<ticketName>` with your actual ticket or feature name.

4. The script will create a new branch, move your changes to it, and create a CSV file in your current branch with the list of changed files.

## Example

```bash
$ python3 main.py TICKET-123
Current repository: my-awesome-project
Current branch: main
Changes detected in the current branch.
...
Script completed. You are now on branch 'main'.
A new branch 'TICKET-123' has been created with all changes.
The autoCommitArtifact.csv has been created in the 'main' branch but is not committed.
```

## Notes

- The script will exit if no changes are detected in the current branch.
- The `autoCommitArtifact.csv` file is created but not committed to the repository. You may want to add this file to your `.gitignore` if you don't want it tracked by Git.

## Troubleshooting

If you encounter any issues:
1. Ensure you have the necessary permissions to create branches and modify files in your repository.
2. Check that your Git configuration is correct and you can perform Git operations from the command line.
3. If the script fails, it will print error messages that can help identify the issue.

