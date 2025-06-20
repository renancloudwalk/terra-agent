# Terraform Agent

A Python CLI tool that reads Terraform JSON plans and explains them in plain English for non-technical users. Features a versioned Model-Context Protocol (MCP) with structured JSON payloads, multi-turn conversations, and intelligent pruning rules.

## Key Features

- **MCP v1.0 Protocol**: All LLM calls use a single structured JSON payload with versioning
- **Intelligent Pruning**: Tool output limited to last 10 bullets, history to last 2 turns
- **Multi-turn Logic**: Asks "Count only or full summary?" for plans with >5 changes
- **Complete Test Suite**: Pytest-driven with mocked responses and reward scoring

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
uv pip install openai pydantic pytest
```

### Set OpenAI API Key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Run the Agent

```bash
python agent.py fixtures/plan_small.json
```

For plans with more than 5 changes, the agent will ask:
```
Count only or full summary?
```

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