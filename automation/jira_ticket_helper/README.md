# Jira Ticket Helper

This Python script fetches detailed information about a Jira issue, including its subtasks and linked issues, and saves the data in a JSON format.

## Features

- Retrieves main issue details (key, title, status, description)
- Fetches information about subtasks
- Gathers data on linked issues
- Outputs data in JSON format for easy parsing and integration with other tools
- Saves the JSON output to a file for later use
- Uses environment variables for secure credential management

## Requirements

- Python 3.6 or higher
- `requests` library
- `python-dotenv` library

## Installation

1. Clone this repository or download the script file.

2. Install the required Python libraries:

   ```
   pip install requests python-dotenv
   ```

3. Create a `.env` file in the same directory as the script with your Jira credentials:

   ```
   JIRA_EMAIL=your_email@example.com
   JIRA_API_TOKEN=your_jira_api_token
   ```

   Replace `your_email@example.com` with your Jira account email and `your_jira_api_token` with your Jira API token.

## Usage

1. Run the script:

   ```
   python jira_issue_info.py
   ```

2. When prompted, enter the Jira issue key (e.g., "PROJ-123").

3. The script will fetch the issue information and:
   - Print the JSON output to the console
   - Save the JSON output to a file named `jira_ticket_helper.json` in the same directory

## Output

The script generates a JSON object with the following structure:

```json
{
  "main_issue": {
    "key": "PROJ-123",
    "title": "Issue Title",
    "status": "In Progress",
    "description": "Issue description..."
  },
  "subtasks": [
    {
      "key": "PROJ-124",
      "title": "Subtask Title",
      "status": "To Do",
      "description": "Subtask description..."
    },
    ...
  ],
  "linked_issues": [
    {
      "relationship": "This issue blocks",
      "issue": {
        "key": "PROJ-125",
        "title": "Linked Issue Title",
        "status": "Open",
        "description": "Linked issue description..."
      }
    },
    ...
  ]
}
```

## Notes

- Ensure that your Jira API token has the necessary permissions to access the issues you're querying.
- The script is configured to work with Jira Cloud. If you're using Jira Server, you may need to modify the API endpoint URL.


## Troubleshooting

If you encounter any issues:

1. Verify that your `.env` file is correctly formatted and contains valid credentials.
2. Ensure you have the required Python libraries installed.
3. Check that you have the necessary permissions in Jira to access the issue and its related data.


For any other problems, please check the error message printed by the script for more information on what might be going wrong.