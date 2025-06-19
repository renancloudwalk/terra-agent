import re
from tools import load_plan


def score(output: str, spec: dict) -> float:
    """
    Score the output based on the specification criteria.
    
    Returns a score out of 100 points:
    - 40 pts if output starts with "Summary: N change"
    - 30 pts if the N matches len(load_plan(spec["plan"]))
    - 20 pts if user_reply=="Count only" and no extra bullets (no newline)
    - 10 pts if the summary is d 2 lines
    """
    total_score = 0.0
    
    # 40 pts: Check if output starts with "Summary: N change"
    summary_pattern = r"^Summary: \d+ change"
    if re.match(summary_pattern, output):
        total_score += 40
        
        # 30 pts: Check if the N matches the actual plan length
        try:
            # Extract the number from the summary
            number_match = re.match(r"^Summary: (\d+) change", output)
            if number_match:
                summary_count = int(number_match.group(1))
                actual_count = len(load_plan(spec["plan"]))
                if summary_count == actual_count:
                    total_score += 30
        except Exception:
            # If we can't load the plan or parse the number, don't award points
            pass
    
    # 20 pts: Check if user_reply is "Count only" and no extra bullets
    if spec.get("user_reply") == "Count only":
        # Check that there are no bullet points (lines starting with -)
        lines = output.split('\n')
        has_bullets = any(line.strip().startswith('-') for line in lines)
        if not has_bullets:
            total_score += 20
    
    # 10 pts: Check if summary is d 2 lines
    line_count = len([line for line in output.split('\n') if line.strip()])
    if line_count <= 2:
        total_score += 10
    
    return total_score