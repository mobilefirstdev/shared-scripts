# Integrator Script (integrator.py)

## Overview

The Integrator Script is a powerful tool designed to automate and streamline the process of integrating changes, generating commit messages, and optionally creating pull requests in a Git repository. This script is particularly useful for teams looking to maintain consistent commit practices and streamline their workflow.

## Features

- Detects changes in the repository
- Generates meaningful commit messages based on changes
- Creates a new branch for the changes
- Updates commit messages with AI-generated content
- Optionally creates a pull request
- Provides rollback functionality in case of errors
- Cleans up temporary artifacts after execution

## Prerequisites

Before using the Integrator Script, ensure you have the following:

- Python 3.x installed
- Git installed and configured
- Required Python packages (install using `pip install -r requirements.txt`):
  - dotenv
  - (other dependencies used by imported modules)

## Setup

1. Clone the repository containing the Integrator Script.
2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Create a `.env` file in the same directory as the script.
   - Add your GitHub token: `GITHUB_TOKEN=your_github_token_here`

## Usage

Run the script from the command line with the following syntax:

```
python integrator.py <ticketName> [PR=true]
```

- `<ticketName>`: The name or ID of the ticket/issue you're working on. This will be used for branch naming and in the commit message.
- `[PR=true]`: (Optional) Include this flag to automatically create a pull request after committing changes.

## Process Flow

1. **Initialization**: The script starts by validating inputs and identifying the current Git branch.
2. **Repository Detection**: Locates the root of the Git repository.
3. **Change Detection**: Uses `git_change_processor` to detect changes in the repository.
4. **CSV File Locating**: Looks for a file named `autoCommitArtifact.csv` in the repository root.
5. **Commit Message Generation**: Utilizes `llm_handler` to generate a commit message based on the changes.
6. **Branch Creation and Commit**: Creates a new branch named after the ticket and commits changes with the generated message.
7. **Pull Request Creation**: (Optional) Creates a pull request using the `auto_pr` script.
8. **Cleanup**: Removes temporary files and artifacts created during the process.

## Error Handling

If an error occurs during execution, the script will:
1. Print detailed error information.
2. Attempt to roll back changes to the original state.
3. Return to the original branch.

## Components

- `git_change_processor`: Module for detecting and processing Git changes.
- `llm_handler`: Module for generating commit messages (likely using an AI/ML model).
- `auto_pr`: Script for creating pull requests (located in the `auto_pr` directory).

## Customization

You can modify the script to fit your specific workflow:
- Adjust the commit message generation logic in the `llm_handler` module.
- Modify the `auto_pr` script to change how pull requests are created.
- Add additional steps or checks to the main process flow as needed.

## Troubleshooting

- If you encounter permission issues, ensure your GitHub token has the necessary permissions.
- For "branch already exists" errors, you may need to manually update or delete the existing branch.
- If the script fails to detect changes, make sure you have uncommitted changes in your repository.

