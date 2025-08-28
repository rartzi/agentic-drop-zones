# Agentic Drop Zone Documentation

## Reference Links
- https://docs.anthropic.com/en/docs/claude-code/sdk/sdk-python
- https://github.com/gorakhargosh/watchdog?tab=readme-ov-file#example-api-usage
- https://pythonhosted.org/watchdog/api.html
- https://docs.astral.sh/uv/guides/scripts/#next-steps
- https://replicate.com/docs/reference/mcp
- https://docs.astral.sh/uv/guides/scripts/#running-a-script-with-dependencies
- https://docs.astral.sh/uv
- https://github.com/openai/whisper
- https://github.com/openai/openai-python

## Recent Updates

### Rich Console Output
Integrated Rich library for beautiful console output:
- Claude Code responses displayed in individual styled panels as content streams in
- Each response block appears in its own panel with title and subtitle
- Color-coded file system events (create, modify, delete, move)
- Structured logging with icons and color formatting
- Clean, segmented display of streaming responses

### MCP Server Integration Support
Added support for Model Context Protocol (MCP) servers through the `mcp_server_file` field in drop zone configuration. This allows integration with external tools and services. The file path is passed directly to ClaudeCodeOptions, which handles loading the configuration.

### PromptArgs Type System
Introduced a structured `PromptArgs` Pydantic model to manage prompt-related arguments cleanly:
- `reusable_prompt`: Path to the reusable prompt file
- `file_path`: Path to the file being processed  
- `model`: Optional model specification
- `mcp_server_file`: Optional path to MCP server configuration file

### Configuration Schema Updates
The `DropZone` model now includes:
- `mcp_server_file`: Optional path to MCP server configuration file (JSON or YAML)

Example configuration:
```yaml
drop_zones:
  - name: "Advanced Zone"
    file_patterns: ["*.py"]
    reusable_prompt: ".claude/commands/analyze.md"
    zone_dirs: ["src/"]
    events: ["created", "modified"]
    agent: "claude_code"
    model: "sonnet"
    mcp_server_file: ".mcp/servers.json"  # New field for MCP integration
```

### MCP Server File Format
MCP server files can be in JSON or YAML format. The ClaudeCodeOptions class handles loading these files automatically:

```json
{
  "database": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-postgres"],
    "env": {"DATABASE_URL": "postgresql://localhost:5432/mydb"}
  }
}
```

### Implementation Notes
- The `mcp_server_file` path is passed directly to `ClaudeCodeOptions` as the `mcp_servers` parameter
- ClaudeCodeOptions natively supports file paths (`dict | str | Path`) for MCP configurations
- No manual file parsing is required - the SDK handles JSON/YAML loading internally

### Visual Output Features
The application now uses Rich console for enhanced visual feedback:

#### File System Events
- ✨ Green for file creation
- 📝 Yellow for file modification  
- 🗑️ Red for file deletion
- 📦 Blue for file moves

#### Claude Code Response Panel
- Displays responses in a styled panel with cyan border
- Shows "🤖 Claude Code" as the title
- Includes the processing file name as subtitle
- Live streaming updates as the response arrives
- Clean padding and formatting for readability

#### Status Messages
- 🚀 Startup banner with application name
- ✅ Green confirmation for started monitors
- 🎯 Cyan summary of active observers
- 🛑 Yellow stop notifications
- ⚡ Keyboard interrupt handling