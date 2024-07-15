from automation.auto_pr.main import create_auto_pr, print_error

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print_error("Usage: python auto_pr_script.py <ticketName>")
        sys.exit(1)
    
    ticket_name = sys.argv[1]
    try:
        pr_url = create_auto_pr(ticket_name)
        if pr_url:
            print(f"Pull request created: {pr_url}")
        else:
            print_error("Failed to create pull request.")
            sys.exit(1)
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
