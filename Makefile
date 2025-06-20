.PHONY: help install test test-quick demo demo-best-of-n clean lint format check-env
.DEFAULT_GOAL := help

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Terra-Agent Makefile Commands$(NC)"
	@echo "================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

check-env: ## Check if required environment variables are set
	@echo "$(GREEN)Checking environment...$(NC)"
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "$(RED)Error: OPENAI_API_KEY not set$(NC)"; \
		echo "Run: export OPENAI_API_KEY='your-key-here'"; \
		exit 1; \
	else \
		echo "$(GREEN)✓ OPENAI_API_KEY is set$(NC)"; \
	fi

install: ## Install dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	uv add mcp openai pydantic pytest

test: check-env ## Run all tests
	@echo "$(GREEN)Running pytest...$(NC)"
	uv run pytest -v

test-quick: check-env ## Run tests without verbose output
	@echo "$(GREEN)Running quick tests...$(NC)"
	uv run pytest -q

demo: check-env ## Run basic agent demo on small plan
	@echo "$(GREEN)Running basic agent demo...$(NC)"
	@echo "Testing with fixtures/plan_small.txt (3 changes):"
	@echo "----------------------------------------"
	uv run python agent.py fixtures/plan_small.txt

demo-large: check-env ## Run agent demo on large plan (interactive)
	@echo "$(GREEN)Running large plan demo (will ask for Count only or full summary)...$(NC)"
	@echo "Testing with fixtures/plan_large.txt (10+ changes):"
	@echo "Type 'Count only' when prompted:"
	@echo "----------------------------------------"
	uv run python agent.py fixtures/plan_large.txt

demo-best-of-n: check-env ## Run Best-of-N selection demo
	@echo "$(GREEN)Running Best-of-N selection demo...$(NC)"
	uv run python demo_best_of_n.py

test-best-of-n: check-env ## Run Best-of-N specific tests
	@echo "$(GREEN)Running Best-of-N tests...$(NC)"
	uv run python test_best_of_n.py

test-single: check-env ## Test single response on small plan
	@echo "$(GREEN)Testing single response (temp=0)...$(NC)"
	@uv run python -c "from agent import run_agent_single; print(run_agent_single('fixtures/plan_small.txt'))"

test-multi: check-env ## Test Best-of-N (N=3) on small plan  
	@echo "$(GREEN)Testing Best-of-N (N=3, temp=0.7)...$(NC)"
	@uv run python -c "from agent import run_agent_best_of_n; best, score, all_resp = run_agent_best_of_n('fixtures/plan_small.txt', n=3, temperature=0.7); print(f'Best: {best} (Score: {score}/100)')"

mcp-server: check-env ## Start MCP server
	@echo "$(GREEN)Starting MCP server...$(NC)"
	@echo "Press Ctrl+C to stop"
	uv run python mcp_server.py

test-mcp: check-env ## Show MCP testing methods
	@echo "$(GREEN)MCP Testing Guide:$(NC)"
	uv run python test_mcp_no_deps.py

test-mcp-manual: ## Show manual MCP testing instructions
	@echo "$(GREEN)Manual MCP Testing Instructions:$(NC)"
	uv run python test_mcp_simple.py --manual-info

test-mcp-examples: ## Show MCP JSON-RPC examples
	@echo "$(GREEN)MCP JSON-RPC Examples:$(NC)"
	uv run python test_mcp_no_deps.py --examples

test-mcp-stdio: check-env ## Test MCP server via stdio (advanced)
	@echo "$(GREEN)Testing MCP server via stdio...$(NC)"
	./test_running_server.sh

reward-test: check-env ## Test reward function directly
	@echo "$(GREEN)Testing reward function...$(NC)"
	@uv run python -c "from reward import score; print('Testing reward function:'); print(f'Perfect response: {score(\"Summary: 3 changes\", {\"plan\": \"fixtures/plan_small.txt\"})}/100'); print(f'Bad response: {score(\"Here are some changes...\", {\"plan\": \"fixtures/plan_small.txt\"})}/100')"

lint: ## Run linting (if available)
	@echo "$(GREEN)Running linting...$(NC)"
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check .; \
	elif command -v flake8 >/dev/null 2>&1; then \
		flake8 .; \
	else \
		echo "$(YELLOW)No linter found (ruff or flake8)$(NC)"; \
	fi

format: ## Format code (if available)
	@echo "$(GREEN)Formatting code...$(NC)"
	@if command -v ruff >/dev/null 2>&1; then \
		ruff format .; \
	elif command -v black >/dev/null 2>&1; then \
		black .; \
	else \
		echo "$(YELLOW)No formatter found (ruff or black)$(NC)"; \
	fi

clean: ## Clean up cache and temporary files
	@echo "$(GREEN)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

status: ## Show project status and requirements check
	@echo "$(GREEN)Terra-Agent Status$(NC)"
	@echo "=================="
	@echo "Git status:"
	@git status --porcelain || echo "Not a git repository"
	@echo ""
	@echo "Python version:"
	@uv run python --version
	@echo ""
	@echo "Environment check:"
	@make check-env 2>/dev/null || echo "$(RED)Environment not ready$(NC)"
	@echo ""
	@echo "Available fixtures:"
	@ls -la fixtures/ 2>/dev/null || echo "$(RED)No fixtures directory$(NC)"

# Quick aliases
quick: test-quick ## Alias for test-quick
best: demo-best-of-n ## Alias for demo-best-of-n