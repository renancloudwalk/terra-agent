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

## Usage

### MCP Server Mode (Recommended)

Run as an MCP server for integration with Claude Desktop or other MCP clients:

```bash
python mcp_server.py
```

### CLI Mode (Legacy)

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
- **`terraform_parse`**: Parse plans and return structured JSON data

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

## Scoring System

The reward function awards points based on:

- **40 pts**: Output starts with "Summary: N change"
- **30 pts**: Number N matches actual plan length
- **20 pts**: For "Count only" responses with no newlines
- **10 pts**: Output has ≤ 1 newline

Minimum passing score: 80/100 points.