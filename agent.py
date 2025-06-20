import json
import sys
from typing import List
from openai import OpenAI
from tools import load_plan

BOT_PROMPT = "You are a Terraform plan assistant. Explain every change in plain English, as if to someone with zero technical background. If there are more than 5 changes, ask \"Count only or full summary?\""


def build_context(system: str, tool_output: List[str], history: List[dict], mcp_version="1.0") -> str:
    """Build MCP context with pruning rules."""
    # Prune tool_output to last 10 bullets, collapse older into "+N more…"
    pruned_tool_output = tool_output.copy()
    if len(pruned_tool_output) > 10:
        excess_count = len(pruned_tool_output) - 9
        pruned_tool_output = [f"+{excess_count} more…"] + pruned_tool_output[-9:]
    
    # Prune history to last 2 turns
    pruned_history = history[-2:] if len(history) > 2 else history
    
    ctx = {
        "mcp_version": mcp_version,
        "system": system,
        "tool_output": pruned_tool_output,
        "history": pruned_history
    }
    return json.dumps(ctx)


def run_agent(plan_path: str) -> str:
    """Run the agent with MCP protocol."""
    # Load and bulletize changes
    resource_changes = load_plan(plan_path)
    tool_output = []
    for change in resource_changes:
        actions = change.change.actions
        action = actions[0] if actions else "no-op"
        tool_output.append(f"- {action} {change.address}")
    
    # First turn: history = []
    history = []
    
    # Build context JSON
    context_json = build_context(BOT_PROMPT, tool_output, history)
    
    # Call OpenAI API
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": context_json}],
        temperature=0
    )
    
    assistant_reply = response.choices[0].message.content
    
    # Check if model asks for count only or full summary
    if "Count only or full summary?" in assistant_reply:
        # Read user input
        user_reply = input().strip()
        
        # Append to history
        history.append({"role": "user", "content": user_reply})
        history.append({"role": "assistant", "content": assistant_reply})
        
        # Rebuild context with updated history
        context_json = build_context(BOT_PROMPT, tool_output, history)
        
        # Second API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": context_json}],
            temperature=0
        )
        
        return response.choices[0].message.content
    
    return assistant_reply


if __name__ == "__main__":
    # Support reading from stdin or file
    if len(sys.argv) < 2:
        # No argument provided, read from stdin
        plan_path = "-"
    else:
        plan_path = sys.argv[1]
    
    result = run_agent(plan_path)
    print(result)