import os
import requests
from requests.auth import HTTPBasicAuth
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_issue_details(issue_key, auth, headers):
    api_endpoint = f"https://budsense.atlassian.net/rest/api/3/issue/{issue_key}"
    response = requests.get(api_endpoint, headers=headers, auth=auth)
    response.raise_for_status()
    return response.json()

def format_issue_details(issue_data):
    description = issue_data['fields']['description']
    formatted_description = ""
    if description:
        if isinstance(description, dict) and 'content' in description:
            for content in description['content']:
                if content['type'] == 'paragraph':
                    for text in content['content']:
                        if text['type'] == 'text':
                            formatted_description += text['text'] + " "
        else:
            formatted_description = description
    
    return {
        "key": issue_data['key'],
        "title": issue_data['fields']['summary'],
        "status": issue_data['fields']['status']['name'],
        "description": formatted_description.strip() if formatted_description else "No description provided."
    }

def get_jira_issue_info(issue_key):
    base_url = "https://budsense.atlassian.net"
    api_endpoint = f"{base_url}/rest/api/3/issue/{issue_key}"

    # Get email and API token from environment variables
    email = os.getenv('JIRA_EMAIL')
    api_token = os.getenv('JIRA_API_TOKEN')

    if not email or not api_token:
        return {"error": "JIRA_EMAIL or JIRA_API_TOKEN not set in .env file"}

    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json"}

    try:
        main_issue = get_issue_details(issue_key, auth, headers)
        result = {
            "main_issue": format_issue_details(main_issue),
            "subtasks": [],
            "linked_issues": []
        }

        # Get subtasks
        for subtask in main_issue['fields'].get('subtasks', []):
            subtask_data = get_issue_details(subtask['key'], auth, headers)
            result["subtasks"].append(format_issue_details(subtask_data))

        # Get linked issues
        for link in main_issue['fields'].get('issuelinks', []):
            if 'outwardIssue' in link:
                linked_issue = get_issue_details(link['outwardIssue']['key'], auth, headers)
                result["linked_issues"].append({
                    "relationship": f"This issue {link['type']['outward']}",
                    "issue": format_issue_details(linked_issue)
                })
            elif 'inwardIssue' in link:
                linked_issue = get_issue_details(link['inwardIssue']['key'], auth, headers)
                result["linked_issues"].append({
                    "relationship": f"This issue {link['type']['inward']} by",
                    "issue": format_issue_details(linked_issue)
                })

        return result

    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP Error occurred: {str(e)}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred while making the request: {str(e)}"}
    except KeyError as e:
        return {"error": f"Error parsing the response: {str(e)}"}

# Example usage
if __name__ == "__main__":
    issue_key = input("Enter the Jira issue key: ")
    result = get_jira_issue_info(issue_key)
    print(json.dumps(result, indent=2))