# Tools Directory

External tools and utilities used by the Agentic Drop Zone system.

## Available Tools

### `vertex_ai_image_generator.py`
- **Purpose**: Google Cloud Vertex AI image generation
- **Model**: `imagen-4.0-ultra-generate-preview-06-06`
- **Usage**: `python tools/vertex_ai_image_generator.py "prompt" --aspect-ratio 16:9 --output-dir path/`
- **Authentication**: Requires `service-account-key.json` and Google Cloud project setup
- **Called by**: Image generation workflows via bash parallel jobs

## Dependencies

Tools in this directory may require additional dependencies:
- Google Cloud SDK and Vertex AI libraries
- Service account authentication
- Environment variables configured in `.env`

## Integration

These tools are invoked directly by Claude Code agents through the Bash tool, not as MCP servers. They provide specialized functionality beyond the standard Claude Code tool suite.