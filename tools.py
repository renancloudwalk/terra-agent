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
    
    # Find all resource blocks in the plan with their configuration
    # Look for patterns like: # resource_type.resource_name will be created
    # followed by resource configuration block
    
    # Split by resource blocks
    resource_blocks = re.split(r'\n  # (.+?) will be (.+?)\n', plan_text)
    
    # Process each resource block
    for i in range(1, len(resource_blocks), 3):  # Skip first element, then take every 3rd
        if i + 2 < len(resource_blocks):
            full_address = resource_blocks[i].strip()
            action_description = resource_blocks[i + 1].strip()
            config_block = resource_blocks[i + 2] if i + 2 < len(resource_blocks) else ""
            
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
            if '.' in full_address:
                parts = full_address.split('.')
                if len(parts) >= 2:
                    # For module.name.resource_type.resource_name
                    if parts[0] == 'module' and len(parts) >= 4:
                        resource_type = parts[2]
                        resource_name = '.'.join(parts[3:])
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
            
            # Parse configuration details from the config block
            after_config = {}
            if config_block:
                # Extract key-value pairs from the resource block
                config_lines = config_block.split('\n')
                for line in config_lines:
                    line = line.strip()
                    # Look for lines like: + name = "value"
                    config_match = re.match(r'[+~-]?\s*(\w+)\s*=\s*(.+)', line)
                    if config_match:
                        key = config_match.group(1)
                        value = config_match.group(2).strip()
                        # Clean up the value (remove quotes, handle known after apply)
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]  # Remove quotes
                        elif value == '(known after apply)':
                            continue  # Skip these
                        
                        after_config[key] = value
            
            change = Change(actions=actions, after=after_config if after_config else None)
            
            resource_change = ResourceChange(
                address=full_address,
                mode='managed',
                type=resource_type,
                name=resource_name,
                change=change
            )
            
            resource_changes.append(resource_change)
    
    # Fallback to simpler parsing if the above doesn't work
    if not resource_changes:
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
            if '.' in full_address:
                parts = full_address.split('.')
                if len(parts) >= 2:
                    if parts[0] == 'module' and len(parts) >= 4:
                        resource_type = parts[2]
                        resource_name = '.'.join(parts[3:])
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