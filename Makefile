
.PHONY: preRelease
preRelease:
ifndef branch
	$(error branch is required)
endif
	@echo "Checking current branch..."
	@current_branch=$$(git rev-parse --abbrev-ref HEAD); \
	echo "Current branch: $$current_branch"; \
	echo "Pulling latest changes from remote..."; \
	git pull origin $$current_branch

	@echo "Updating dependencies for branch: $(branch)"
	@GOPRIVATE=github.com/mobilefirstdev/* && cat go.mod | grep "github.com/mobilefirstdev" | grep -v "^module" | cut -d ' ' -f 1 | while read -r module; do \
		echo "Updating $$module to branch $(branch)..."; \
		GOPRIVATE=github.com/mobilefirstdev/* go get "$$module"@$(branch); \
	done
	@echo "Running go mod tidy..."
	@GOPRIVATE=github.com/mobilefirstdev/* go mod tidy
	@echo "Synchronizing vendor directory..."
	@GOPRIVATE=github.com/mobilefirstdev/* go mod vendor
	@echo "Running go build..."
	@GOPRIVATE=github.com/mobilefirstdev/* go build ./...
ifdef commit
	@echo "Committing changes with message: $(commit)"
	@git add -A
	@git commit -m "$(commit)"
	@git push
else
	@echo "No commit message provided, skipping commit."
endif
	@echo "preRelease process completed."