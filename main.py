def main():
    """Main entry point for terra-agent."""
    print("Terraform Agent - Parse and explain Terraform plans in plain English")
    print()
    print("Usage:")
    print("  CLI Mode:    python agent.py <plan_file>")
    print("  MCP Server:  python mcp_server.py")
    print("  Tests:       uv run pytest -v")
    print()
    print("For more information, see README.md")


if __name__ == "__main__":
    main()
