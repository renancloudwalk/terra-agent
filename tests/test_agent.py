import json
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent import run_agent_single, build_context, BOT_PROMPT
from reward import score


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
    
    # Mock OpenAI API responses
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    
    if spec_name == "small_plan":
        # Small plan: full explanation
        mock_response.choices[0].message.content = """Summary: 3 changes

1. Creating a new web server to host your website
2. Adding security rules to protect your data  
3. Setting up storage for your files"""
        
        with patch('agent.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Mock input to prevent actual user input
            with patch('builtins.input'):
                output = run_agent_single(spec["plan"])
    
    elif spec_name == "large_plan_count":
        # Large plan: multi-turn conversation
        mock_response_1 = MagicMock()
        mock_response_1.choices = [MagicMock()]
        mock_response_1.choices[0].message.content = "Count only or full summary?"
        
        mock_response_2 = MagicMock()
        mock_response_2.choices = [MagicMock()]
        mock_response_2.choices[0].message.content = "Summary: 11 changes"
        
        with patch('agent.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]
            mock_openai.return_value = mock_client
            
            # Mock input to return the user reply
            with patch('builtins.input', return_value=spec["user_reply"]):
                output = run_agent_single(spec["plan"])
    
    # Score the output
    test_score = score(output, spec)
    
    # Assert minimum score
    assert test_score >= 80, f"Score {test_score} < 80 for {spec_name}. Output: {output}"


def test_build_context():
    """Test the MCP context building function."""
    system = "Test system prompt"
    tool_output = [f"- item {i}" for i in range(15)]  # More than 10 items
    history = [{"role": "user", "content": f"turn {i}"} for i in range(5)]  # More than 2 turns
    
    context_json = build_context(system, tool_output, history)
    context = json.loads(context_json)
    
    # Check MCP structure
    assert context["mcp_version"] == "1.0"
    assert context["system"] == system
    
    # Check tool_output pruning (should have exactly 10 items with "+6 more…" prefix)
    assert len(context["tool_output"]) == 10
    assert context["tool_output"][0] == "+6 more…"
    
    # Check history pruning (should have exactly 2 items)
    assert len(context["history"]) == 2


def test_score_function():
    """Test the scoring function with known inputs."""
    # Test case 1: Perfect score for small plan with explanations
    spec = {
        "plan": "fixtures/plan_small.txt"
    }
    output = """Summary: 3 changes

1. Creating a new web server to host your website
2. Adding security rules to protect your data  
3. Setting up storage for your files"""
    
    test_score = score(output, spec)
    assert test_score >= 80  # Should get full points
    
    # Test case 2: Count only scenario
    spec = {
        "plan": "fixtures/plan_large.txt",
        "user_reply": "Count only"
    }
    output = "Summary: 11 changes"
    
    test_score = score(output, spec)
    assert test_score >= 90  # Should get full points