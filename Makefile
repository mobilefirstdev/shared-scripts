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
	@GOPRIVATE=github.com/mobilefirstdev/* && cat go.mod | grep "github.com/mobilefirstdev" | grep -v "\^module" | cut -d ' ' -f 1 | while read -r module; do \
		echo "Updating $$module to branch $(branch)..."; \
		GOPRIVATE=github.com/mobilefirstdev/* go get "$$module"@$(branch); \
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
	@go run github.com/golangci/golangci-lint/cmd/golangci-lint run