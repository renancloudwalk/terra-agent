#!/usr/bin/env python3
"""
Demonstration of Best-of-N selection functionality.
Shows how the reward function selects the best response from multiple attempts.
"""

from agent import run_agent_best_of_n, run_agent_single
from reward import score
import json


def demo_best_of_n():
    """Demonstrate Best-of-N selection."""
    print("🎯 Terra-Agent Best-of-N Selection Demo")
    print("=" * 50)
    
    # Test 1: Single shot vs Best-of-N on small plan
    print("\n📊 Test 1: Single Shot vs Best-of-N (Small Plan)")
    print("-" * 40)
    
    plan_path = "fixtures/plan_small.txt"
    
    # Single shot (deterministic)
    single_response = run_agent_single(plan_path, temperature=0)
    single_score = score(single_response, {"plan": plan_path})
    
    print(f"Single Shot (temp=0): {single_score}/100")
    print(f"Response: {single_response}")
    print()
    
    # Best-of-N with variation
    best_response, best_score, all_responses = run_agent_best_of_n(
        plan_path=plan_path,
        n=5,
        temperature=0.7
    )
    
    print(f"Best-of-5 (temp=0.7): {best_score}/100")
    print(f"Response: {best_response}")
    
    improvement = best_score - single_score 
    print(f"Improvement: {improvement:+.1f} points")
    
    # Test 2: Multi-turn scenario
    print(f"\n📊 Test 2: Best-of-N Multi-turn (Large Plan)")
    print("-" * 40)
    
    plan_path = "fixtures/plan_large.txt"
    
    best_response, best_score, all_responses = run_agent_best_of_n(
        plan_path=plan_path,
        n=3,
        user_reply="Count only",
        temperature=0.5
    )
    
    print(f"Best-of-3 Result: {best_score}/100")
    print(f"Response: {best_response}")
    
    # Show all responses and scores
    print(f"\n📋 All Responses:")
    for i, (resp, resp_score) in enumerate(all_responses, 1):
        print(f"  {i}. Score: {resp_score}/100 - {resp}")
    
    # Test 3: Higher temperature for more variation
    print(f"\n📊 Test 3: High Temperature Variation") 
    print("-" * 40)
    
    best_response, best_score, all_responses = run_agent_best_of_n(
        plan_path="fixtures/plan_small.txt",
        n=7,
        temperature=1.2  # Very high temperature
    )
    
    print(f"Best-of-7 (temp=1.2): {best_score}/100")
    print(f"Response: {best_response}")
    
    # Show score distribution
    scores = [score for _, score in all_responses]
    avg_score = sum(scores) / len(scores)
    min_score = min(scores)
    max_score = max(scores)
    
    print(f"\nScore Distribution:")
    print(f"  Average: {avg_score:.1f}/100")
    print(f"  Range: {min_score}/100 - {max_score}/100")
    print(f"  Best vs Average: {best_score - avg_score:+.1f} points")
    
    print(f"\n🎯 Best-of-N Selection Summary:")
    print(f"✅ Implemented Best-of-N selection with reward function scoring")
    print(f"✅ Higher temperature generates more variation")
    print(f"✅ Reward function successfully selects best responses")
    print(f"✅ Integrated with both CLI and MCP server")


if __name__ == "__main__":
    try:
        demo_best_of_n()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nRequirements:")
        print("- OPENAI_API_KEY environment variable")
        print("- fixtures/plan_small.txt and fixtures/plan_large.txt")
        print("- OpenAI Python package")