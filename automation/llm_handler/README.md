# Auto Commit Script

## Table of Contents
1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Usage](#usage)
5. [How It Works](#how-it-works)
6. [Output](#output)
7. [Troubleshooting](#troubleshooting)
8. [Contributing](#contributing)

## Introduction

The Auto Commit Script (`main.py`) is a Python tool designed to automate the process of generating commit messages for changes in a Git repository. It analyzes the differences between the current branch and a specified ticket branch, creates individual commit messages for each changed file, and then combines these into a comprehensive, final commit message.

This tool is useful for developers who want to maintain detailed, consistent commit messages across their project, especially when dealing with multiple file changes in a single commit.

## Prerequisites

Before you can use this script, ensure you have the following:

- Python 3.6 or higher installed on your system
- Git installed and configured on your machine
- Access to the repository you want to analyze
- A file named `autoCommitArtifact.csv` in the root of your repository, containing the paths of files to be analyzed

## Installation

1. Ensure that the script `main.py` is located in the `shared-scripts/automation/llm_handler/` directory of your repository.

2. Install the required Python package:
   ```
   pip install requests
   ```

3. Make sure you have the necessary permissions to execute the script and access the Git repository.

## Usage

To use the script, follow these steps:

1. Open a terminal or command prompt.

2. Navigate to the root of your Git repository (the `shared-scripts` directory).

3. Run the script with the following command:
   ```
   python3 automation/llm_handler/main.py <ticketNumber>
   ```
   Replace `<ticketNumber>` with the name of the branch containing your changes.

4. The script will process the files, generate commit messages, and create a final combined commit message.

## How It Works

1. The script reads the `autoCommitArtifact.csv` file to get the list of files to analyze.

2. For each file, it compares the content between the current branch and the specified ticket branch.

3. It categorizes each file as 'new', 'modified', or 'deleted'.

4. For new and modified files, it generates an individual commit message using an AI model.

5. All individual commit messages are combined.

6. A final, comprehensive commit message is generated based on all the individual messages.

7. The script saves all outputs in a `TEMP` folder within your repository.

## Output

The script generates the following outputs in the `TEMP` folder:

- `new_X.txt` or `modified_X.txt`: Content comparison for each file
- `new_X_llm.txt` or `modified_X_llm.txt`: Individual commit messages for each file
- `final_commit_message.txt`: The final, combined commit message

Where `X` is a number representing the order in which the files were processed.

## Troubleshooting

If you encounter any issues:

1. Ensure all prerequisites are correctly installed.
2. Check that the `autoCommitArtifact.csv` file exists in the root of your repository and is correctly formatted.
3. Verify that the `main.py` script is located in the `shared-scripts/automation/llm_handler/` directory.
4. Ensure you're running the script from the `shared-scripts` directory.
5. Verify that you have the necessary permissions to access the Git repository and create files.
6. Check your internet connection, as the script needs to make API calls.

If problems persist, please check the error messages in the console output for more information.
