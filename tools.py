import json
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


def load_plan(path: str) -> List[ResourceChange]:
    """Load Terraform plan and return list of resource changes."""
    with open(path, 'r') as f:
        plan_data = json.load(f)
    
    resource_changes = plan_data.get('resource_changes', [])
    return [ResourceChange(**change) for change in resource_changes]