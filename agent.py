import sys
from openai import OpenAI
from tools import load_plan


def get_action_from_change(resource_change):
    """Determine the action type from the resource change."""
    change = resource_change.change
    
    if change.before is None and change.after is not None:
        return "create"
    elif change.before is not None and change.after is None:
        return "destroy"
    elif change.before is not None and change.after is not None:
        return "update"
    else:
        return "no-op"


def main():
    if len(sys.argv) < 2:
        print("Usage: python agent.py <plan_file_path>")
        sys.exit(1)
    
    plan_file_path = sys.argv[1]
    
    try:
        resource_changes = load_plan(plan_file_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading plan: {e}")
        sys.exit(1)
    
    # Build the tool message with bullet list of changes
    tool_message_content = []
    for resource_change in resource_changes:
        action = get_action_from_change(resource_change)
        tool_message_content.append(f"- {action} {resource_change.address}")
    
    tool_message = "\n".join(tool_message_content)
    
    # Initialize messages with system prompt and tool message
    messages = [
        {
            "role": "system",
            "content": "You are a Terraform plan assistant. If there are more than 5 changes, ask the user 'Count only or full summary?'."
        },
        {
            "role": "user",
            "content": f"Here are the Terraform plan changes:\n\n{tool_message}"
        }
    ]
    
    # Initialize OpenAI client
    client = OpenAI()
    
    # First API call
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0
    )
    
    assistant_reply = response.choices[0].message.content
    print(assistant_reply)
    
    # Check if assistant is asking for count only or full summary
    if "Count only or full summary?" in assistant_reply:
        # Get user input for second turn
        user_response = input("\nYour response: ").strip()
        
        # Append messages for second turn
        messages.append({
            "role": "assistant",
            "content": assistant_reply
        })
        messages.append({
            "role": "user",
            "content": user_response
        })
        
        # Second API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0
        )
        
        final_reply = response.choices[0].message.content
        print(final_reply)


if __name__ == "__main__":
    main()