import re
from tools import load_plan


def score(output: str, spec: dict) -> float:
    """
    Score the output based on the specification criteria.
    
    Returns a score out of 100 points:
    - 40 pts if output starts with "Summary: N change" or "Summary: N changes"
    - 30 pts if the N matches len(load_plan(spec["plan"]))
    - 20 pts if user_reply=="Count only" and response is count-only
    - 10 pts if full explanations contain business-friendly language
    """
    total_score = 0.0
    
    # 40 pts: Check if output starts with "Summary: N change" or "Summary: N changes"
    if re.match(r"^Summary: \d+ changes?", output):
        total_score += 40
    
    # 30 pts: Check if the N matches the actual plan length
    try:
        number_match = re.match(r"^Summary: (\d+) changes?", output)
        if number_match:
            summary_count = int(number_match.group(1))
            actual_count = len(load_plan(spec["plan"]))
            if summary_count == actual_count:
                total_score += 30
    except Exception:
        pass
    
    # 20 pts: Check count-only behavior
    if spec.get("user_reply") == "Count only":
        # For count-only, should be just one line
        if "\n" not in output.strip():
            total_score += 20
    else:
        # For full explanations, should have multiple lines with explanations
        if "\n" in output and len(output.split('\n')) > 2:
            total_score += 20
    
    # 10 pts: Check for business-friendly language in explanations
    business_terms = ["website", "server", "database", "security", "storage", "data", 
                     "business", "customers", "access", "protect", "cost", "online"]
    if any(term in output.lower() for term in business_terms):
        total_score += 10
    
    return total_score