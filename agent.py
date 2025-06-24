import json
import sys
from typing import List, Tuple
from openai import OpenAI
from tools import load_plan
from reward import score

BOT_PROMPT = """You are a Terraform plan assistant that explains infrastructure changes concisely for developers.

Always start your response with 'Summary: N changes' where N is the exact number of changes, then list what is being done.

For each change, simply state what action is being performed:
- "Creating an EC2 instance (aws_instance.web)"
- "Deleting an RDS database (aws_db_instance.main)"
- "Modifying a security group (aws_security_group.web_sg)"
- "Creating an S3 bucket (aws_s3_bucket.storage)"

Keep explanations brief and factual. Include the resource type and name from the plan.

If there are more than 5 changes, ask "Count only or full summary?" 
- If user says "Count only", respond with just 'Summary: N changes' on a single line
- If user wants full summary, provide the brief action statements above

Be concise and direct - just state what's happening, not why or how."""


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


def run_agent_single(plan_path: str, user_reply: str = None, temperature: float = 0) -> str:
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
        temperature=temperature
    )
    
    assistant_reply = response.choices[0].message.content
    
    # Check if model asks for count only or full summary
    if "Count only or full summary?" in assistant_reply:
        # Use provided user_reply or read from input
        if user_reply is None:
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
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    return assistant_reply


def run_agent_best_of_n(plan_path: str, n: int = 3, user_reply: str = None, temperature: float = 0.7) -> Tuple[str, float, List[Tuple[str, float]]]:
    """
    Run agent N times and return the best response according to the reward function.
    
    Args:
        plan_path: Path to the Terraform plan
        n: Number of responses to generate
        user_reply: User reply for multi-turn (None for interactive)
        temperature: Temperature for API calls
    
    Returns:
        Tuple of (best_response, best_score, all_responses_with_scores)
    """
    # Create spec for scoring
    spec = {
        "plan": plan_path,
        "user_reply": user_reply
    }
    
    responses_with_scores = []
    
    # Generate N responses
    for i in range(n):
        try:
            response = run_agent_single(plan_path, user_reply, temperature)
            response_score = score(response, spec)
            responses_with_scores.append((response, response_score))
            print(f"Response {i+1}/{n}: Score {response_score}/100")
        except Exception as e:
            print(f"Error generating response {i+1}: {e}")
            responses_with_scores.append((f"Error: {e}", 0.0))
    
    # Sort by score (highest first) and return the best
    responses_with_scores.sort(key=lambda x: x[1], reverse=True)
    best_response, best_score = responses_with_scores[0]
    
    return best_response, best_score, responses_with_scores


def run_agent(plan_path: str) -> str:
    """Legacy wrapper for backward compatibility."""
    return run_agent_single(plan_path)


if __name__ == "__main__":
    # Support reading from stdin or file
    if len(sys.argv) < 2:
        # No argument provided, read from stdin
        plan_path = "-"
    else:
        plan_path = sys.argv[1]
    
    result = run_agent(plan_path)
    print(result)