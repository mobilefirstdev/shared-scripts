# Auto PR Script

## Description

Auto PR Script is a Python utility designed to automate the process of creating pull requests (PRs) on GitHub. It streamlines the workflow by pushing your current branch, fetching repository information, and creating a pull request with a single command.

## Features

- Automatically pushes the current branch to the remote repository
- Fetches the default branch name from the remote
- Retrieves repository information (owner and repo name)
- Creates a pull request using the GitHub API
- Uses the latest commit message as the PR description
- Supports colored console output for better readability
- Handles errors gracefully with informative messages

## Prerequisites

- Python 3.6+
- Git installed and configured
- GitHub account with access to the repository
- GitHub Personal Access Token with repo scope

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/auto-pr.git
   cd auto-pr
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your GitHub Personal Access Token:
   - Create a `.env` file in the project root
   - Add your GitHub token: `GITHUB_TOKEN=your_github_token_here`

## Usage

Run the script from the command line, providing the ticket name (which should match your branch name) as an argument:

```
python main.py <ticketName>
```

For example:
```
python main.py feature-123
```

This will:
1. Push the `feature-123` branch to the remote repository
2. Fetch the default branch name (e.g., `main` or `master`)
3. Get the repository information
4. Use the latest commit message as the PR description
5. Create a pull request from `feature-123` to the default branch

## Configuration

The script uses environment variables for configuration. You can set these in your `.env` file:

- `GITHUB_TOKEN`: Your GitHub Personal Access Token (required)

## Error Handling

The script includes comprehensive error handling:
- It will display colored error messages for various failure scenarios
- If any step fails, the script will exit with a non-zero status code and display an error message


## Troubleshooting

If you encounter any issues:
1. Ensure your GitHub token has the necessary permissions
2. Check that your local Git repository is properly configured with a remote
3. Verify that you're in the correct directory when running the script
4. Make sure your branch name matches the ticket name you're providing as an argument

