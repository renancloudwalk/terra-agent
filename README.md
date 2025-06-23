# Terraform Agent MCP Server

A Model Context Protocol (MCP) server that reads Terraform plan text and explains it in plain English for non-technical users. Features intelligent pruning, multi-turn conversations, and real Atlantis integration.

## Key Features

- **True MCP Server**: Implements the Model Context Protocol with stdio transport
- **Terraform Plan Parser**: Handles real Terraform plan text output (not JSON)
- **Intelligent Explanations**: Uses structured MCP context with pruning rules
- **Multi-turn Logic**: Asks "Count only or full summary?" for plans with >5 changes
- **Atlantis Ready**: Perfect for CI/CD integration with text-based plan output

## Setup

### Create Python Virtual Environment

```bash
# Create virtual environment with Python 3.11
uv venv --python=python3.11

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Install Dependencies

```bash
uv add mcp openai pydantic pytest
```

### Set OpenAI API Key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Architecture

The terra-agent has **two distinct modes** that share the same core logic:

### 🖥️ CLI Mode
- **Direct script execution** for testing and development
- Used by Makefile commands and pytest
- Processes files directly: `python agent.py fixtures/plan_small.txt`

### 🔌 MCP Server Mode  
- **Continuous stdio server** for Claude Desktop integration
- Exposes tools via Model Context Protocol
- Runs as service: `python mcp_server.py`

```
┌─────────────────┐    ┌─────────────────┐
│   CLI Mode      │    │  MCP Server     │
│                 │    │                 │
│ make demo       │    │ make mcp-server │
│ make test       │    │ (stdio server)  │
│ python agent.py │    │ Claude Desktop  │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│         Same Core Logic                 │
│   (run_agent_single, run_agent_best_of_n) │
└─────────────────────────────────────────┘
```

## Usage

### Quick Testing (CLI Mode)

Use the Makefile for easy testing and development:

```bash
make help           # Show all commands
make demo           # Basic agent demo
make best           # Best-of-N demo
make test           # Run pytest suite
make test-single    # Test single response
make test-multi     # Test Best-of-N selection
```

### Production Integration (MCP Server Mode)

Run as an MCP server for Claude Desktop integration:

```bash
make mcp-server     # Start MCP server
# OR
python mcp_server.py
```

### CLI Mode (Direct Usage)

For direct command-line usage:

```bash
# From file
python agent.py fixtures/plan_small.txt

# From stdin (Atlantis style)
terraform plan | python agent.py
```

### MCP Client Integration

Add to your MCP client config (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "terraform-agent": {
      "command": "uv",
      "args": ["run", "python", "mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

### Available MCP Tools

- **`terraform_explain`**: Parse and explain Terraform plans in plain English
- **`terraform_explain_best_of_n`**: Generate N explanations and return the best one according to reward function

### Run Tests

```bash
uv run pytest -q
```

## MCP (Model-Context Protocol) v1.0

The agent implements a structured protocol where every LLM call receives exactly this JSON format:

```json
{
  "mcp_version": "1.0",
  "system": "<system prompt>",
  "tool_output": ["- create aws_instance.web", "- create aws_s3_bucket.storage"],
  "history": [
    {"role": "user", "content": "Count only"},
    {"role": "assistant", "content": "Summary: 3 changes"}
  ]
}
```

### Pruning Rules

1. **tool_output**: Keeps only the last 10 bullets; older ones collapse into "+N more…"
2. **history**: Keeps only the last 2 conversation turns

## Project Structure

- `tools.py` - Pydantic models and Terraform plan parser
- `agent.py` - Main CLI with MCP protocol implementation
- `reward.py` - Scoring function for output validation
- `prompts.json` - Test specifications
- `tests/test_agent.py` - Parametrized pytest suite with MCP tests
- `fixtures/` - Sample Terraform plan files
  - `plan_small.json` - 3 changes (no multi-turn)
  - `plan_large.json` - 10 changes (triggers multi-turn)

## Scoring System & Best-of-N Selection

The reward function awards points based on:

- **40 pts**: Output starts with "Summary: N change"
- **30 pts**: Number N matches actual plan length
- **20 pts**: For "Count only" responses with no newlines
- **10 pts**: Output has ≤ 1 newline

Minimum passing score: 80/100 points.

### Best-of-N Selection

The agent supports Best-of-N selection where multiple responses are generated and the best one is selected according to the reward function:

```python
from agent import run_agent_best_of_n

# Generate 5 responses and return the best one
best_response, best_score, all_responses = run_agent_best_of_n(
    plan_path="fixtures/plan_small.txt",
    n=5,
    temperature=0.8  # Higher temperature for variation
)
```

This feature is also available through the MCP server as `terraform_explain_best_of_n`.