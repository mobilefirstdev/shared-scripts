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

# Define the Python interpreter
PYTHON := python

# Define the paths to the Python scripts relative to this Makefile
AUTO_COMMIT_SCRIPT := automation/auto_commit/main.py
LLM_HANDLER_SCRIPT := automation/llm_handler/main.py

# Get the absolute path of the directory containing this Makefile
SHARED_SCRIPTS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# Target for AI-assisted commit
.PHONY: aiCommit
aiCommit:
	@if [ -z "$(TICKET)" ]; then \
		echo "Error: TICKET parameter is required. Usage: make -f path/to/shared-scripts/Makefile aiCommit TICKET=<ticketName>"; \
		exit 1; \
	fi
	@echo "Starting AI-assisted commit process for ticket: $(TICKET)"
	@$(PYTHON) $(SHARED_SCRIPTS_DIR)$(AUTO_COMMIT_SCRIPT) $(TICKET)
	@$(PYTHON) $(SHARED_SCRIPTS_DIR)$(LLM_HANDLER_SCRIPT) $(TICKET)
	@echo "AI-assisted commit process completed."
	@echo "Please review the generated commit message in TEMP/final_commit_message.txt"
	@echo "To commit the changes, use: git commit -F TEMP/final_commit_message.txt"

# Help target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  aiCommit TICKET=<ticketName>  Run AI-assisted commit process"
	@echo "  help                          Display this help message"
	@echo ""
	@echo "Usage from main repository:"
	@echo "  make -f path/to/shared-scripts/Makefile aiCommit TICKET=<ticketName>"