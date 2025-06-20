import re
from tools import load_plan


def score(output: str, spec: dict) -> float:
    """
    Score the output based on the specification criteria.
    
    Returns a score out of 100 points:
    - 40 pts if output starts with "Summary: N change"
    - 30 pts if the N matches len(load_plan(spec["plan"]))
    - 20 pts if user_reply=="Count only" and no newline in output
    - 10 pts if output.count("\\n") <= 1
    """
    total_score = 0.0
    
    # 40 pts: Check if output starts with "Summary: N change"
    if re.match(r"^Summary: \d+ change", output):
        total_score += 40
    
    # 30 pts: Check if the N matches the actual plan length
    try:
        number_match = re.match(r"^Summary: (\d+) change", output)
        if number_match:
            summary_count = int(number_match.group(1))
            actual_count = len(load_plan(spec["plan"]))
            if summary_count == actual_count:
                total_score += 30
    except Exception:
        pass
    
    # 20 pts: Check if user_reply is "Count only" and no newline in output
    if spec.get("user_reply") == "Count only" and "\n" not in output:
        total_score += 20
    
    # 10 pts: Check if output has <= 1 newline
    if output.count("\n") <= 1:
        total_score += 10
    
    return total_score