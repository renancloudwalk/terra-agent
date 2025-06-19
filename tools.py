import json
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class Change:
    before: Optional[Dict[str, Any]]
    after: Optional[Dict[str, Any]]
    before_sensitive: Optional[Dict[str, bool]]
    after_sensitive: Optional[Dict[str, bool]]
    after_unknown: Optional[Dict[str, bool]]


@dataclass
class ResourceChange:
    address: str
    mode: str
    type: str
    name: str
    provider_name: str
    change: Change


def load_plan(path: str) -> List[ResourceChange]:
    """
    Load a Terraform JSON plan file and return a list of ResourceChange instances.
    
    Args:
        path: Path to the Terraform JSON plan file
        
    Returns:
        List of ResourceChange instances
    """
    plan_path = Path(path)
    
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {path}")
    
    with open(plan_path, 'r') as f:
        plan_data = json.load(f)
    
    resource_changes = []
    
    for resource_change_data in plan_data.get('resource_changes', []):
        change_data = resource_change_data.get('change', {})
        
        change = Change(
            before=change_data.get('before'),
            after=change_data.get('after'),
            before_sensitive=change_data.get('before_sensitive'),
            after_sensitive=change_data.get('after_sensitive'),
            after_unknown=change_data.get('after_unknown')
        )
        
        resource_change = ResourceChange(
            address=resource_change_data.get('address', ''),
            mode=resource_change_data.get('mode', ''),
            type=resource_change_data.get('type', ''),
            name=resource_change_data.get('name', ''),
            provider_name=resource_change_data.get('provider_name', ''),
            change=change
        )
        
        resource_changes.append(resource_change)
    
    return resource_changes