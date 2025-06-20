import re
import sys
from typing import List
from pydantic import BaseModel


class Change(BaseModel):
    actions: List[str]
    before: dict | None = None
    after: dict | None = None


class ResourceChange(BaseModel):
    address: str
    mode: str
    type: str
    name: str
    change: Change


def parse_terraform_plan_text(plan_text: str) -> List[ResourceChange]:
    """Parse text-based Terraform plan output and extract resource changes."""
    resource_changes = []
    
    # Find all resource blocks in the plan
    # Look for patterns like: # module.name.resource_type.resource_name will be updated in-place
    resource_pattern = r'# (.+?) will be (.+?)(?:\n|$)'
    
    for match in re.finditer(resource_pattern, plan_text, re.MULTILINE):
        full_address = match.group(1).strip()
        action_description = match.group(2).strip()
        
        # Parse the action
        actions = []
        if 'created' in action_description or 'be created' in action_description:
            actions = ['create']
        elif 'updated' in action_description or 'be updated' in action_description:
            actions = ['update'] 
        elif 'destroyed' in action_description or 'be destroyed' in action_description:
            actions = ['delete']
        elif 'replaced' in action_description or 'be replaced' in action_description:
            actions = ['replace']
        else:
            actions = ['unknown']
        
        # Extract resource type and name from address
        # Handle module paths like: module.name.resource_type.resource_name
        if '.' in full_address:
            parts = full_address.split('.')
            if len(parts) >= 2:
                # For module.name.resource_type.resource_name
                if parts[0] == 'module' and len(parts) >= 4:
                    resource_type = parts[2]
                    resource_name = '.'.join(parts[3:])  # Handle names with dots
                # For resource_type.resource_name
                else:
                    resource_type = parts[0]
                    resource_name = '.'.join(parts[1:])
            else:
                resource_type = 'unknown'
                resource_name = full_address
        else:
            resource_type = 'unknown'
            resource_name = full_address
        
        change = Change(actions=actions)
        
        resource_change = ResourceChange(
            address=full_address,
            mode='managed',
            type=resource_type,
            name=resource_name,
            change=change
        )
        
        resource_changes.append(resource_change)
    
    return resource_changes


def load_plan(path: str) -> List[ResourceChange]:
    """Load Terraform plan from text file or stdin and return list of resource changes."""
    if path == '-' or path == '/dev/stdin':
        # Read from stdin
        plan_text = sys.stdin.read()
    else:
        # Read from file
        with open(path, 'r') as f:
            plan_text = f.read()
    
    return parse_terraform_plan_text(plan_text)