#!/usr/bin/env python3
"""
Test script for Best-of-N selection functionality.
Demonstrates how the reward function can select the best output from multiple attempts.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent import run_agent_best_of_n, run_agent_single
from reward import score


def test_best_of_n_small_plan():
    """Test Best-of-N on small plan (no multi-turn)."""
    print("=" * 60)
    print("Testing Best-of-N on Small Plan (3 changes)")
    print("=" * 60)
    
    plan_path = "fixtures/plan_small.txt"
    n = 5
    
    # Run Best-of-N
    best_response, best_score, all_responses = run_agent_best_of_n(
        plan_path=plan_path,
        n=n,
        temperature=0.8  # Higher temperature for more variation
    )
    
    print(f"\n🏆 BEST RESPONSE (Score: {best_score}/100):")
    print("-" * 40)
    print(best_response)
    
    print(f"\n📊 ALL RESPONSES:")
    print("-" * 40)
    for i, (response, response_score) in enumerate(all_responses, 1):
        print(f"Response {i}: {response_score}/100")
        print(f"  {response[:80]}{'...' if len(response) > 80 else ''}")
        print()


def test_best_of_n_large_plan():
    """Test Best-of-N on large plan (with multi-turn)."""
    print("=" * 60)
    print("Testing Best-of-N on Large Plan (10+ changes, Count only)")
    print("=" * 60)
    
    plan_path = "fixtures/plan_large.txt"
    user_reply = "Count only"
    n = 5
    
    # Run Best-of-N
    best_response, best_score, all_responses = run_agent_best_of_n(
        plan_path=plan_path,
        n=n,
        user_reply=user_reply,
        temperature=0.8  # Higher temperature for more variation
    )
    
    print(f"\n🏆 BEST RESPONSE (Score: {best_score}/100):")
    print("-" * 40)
    print(best_response)
    
    print(f"\n📊 ALL RESPONSES:")
    print("-" * 40)
    for i, (response, response_score) in enumerate(all_responses, 1):
        print(f"Response {i}: {response_score}/100")
        print(f"  {response[:80]}{'...' if len(response) > 80 else ''}")
        print()


def compare_single_vs_best_of_n():
    """Compare single shot vs Best-of-N selection."""
    print("=" * 60)
    print("Comparing Single Shot vs Best-of-N")
    print("=" * 60)
    
    plan_path = "fixtures/plan_small.txt"
    spec = {"plan": plan_path}
    
    # Single shot with temperature=0 (deterministic)
    single_response = run_agent_single(plan_path, temperature=0)
    single_score = score(single_response, spec)
    
    # Best-of-N with temperature=0.8 (varied)
    best_response, best_score, all_responses = run_agent_best_of_n(
        plan_path=plan_path,
        n=5,
        temperature=0.8
    )
    
    print(f"🔸 Single Shot (temp=0): {single_score}/100")
    print(f"  {single_response[:80]}{'...' if len(single_response) > 80 else ''}")
    print()
    
    print(f"🔸 Best-of-5 (temp=0.8): {best_score}/100")
    print(f"  {best_response[:80]}{'...' if len(best_response) > 80 else ''}")
    print()
    
    improvement = best_score - single_score
    print(f"📈 Improvement: {improvement:+.1f} points")
    
    if improvement > 0:
        print("✅ Best-of-N improved the result!")
    elif improvement == 0:
        print("➡️  Best-of-N matched the single shot result.")
    else:
        print("❌ Single shot was better (unusual with temp=0 vs temp=0.8)")


if __name__ == "__main__":
    try:
        test_best_of_n_small_plan()
        print("\n" + "=" * 60 + "\n")
        
        test_best_of_n_large_plan()
        print("\n" + "=" * 60 + "\n")
        
        compare_single_vs_best_of_n()
        
    except Exception as e:
        print(f"Error during testing: {e}")
        print("Make sure you have:")
        print("1. OPENAI_API_KEY environment variable set")
        print("2. fixtures/plan_small.txt and fixtures/plan_large.txt files")
        print("3. All dependencies installed (openai, pydantic)")