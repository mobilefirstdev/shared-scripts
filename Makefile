.PHONY: updateLocal
updateLocal:
	@echo "Fetching all remote branches..."
	@git fetch --all
	@echo "Updating local branches with latest changes from remote branches..."
	@for branch in $$(git for-each-ref --format='%(refname:short)' refs/heads/); do \
		echo "Updating branch $$branch..."; \
		git checkout $$branch; \
		if [ -n "$$(git status --porcelain)" ]; then \
			echo "Stashing local changes in branch $$branch..."; \
			git stash; \
			echo "Pulling latest changes for branch $$branch..."; \
			git pull origin $$branch || (echo "Merge conflict detected in branch $$branch. Please resolve conflicts and run make updateLocal again." && exit 1); \
			echo "Applying stashed changes..."; \
			if ! git stash pop; then \
				echo "Merge conflict detected when applying stashed changes in branch $$branch. Please resolve conflicts and run make updateLocal again."; \
				exit 1; \
			fi; \
		else \
			echo "No local changes in branch $$branch. Pulling latest changes..."; \
			git pull origin $$branch; \
		fi; \
	done
	@echo "All local branches have been updated."

.PHONY: preRelease
preRelease:
ifndef branch
	$(error branch is required)
endif
ifndef needs_go_build
	needs_go_build=no
endif
	@echo "Checking current branch..."
	@current_branch=$$(git rev-parse --abbrev-ref HEAD); \
	echo "Current branch: $$current_branch"; \
	echo "Pulling latest changes from remote..."; \
	git pull origin $$current_branch
	@echo "Updating dependencies for branch: $(branch)"
	@GOPRIVATE=github.com/mobilefirstdev/* && cat go.mod | grep "github.com/mobilefirstdev" | grep -v "^module" | awk '{print $$1}' | while read -r module; do \
		echo "Updating $$module to branch $(branch)..."; \
		GOPRIVATE=github.com/mobilefirstdev/* go get "$$module@$(branch)"; \
	done
	@echo "Running go mod tidy..."
	@GOPRIVATE=github.com/mobilefirstdev/* go mod tidy
	@echo "Synchronizing vendor directory..."
	@GOPRIVATE=github.com/mobilefirstdev/* go mod vendor
ifeq ($(needs_go_build),yes)
	@echo "Running go build..."
	@GOPRIVATE=github.com/mobilefirstdev/* go build ./...
else
	@echo "Running make build..."
	@make build
endif
ifdef commit
	@echo "Committing changes with message: $(commit)"
	@git add -A
	@git commit -m "$(commit)"
	@git push
else
	@echo "No commit message provided, skipping commit."
endif
	@echo "preRelease process completed."

.PHONY: lint
lint:
	@echo "Running linter..."
	golangci-lint run


.PHONY: updateRemoteBranches update-remote-prod update-remote-staging update-remote-dev
updateRemoteBranches: update-remote-prod update-remote-staging update-remote-dev

# Update dev branch
update-remote-dev:
	git checkout dev
	git pull origin dev

# Update staging branch
update-remote-staging:
	git checkout staging
	git pull origin staging

# Update prod branch
update-remote-prod:
	git checkout prod
	git pull origin prod

.PHONY: codeMerge
codeMerge:
ifndef base
	$(error base is required)
endif
ifndef target
	$(error target is required)
endif
ifndef commitmess
	$(error commitmess is required)
endif
ifndef needsBuild
	needsBuild=no
endif


	@echo "Pulling target branch: $(target)"
	git checkout $(target)
	git pull origin $(target)

	@echo "Updating base branch: $(base)"
	git checkout $(base)
	git pull origin $(base)
	git checkout $(target)
	git merge $(base)

	@echo "Running preRelease on target branch: $(target)"
ifeq ($(needsBuild),yes)
	make preRelease branch=$(target) needs_go_build=yes
else
	make preRelease branch=$(target)
endif

	@echo "Updating git-modules for branch: $(target)"
	cd shared-scripts
	git pull origin dev
	cd ..

	@echo "Committing changes with message: $(commitmess)"
	git add -A
	git commit -m "$(commitmess)"
	git push origin $(target)

	@echo "codeMerge process completed."



.PHONY: cutoffMerge
cutoffMerge:
ifndef version
	$(error version is required)
endif
	$(eval CURRENT_DIR := $(shell pwd))
	$(eval IS_SERVICE := $(if $(findstring -service,$(CURRENT_DIR)),yes,no))
	$(eval NEEDS_BUILD := $(if $(filter yes,$(IS_SERVICE)),,yes))
	@echo "Current directory: $(CURRENT_DIR)"
	@if [ "$(IS_SERVICE)" = "yes" ]; then \
		echo "This directory is a service."; \
		echo "needsBuild is not set for services."; \
	else \
		echo "This directory is not a service."; \
		echo "needsBuild is set to yes."; \
	fi
	@echo "Executing codeMerge..."
	@if [ "$(IS_SERVICE)" = "yes" ]; then \
		make codeMerge base=dev target=staging commitmess="code cutoff: $(version)"; \
	else \
		make codeMerge base=dev target=staging commitmess="code cutoff: $(version)" needsBuild=yes; \
	fi

.PHONY: releaseMerge
releaseMerge:
ifndef version
	$(error version is required)
endif
	$(eval CURRENT_DIR := $(shell pwd))
	$(eval IS_SERVICE := $(if $(findstring -service,$(CURRENT_DIR)),yes,no))
	$(eval NEEDS_BUILD := $(if $(filter yes,$(IS_SERVICE)),,yes))
	@echo "Current directory: $(CURRENT_DIR)"
	@if [ "$(IS_SERVICE)" = "yes" ]; then \
		echo "This directory is a service."; \
		echo "needsBuild is not set for services."; \
	else \
		echo "This directory is not a service."; \
		echo "needsBuild is set to yes."; \
	fi
	@echo "Executing codeMerge..."
	@if [ "$(IS_SERVICE)" = "yes" ]; then \
		make codeMerge base=staging target=prod commitmess="release: $(version)"; \
	else \
		make codeMerge base=staging target=prod commitmess="release: $(version)" needsBuild=yes; \
	fi



# Makefile for AI-assisted commit

# Define the Python interpreter (use Python 3.10 specifically)
PYTHON := python3.10

# Get the absolute path of the directory containing this Makefile
SHARED_SCRIPTS_DIR := $(shell pwd)

# Define the paths to the Python scripts relative to this Makefile
AUTO_COMMIT_SCRIPT := "$(SHARED_SCRIPTS_DIR)/automation/auto_commit/main.py"
LLM_HANDLER_SCRIPT := "$(SHARED_SCRIPTS_DIR)/automation/llm_handler/main.py"
AUTO_PR_SCRIPT := "$(SHARED_SCRIPTS_DIR)/automation/auto_pr/main.py"

# ANSI color codes
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
RESET := \033[0m

# Target for AI-assisted commit
.PHONY: aiCommit
aiCommit:
	@if [ -z "$(TICKET)" ]; then \
		echo "$(YELLOW)Error: TICKET parameter is required. Usage: make aiCommit TICKET=<ticketName> [PR=yes]$(RESET)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Starting AI-assisted commit process for ticket: $(TICKET)$(RESET)"
	@echo "$(BLUE)SHARED_SCRIPTS_DIR: $(SHARED_SCRIPTS_DIR)$(RESET)"
	@echo "$(BLUE)AUTO_COMMIT_SCRIPT: $(AUTO_COMMIT_SCRIPT)$(RESET)"
	@echo "$(BLUE)LLM_HANDLER_SCRIPT: $(LLM_HANDLER_SCRIPT)$(RESET)"
	@if [ ! -f $(AUTO_COMMIT_SCRIPT) ]; then \
		echo "$(RED)Error: $(AUTO_COMMIT_SCRIPT) not found$(RESET)"; \
		exit 1; \
	fi
	@if [ ! -f $(LLM_HANDLER_SCRIPT) ]; then \
		echo "$(RED)Error: $(LLM_HANDLER_SCRIPT) not found$(RESET)"; \
		exit 1; \
	fi
	@(trap 'echo "$(YELLOW)Cleaning up temporary files...$(RESET)" && rm -rf TEMP autoCommitArtifact.csv && echo "$(GREEN)Temporary files cleaned up.$(RESET)"' EXIT; \
	set -e; \
	echo "$(BLUE)Running auto_commit script...$(RESET)"; \
	cd "$(SHARED_SCRIPTS_DIR)" && $(PYTHON) -m automation.auto_commit.main "$(TICKET)" || (echo "$(RED)Error in auto_commit script$(RESET)" && exit 1); \
	echo "$(BLUE)Running llm_handler script...$(RESET)"; \
	cd "$(SHARED_SCRIPTS_DIR)" && $(PYTHON) -m automation.llm_handler.main "$(TICKET)" || (echo "$(RED)Error in llm_handler script$(RESET)" && exit 1); \
	echo "$(GREEN)AI-assisted commit process completed.$(RESET)"; \
	echo "$(BLUE)Extracting commit message...$(RESET)"; \
	if [ -f TEMP/final_commit_message.txt ]; then \
		COMMIT_MSG=$$(grep -o '"response": *"[^"]*"' TEMP/final_commit_message.txt | sed 's/"response": *"//;s/"//'); \
		if [ -z "$$COMMIT_MSG" ]; then \
			echo "$(RED)Error: Unable to extract commit message from JSON$(RESET)"; \
			exit 1; \
		fi; \
		echo "$(GREEN)Commit message extracted successfully.$(RESET)"; \
		echo "$(BLUE)Switching to branch $(TICKET)...$(RESET)"; \
		git checkout $(TICKET) || (echo "$(RED)Error: Unable to switch to branch $(TICKET)$(RESET)" && exit 1); \
		echo "$(BLUE)Creating commit on branch $(TICKET)...$(RESET)"; \
		git commit --amend -m "$$COMMIT_MSG" || (echo "$(RED)Error: Unable to create commit$(RESET)" && exit 1); \
		echo "$(GREEN)Commit created successfully on branch $(TICKET).$(RESET)"; \
		echo "$(BLUE)Pushing branch $(TICKET) to origin...$(RESET)"; \
		git push -u origin $(TICKET) || (echo "$(RED)Error: Unable to push branch to origin$(RESET)" && exit 1); \
		echo "$(GREEN)Branch $(TICKET) pushed to origin successfully.$(RESET)"; \
		echo "$(BLUE)Switching back to original branch...$(RESET)"; \
		git checkout - || (echo "$(RED)Error: Unable to switch back to original branch$(RESET)" && exit 1); \
		echo "$(GREEN)Returned to original branch.$(RESET)"; \
		if [ "$(PR)" = "yes" ]; then \
			if [ ! -f $(AUTO_PR_SCRIPT) ]; then \
				echo "$(RED)Error: $(AUTO_PR_SCRIPT) not found$(RESET)"; \
				exit 1; \
			fi; \
			echo "$(BLUE)Running auto_pr script...$(RESET)"; \
			cd "$(SHARED_SCRIPTS_DIR)" && $(PYTHON) -m automation.auto_pr.main "$(TICKET)" || (echo "$(RED)Error in auto_pr script$(RESET)" && exit 1); \
			echo "$(GREEN)Auto PR process completed.$(RESET)"; \
		else \
			echo "$(YELLOW)Skipping PR creation. Use PR=yes to create a PR automatically.$(RESET)"; \
		fi; \
	else \
		echo "$(YELLOW)Warning: final_commit_message.txt not found. Skipping commit step.$(RESET)"; \
	fi; \
	echo "$(GREEN)AI-assisted commit process completed successfully.$(RESET)"; \
	echo "$(BLUE)You can now review the changes in the '$(TICKET)' branch on the remote repository.$(RESET)"; \
	)

# Help target
.PHONY: help
help:
	@echo "$(BLUE)Available targets:$(RESET)"
	@echo "  $(GREEN)aiCommit TICKET=<ticketName> [PR=yes]$(RESET)  Run AI-assisted commit process"
	@echo "  $(GREEN)help$(RESET)                                   Display this help message"
	@echo ""
	@echo "$(BLUE)Usage from shared-scripts directory:$(RESET)"
	@echo "  $(GREEN)make aiCommit TICKET=<ticketName> [PR=yes]$(RESET)"
	@echo ""
	@echo "$(BLUE)Usage from main repository:$(RESET)"
	@echo "  $(GREEN)make -f path/to/shared-scripts/Makefile aiCommit TICKET=<ticketName> [PR=yes]$(RESET)"