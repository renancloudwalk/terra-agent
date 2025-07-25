import json
import sys
from typing import List, Tuple
from openai import OpenAI
from tools import load_plan
from reward import score

BOT_PROMPT = """You are a Terraform plan assistant that explains infrastructure changes concisely for developers.

Always start your response with 'Summary: N changes' where N is the exact number of changes, then list what is being done.

For each change, extract and include the most important details:
- Resource action (creating/deleting/modifying)
- Resource type and terraform name
- Actual resource name/identifier (from the configuration)
- Environment (prod/stg/dev if visible)
- Key configuration details (size, region, ports, etc.)

Examples:
- "Creating Redis instance 'my-stg-redis' (google_redis_instance.default) in us-central1"
- "Deleting RDS database 'prod-db' (aws_db_instance.main) - t3.micro"
- "Modifying security group 'web-sg' (aws_security_group.web_sg) - adding port 443"
- "Creating S3 bucket 'app-storage-prod' (aws_s3_bucket.storage)"

Extract meaningful names and configuration from the plan details, not just the terraform resource names.

If there are more than 5 changes, ask "Count only or full summary?" 
- If user says "Count only", respond with just 'Summary: N changes' on a single line
- If user wants full summary, provide the detailed action statements above

Be concise but informative - include the details that matter for understanding the actual impact."""


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
    # Load and bulletize changes with details
    resource_changes = load_plan(plan_path)
    tool_output = []
    for change in resource_changes:
        actions = change.change.actions
        action = actions[0] if actions else "no-op"
        
        # Include basic info
        line = f"- {action} {change.address}"
        
        # Add configuration details if available
        if hasattr(change.change, 'after') and change.change.after:
            after = change.change.after
            details = []
            
            # Extract common meaningful fields
            if isinstance(after, dict):
                if 'name' in after and after['name']:
                    details.append(f"name: {after['name']}")
                if 'display_name' in after and after['display_name']:
                    details.append(f"display_name: {after['display_name']}")
                if 'instance_type' in after and after['instance_type']:
                    details.append(f"type: {after['instance_type']}")
                if 'memory_size_gb' in after and after['memory_size_gb']:
                    details.append(f"memory: {after['memory_size_gb']}GB")
                if 'region' in after and after['region']:
                    details.append(f"region: {after['region']}")
                if 'location_id' in after and after['location_id']:
                    details.append(f"location: {after['location_id']}")
                if 'tier' in after and after['tier']:
                    details.append(f"tier: {after['tier']}")
                if 'redis_version' in after and after['redis_version']:
                    details.append(f"version: {after['redis_version']}")
                
            if details:
                line += f" ({', '.join(details)})"
        
        tool_output.append(line)
    
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