import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel


class Change(BaseModel):
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    before_sensitive: Optional[Dict[str, bool]] = None
    after_sensitive: Optional[Dict[str, bool]] = None
    after_unknown: Optional[Dict[str, bool]] = None


class ResourceChange(BaseModel):
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
        
        change = Change(**change_data)
        
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