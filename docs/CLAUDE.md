# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Agentic Drop Zone system - a file monitoring and processing application that automatically triggers Claude Code agents via AWS Bedrock when files are dropped into configured directories. The system uses Python Watchdog for file monitoring and executes custom workflows with full tool access (`bypassPermissions` mode) based on file patterns.

## Core Architecture

### Main Components

- **`sfs_agentic_drop_zone.py`**: Single-file Python script using uv for dependency management
- **`drops.yaml`**: Configuration file defining drop zones, file patterns, and agent workflows
- **`.claude/commands/`**: Reusable prompt templates for different workflows
- **Claude Code Agent**: Single agent implementation via AWS Bedrock with full tool access

### Key Dependencies

The project uses uv for Python dependency management with these core libraries:
- `claude-code-sdk`: Native Python SDK for Claude Code integration
- `watchdog`: File system monitoring
- `pyyaml`: Configuration parsing
- `rich`: Console output formatting
- `pydantic`: Data validation and settings management

### System Flow

1. **File Monitoring**: Python Watchdog Observer monitors configured directories for file events
2. **Pattern Matching**: Incoming files are matched against configured patterns in `drops.yaml` using Pydantic validation
3. **Prompt Processing**: Matched files trigger prompt template loading with variable substitution (`[[FILE_PATH]]` → actual path)
4. **Agent Execution**: ClaudeSDKClient with `bypassPermissions: true` processes the prompt via AWS Bedrock
5. **Tool Access**: Claude Code gets full tool access (Bash, Read, Write, Glob, Grep) for autonomous workflow execution
6. **Response Streaming**: Real-time output display using Rich streaming panels with progress indicators

## Logging & Monitoring System

The system includes enhanced logging, error handling, and monitoring capabilities. For complete details see `docs/enhanced_logging_and_monitoring.md`.

### Quick Reference
- **Log files**: `logs/agentic_drop_zone.log`, `logs/errors.log`, `logs/workflows.log`
- **Health checks**: `curl http://localhost:8080/health/detailed`
- **Workflow states**: PENDING → RUNNING → COMPLETED/FAILED/TIMEOUT
- **Notifications**: Configure `NOTIFICATION_WEBHOOK_URL` for real-time error alerts

## Development Commands

### Running the Application

#### With AWS Bedrock:
```bash
# Install and run with uv (using .env file)
uv run sfs_agentic_drop_zone.py

# Or with inline environment variables
CLAUDE_CODE_USE_BEDROCK=1 AWS_BEARER_TOKEN_BEDROCK="your-key" AWS_REGION="us-east-1" uv run sfs_agentic_drop_zone.py
```

#### With Direct Anthropic API:
```bash
# Install and run with uv
uv run sfs_agentic_drop_zone.py

# Run with environment variables
ANTHROPIC_API_KEY="your-key" uv run sfs_agentic_drop_zone.py
```

### Environment Setup

#### Option 1: AWS Bedrock (Recommended for Enterprise)
```bash
# Copy sample environment file
cp .env.sample .env

# AWS Bedrock Configuration
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_BEARER_TOKEN_BEDROCK="your-api-key"
export AWS_REGION="your-aws-region"
export ANTHROPIC_MODEL="us.anthropic.claude-sonnet-4-20250514-v1:0"
export CLAUDE_CODE_PATH="claude"  # defaults to 'claude'

# Optional for Google Cloud image workflows
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export GOOGLE_CLOUD_PROJECT="gcp-rnd-chatbot-1783-poc-ee44"
export GOOGLE_CLOUD_REGION="us-central1"

# Alternative: Replicate API for image workflows
# export REPLICATE_API_TOKEN="your-replicate-token"
```

#### Option 2: Direct Anthropic API
```bash
# Copy sample environment file
cp .env.sample .env

# Direct Anthropic API Configuration
export ANTHROPIC_API_KEY="your-claude-api-key"
export CLAUDE_CODE_PATH="claude"  # defaults to 'claude'

# Optional for Google Cloud image workflows
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export GOOGLE_CLOUD_PROJECT="gcp-rnd-chatbot-1783-poc-ee44"
export GOOGLE_CLOUD_REGION="us-central1"

# Alternative: Replicate API for image workflows
# export REPLICATE_API_TOKEN="your-replicate-token"
```

### MCP Server Configuration
```bash
# Copy sample MCP configuration
cp .mcp.json.sample .mcp.json

# Edit with your API keys for MCP tools
```

## Configuration System

### Drop Zone Structure (`drops.yaml`)
Each drop zone configuration includes:
- `name`: Display name for the zone
- `file_patterns`: Array of file patterns to monitor (e.g., `["*.txt", "*.md"]`)
- `reusable_prompt`: Path to prompt template file
- `zone_dirs`: Directories to monitor
- `events`: File system events to trigger on (`["created", "modified", "deleted", "moved"]`)
- `agent`: Agent type (`claude_code`, `gemini_cli`, `codex_cli`)
- `model`: Model specification (e.g., `sonnet`, `gemini-2.5-pro`)
- `color`: Console output color
- `mcp_server_file`: Optional MCP configuration file
- `create_zone_dir_if_not_exists`: Auto-create directories

### Prompt Template System
Prompt templates use variable substitution:
- `[[FILE_PATH]]`: Replaced with the actual file path that triggered the event
- Templates include YAML frontmatter with metadata
- Support for workflow-specific variables and instructions

## Agent Integration

### Claude Code SDK Integration
- Uses `ClaudeSDKClient` with streaming responses
- Runs in `bypassPermissions` mode for full tool access
- Supports MCP server integration for extended capabilities
- Rich panel output with real-time streaming

### Gemini CLI Integration
- Subprocess execution with `--yolo` and `--sandbox` flags
- Line-by-line streaming output (CLI limitation)
- Alternative model support outside Anthropic ecosystem

### Agent Selection Strategy
- Claude Code: Best for complex tasks requiring tool use and SOTA performance
- Gemini CLI: Quick tasks and alternative model access
- Codex CLI: Planned but not yet implemented

## Pre-configured Workflows

The system includes several ready-to-use workflows:

### Google Image Generation (`google_generate_images_zone/`)
- **Trigger**: `*.txt`, `*.md` files
- **Requirements**: `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_CLOUD_PROJECT`
- **Function**: Generate images from text prompts using Google Cloud Vertex AI Imagen

### Replicate Image Generation (`replicate_generate_images_zone/`)
- **Trigger**: `*.txt`, `*.md` files
- **Requirements**: `REPLICATE_API_TOKEN`
- **Function**: Generate images from text prompts using Replicate AI models (alternative)

### Image Editing (`edit_images_zone/`)
- **Trigger**: `*.txt`, `*.md`, `*.json` files
- **Requirements**: `REPLICATE_API_TOKEN`
- **Function**: Edit existing images using AI models

### Training Data Generation (`training_data_zone/`)
- **Trigger**: `*.csv`, `*.jsonl` files
- **Function**: Analyze patterns and generate synthetic training data

### Morning Debrief (`morning_debrief_zone/`)
- **Trigger**: Audio files (`*.mp3`, `*.wav`, `*.m4a`, etc.)
- **Requirements**: `openai-whisper` (`uv tool install openai-whisper`)
- **Function**: Transcribe and analyze morning debrief recordings

### Finance Categorization (`finance_zone/`)
- **Trigger**: `*.csv` files
- **Function**: Categorize financial transactions

## Testing Workflows

```bash
# Test echo workflow
cp example_input_files/echo.txt agentic_drop_zone/echo_zone/

# Test Google image generation
cp example_input_files/cats.txt agentic_drop_zone/google_generate_images_zone/

# Or test Replicate image generation (alternative)
cp example_input_files/cats.txt agentic_drop_zone/replicate_generate_images_zone/

# Test training data generation
cp example_input_files/sample_data.csv agentic_drop_zone/training_data_zone/
```

## Security Considerations

- Agents run with dangerous execution permissions (`bypassPermissions` for Claude Code, `--yolo` for Gemini CLI)
- System provides complete control over the local environment
- Sandboxing available for Gemini CLI with `--sandbox` flag
- Users assume full responsibility for agent actions

## File Organization

```
.
├── sfs_agentic_drop_zone.py    # Main application
├── drops.yaml                   # Zone configurations
├── .claude/commands/           # Prompt templates
├── agentic_drop_zone/          # Drop zone directories
├── example_input_files/        # Test files
├── ai_docs/                    # AI-related documentation
└── specs/                      # Technical specifications
```

## Extending the System

### Adding New Workflows
1. Create prompt template in `.claude/commands/`
2. Add drop zone configuration to `drops.yaml`
3. Test with sample files in `example_input_files/`

### Adding New Agent Types
1. Implement agent class in `sfs_agentic_drop_zone.py`
2. Add to `AgentType` enum
3. Update configuration validation
4. Add subprocess or SDK integration

### Prompt Template Best Practices
- Use YAML frontmatter for metadata
- Define clear variable substitution patterns
- Include workflow-specific instructions
- Specify required tools and permissions