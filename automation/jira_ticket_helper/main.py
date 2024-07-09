import requests
from requests.auth import HTTPBasicAuth
import json

def get_jira_ticket_info(ticket_key):
    # Jira API endpoint
    base_url = "https://budsense.atlassian.net"
    api_endpoint = f"{base_url}/rest/api/2/issue/{ticket_key}"

    # Authentication
    email = "sheroze@mybudsense.com"  
    api_token = "" 

    # Make the API request
    auth = HTTPBasicAuth(email, api_token)
    headers = {"Accept": "application/json"}

    try:
        response = requests.get(api_endpoint, headers=headers, auth=auth)
        response.raise_for_status()  
        
        ticket_data = response.json()
        
        # Extract relevant information
        summary = ticket_data['fields']['summary']
        status = ticket_data['fields']['status']['name']
        assignee = ticket_data['fields']['assignee']['displayName'] if ticket_data['fields']['assignee'] else "Unassigned"
        description = ticket_data['fields']['description']

        # Print the information
        print(f"Ticket: {ticket_key}")
        print(f"Summary: {summary}")
        print(f"Status: {status}")
        print(f"Assignee: {assignee}")
        print(f"Description: {description}")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error occurred: {e}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while making the request: {e}")
    except KeyError as e:
        print(f"Error parsing the response: {e}")

# Example usage
ticket_key = input("Enter the Jira ticket key: ")
get_jira_ticket_info(ticket_key)
