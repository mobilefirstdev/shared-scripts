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
                echo "Updating git submodules in $dir"
                if git submodule update; then
                    echo "Successfully updated submodules in $dir"
                else
                    echo "Failed to update submodules in $dir"
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