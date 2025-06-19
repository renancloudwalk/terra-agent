import json
import pytest
import subprocess
import tempfile
import os
from pathlib import Path
from reward import score


def run_agent(plan_path: str, user_reply: str = None) -> str:
    """
    Run the agent with the given plan path and optional user reply.
    Returns the final output from the agent.
    """
    # Run the agent script
    cmd = ["python", "agent.py", plan_path]
    
    if user_reply is not None:
        # Use subprocess with input for multi-turn conversation
        result = subprocess.run(
            cmd,
            input=user_reply,
            text=True,
            capture_output=True,
            cwd=Path(__file__).parent.parent
        )
    else:
        # Single turn conversation
        result = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            cwd=Path(__file__).parent.parent
        )
    
    if result.returncode != 0:
        pytest.fail(f"Agent failed with error: {result.stderr}")
    
    return result.stdout.strip()


@pytest.fixture
def prompts_data():
    """Load the prompts.json file."""
    prompts_path = Path(__file__).parent.parent / "prompts.json"
    with open(prompts_path, 'r') as f:
        return json.load(f)


@pytest.mark.parametrize("spec_name", ["small_plan", "large_plan_count"])
def test_agent_scenarios(prompts_data, spec_name):
    """
    Test agent scenarios from prompts.json.
    Each scenario must score >= 80 points.
    """
    spec = prompts_data[spec_name]
    
    # Get the plan path relative to the project root
    plan_path = Path(__file__).parent.parent / spec["plan"]
    
    # Run the agent
    output = run_agent(str(plan_path), spec.get("user_reply"))
    
    # Score the output
    test_score = score(output, spec)
    
    # Assert minimum score
    assert test_score >= 80, f"Score {test_score} < 80 for {spec_name}. Output: {output}"


def test_score_function():
    """Test the scoring function with known inputs."""
    # Test case 1: Perfect score
    spec = {
        "plan": "fixtures/plan_small.json", 
        "user_reply": None
    }
    output = "Summary: 3 changes to apply."
    
    # This should get 40 + 30 + 10 = 80 points (assuming the plan has 3 changes)
    test_score = score(output, spec)
    assert test_score >= 40  # At least the summary format points
    
    # Test case 2: Count only scenario
    spec = {
        "plan": "fixtures/plan_large.json",
        "user_reply": "Count only"
    }
    output = "Summary: 10 changes"
    
    # This should get points for format, count match (if correct), count-only bonus, and short summary
    test_score = score(output, spec)
    assert test_score >= 40  # At least the summary format points