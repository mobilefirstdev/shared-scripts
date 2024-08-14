#!/bin/bash

# Function to update submodules in the first layer of directories
update_submodules() {
    # Loop through all directories in the current directory
    for dir in */; do
        # Check if it's a directory
        if [ -d "$dir" ]; then
            # Enter the directory
            cd "$dir"

            # Check if it's a git repository
            if [ -d ".git" ]; then
                echo "Updating repository and submodule in $dir"

                # Pull the latest changes in the main repository
                if git pull; then
                    echo "Successfully pulled latest changes in $dir"
                else
                    echo "Failed to pull latest changes in $dir"
                    cd ..
                    continue
                fi

                # Navigate to the submodule directory
                if [ -d "shared-scripts" ]; then
                    cd shared-scripts

                    # Pull the latest changes from the dev branch of the submodule
                    if git pull origin dev; then
                        echo "Successfully pulled latest changes in shared-scripts"
                    else
                        echo "Failed to pull latest changes in shared-scripts"
                        cd ..
                        continue
                    fi

                    # Return to the main directory
                    cd ..

                    # Add the updated submodule to the commit
                    git add shared-scripts
                    git commit -m "Update submodule to latest commit"

                    # Push the changes to the remote repository
                    if git push; then
                        echo "Successfully pushed updates to the repository"
                    else
                        echo "Failed to push updates to the repository"
                    fi
                else
                    echo "shared-scripts directory not found in $dir"
                fi

            else
                echo "$dir is not a git repository."
            fi

            # Return to the original directory
            cd ..
        fi
    done
}

# Check if the current directory is a git repository
if [ -d ".git" ]; then
    echo "Current directory is a git repository. Navigating one level up."
    cd ..
fi

# Update submodules in the first layer of directories
update_submodules