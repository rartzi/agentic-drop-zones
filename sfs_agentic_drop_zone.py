#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "claude-code-sdk",
#     "pydantic",
#     "watchdog",
#     "pyyaml",
#     "python-dotenv",
#     "rich",
#     "structlog",
#     "httpx",
#     "fastapi",
#     "uvicorn",
# ]
# ///

"""Agentic Drop Zone - File monitoring and processing system."""

import asyncio
import json
import logging
import os
import signal
import time
import yaml
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Literal, Dict, List
import structlog
import httpx

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileSystemEvent,
    EVENT_TYPE_CREATED,
    EVENT_TYPE_MODIFIED,
    EVENT_TYPE_DELETED,
    EVENT_TYPE_MOVED,
)
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

# Load environment variables
load_dotenv()

# Constants
FILE_PATH_PLACEHOLDER = "[[FILE_PATH]]"


# ===========================
# ENHANCED LOGGING SYSTEM
# ===========================

def setup_structured_logging():
    """Configure structured logging with JSON output and different levels."""

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure standard logging to write to files first
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Main application log
    main_handler = logging.FileHandler(logs_dir / "agentic_drop_zone.log")
    main_handler.setFormatter(logging.Formatter(log_format))
    main_handler.setLevel(logging.INFO)

    # Error log (ERROR and CRITICAL only)
    error_handler = logging.FileHandler(logs_dir / "errors.log")
    error_handler.setFormatter(logging.Formatter(log_format))
    error_handler.setLevel(logging.ERROR)

    # Workflow log (detailed workflow processing)
    workflow_handler = logging.FileHandler(logs_dir / "workflows.log")
    workflow_handler.setFormatter(logging.Formatter(log_format))
    workflow_handler.setLevel(logging.DEBUG)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(main_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(workflow_handler)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger("agentic_drop_zone")


# ===========================
# ERROR NOTIFICATION SYSTEM
# ===========================

class NotificationLevel(str, Enum):
    """Notification severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationConfig(BaseModel):
    """Configuration for notification webhooks."""
    webhook_url: Optional[str] = Field(default=None, description="Webhook URL for notifications")
    enabled: bool = Field(default=True, description="Whether notifications are enabled")
    min_level: NotificationLevel = Field(default=NotificationLevel.ERROR, description="Minimum level to send notifications")
    timeout: int = Field(default=10, description="Webhook request timeout in seconds")


class NotificationService:
    """Service for sending notifications via webhooks."""

    def __init__(self, config: NotificationConfig):
        self.config = config
        self.logger = structlog.get_logger("notifications")

    async def send_notification(
        self,
        level: NotificationLevel,
        title: str,
        message: str,
        context: Dict[str, Any] = None
    ) -> bool:
        """Send a notification if conditions are met."""

        if not self.config.enabled or not self.config.webhook_url:
            return False

        # Check if level meets minimum threshold
        level_order = {
            NotificationLevel.INFO: 0,
            NotificationLevel.WARNING: 1,
            NotificationLevel.ERROR: 2,
            NotificationLevel.CRITICAL: 3
        }

        if level_order[level] < level_order[self.config.min_level]:
            return False

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.value,
            "title": title,
            "message": message,
            "system": "agentic-drop-zone",
            "context": context or {}
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    self.config.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

                self.logger.info(
                    "Notification sent successfully",
                    level=level.value,
                    title=title,
                    status_code=response.status_code
                )
                return True

        except Exception as e:
            self.logger.error(
                "Failed to send notification",
                level=level.value,
                title=title,
                error=str(e)
            )
            return False


# ===========================
# WORKFLOW MONITORING SYSTEM
# ===========================

class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class WorkflowMetrics(BaseModel):
    """Metrics for workflow execution."""
    workflow_id: str
    zone_name: str
    file_path: str
    agent: str
    model: str
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None


class WorkflowMonitor:
    """Monitor and track workflow execution."""

    def __init__(self, notification_service: NotificationService):
        self.active_workflows: Dict[str, WorkflowMetrics] = {}
        self.completed_workflows: List[WorkflowMetrics] = []
        self.notification_service = notification_service
        self.logger = structlog.get_logger("workflow_monitor")
        self.timeout_seconds = 300  # 5 minutes default timeout

    def start_workflow(
        self,
        workflow_id: str,
        zone_name: str,
        file_path: str,
        agent: str,
        model: str
    ) -> WorkflowMetrics:
        """Start tracking a new workflow."""

        metrics = WorkflowMetrics(
            workflow_id=workflow_id,
            zone_name=zone_name,
            file_path=file_path,
            agent=agent,
            model=model,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.now(timezone.utc)
        )

        self.active_workflows[workflow_id] = metrics

        self.logger.info(
            "Workflow started",
            workflow_id=workflow_id,
            zone_name=zone_name,
            file_path=file_path,
            agent=agent,
            model=model
        )

        return metrics

    async def complete_workflow(
        self,
        workflow_id: str,
        status: WorkflowStatus,
        error_message: Optional[str] = None
    ) -> Optional[WorkflowMetrics]:
        """Mark a workflow as completed."""

        if workflow_id not in self.active_workflows:
            self.logger.warning("Attempted to complete unknown workflow", workflow_id=workflow_id)
            return None

        metrics = self.active_workflows.pop(workflow_id)
        metrics.end_time = datetime.now(timezone.utc)
        metrics.duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()
        metrics.status = status
        metrics.error_message = error_message

        self.completed_workflows.append(metrics)

        # Send notifications for failures
        if status == WorkflowStatus.FAILED:
            await self.notification_service.send_notification(
                NotificationLevel.ERROR,
                f"Workflow Failed: {metrics.zone_name}",
                f"File: {Path(metrics.file_path).name}\nAgent: {metrics.agent}\nError: {error_message}",
                context=metrics.dict()
            )
        elif status == WorkflowStatus.TIMEOUT:
            await self.notification_service.send_notification(
                NotificationLevel.CRITICAL,
                f"Workflow Timeout: {metrics.zone_name}",
                f"File: {Path(metrics.file_path).name}\nAgent: {metrics.agent}\nDuration: {metrics.duration_seconds:.1f}s",
                context=metrics.dict()
            )

        self.logger.info(
            "Workflow completed",
            workflow_id=workflow_id,
            status=status.value,
            duration_seconds=metrics.duration_seconds,
            error_message=error_message
        )

        return metrics

    async def check_timeouts(self) -> List[str]:
        """Check for timed out workflows and mark them as such."""
        timed_out = []
        current_time = datetime.now(timezone.utc)

        for workflow_id, metrics in list(self.active_workflows.items()):
            duration = (current_time - metrics.start_time).total_seconds()
            if duration > self.timeout_seconds:
                await self.complete_workflow(workflow_id, WorkflowStatus.TIMEOUT)
                timed_out.append(workflow_id)

        return timed_out

    def get_active_count(self) -> int:
        """Get number of active workflows."""
        return len(self.active_workflows)

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the monitoring system."""
        return {
            "active_workflows": len(self.active_workflows),
            "completed_workflows": len(self.completed_workflows),
            "oldest_active_workflow": (
                min(self.active_workflows.values(), key=lambda w: w.start_time).start_time.isoformat()
                if self.active_workflows else None
            ),
            "system_status": "healthy"
        }


# Initialize global instances
logger = setup_structured_logging()
notification_config = NotificationConfig(
    webhook_url=os.getenv("NOTIFICATION_WEBHOOK_URL"),
    min_level=NotificationLevel(os.getenv("NOTIFICATION_MIN_LEVEL", "error"))
)
notification_service = NotificationService(notification_config)
workflow_monitor = WorkflowMonitor(notification_service)


# Environment variable checks
def check_environment_variables():
    """Check for required environment variables at startup."""
    # Check if using Bedrock or direct Anthropic API
    use_bedrock = os.getenv("CLAUDE_CODE_USE_BEDROCK", "0") == "1"

    if use_bedrock:
        required_vars = {
            "AWS_REGION": "Required AWS region for Bedrock",
            "CLAUDE_CODE_PATH": "Required path to Claude CLI executable",
        }
        # Note: AWS_BEARER_TOKEN_BEDROCK is optional if using ~/.aws/credentials
    else:
        required_vars = {
            "ANTHROPIC_API_KEY": "Required for Claude Code SDK authentication",
            "CLAUDE_CODE_PATH": "Required path to Claude CLI executable",
        }

    optional_vars = {
        "REPLICATE_API_TOKEN": "Optional - needed for Replicate image generation/editing",
        "GOOGLE_APPLICATION_CREDENTIALS": "Optional - needed for Google Cloud image generation",
        "GOOGLE_CLOUD_PROJECT": "Optional - needed for Google Cloud image generation"
    }

    missing_required = []

    # Check required variables
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_required.append(f"  - {var}: {description}")

    # Display missing required variables
    if missing_required:
        console.print("[bold red]❌ Missing required environment variables:[/bold red]")
        for item in missing_required:
            console.print(f"[red]{item}[/red]")
        console.print(
            "\n[yellow]Please set these in your .env file or environment[/yellow]"
        )
        raise EnvironmentError("Missing required environment variables")

    # Check optional variables and display warnings
    missing_optional = []
    for var, description in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"  - {var}: {description}")

    if missing_optional:
        console.print("[yellow]⚠️  Optional environment variables not set:[/yellow]")
        for item in missing_optional:
            console.print(f"[dim]{item}[/dim]")
        console.print()

    api_mode = "AWS Bedrock" if use_bedrock else "Anthropic API"
    console.print(f"[green]✅ All required environment variables are set for {api_mode}[/green]")


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()


class EventType(str, Enum):
    """Supported file system event types."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


class AgentType(str, Enum):
    """Supported agent types."""

    CLAUDE_CODE = "claude_code"
    GEMINI_CLI = "gemini_cli"
    CODEX_CLI = "codex_cli"


class PromptArgs(BaseModel):
    """Arguments for prompt processing."""

    reusable_prompt: str = Field(description="Path to the reusable prompt file")
    file_path: str = Field(description="Path to the file being processed")
    model: Optional[str] = Field(
        default=None, description="Model to use for processing"
    )
    mcp_server_file: Optional[str] = Field(
        default=None, description="Path to MCP server configuration file (JSON or YAML)"
    )
    zone_name: Optional[str] = Field(default=None, description="Name of the drop zone")
    zone_color: Optional[str] = Field(
        default="cyan", description="Color for the drop zone"
    )


class DropZone(BaseModel):
    """Configuration for a single drop zone."""

    name: str = Field(description="Name of the drop zone")
    file_patterns: list[str] = Field(description="File patterns to watch (e.g., *.txt)")
    reusable_prompt: str = Field(
        description="Path to the reusable prompt file (e.g., .claude/commands/echo.md)"
    )
    zone_dirs: list[str] = Field(
        description="List of directories to monitor (supports * wildcard)"
    )
    events: list[EventType] = Field(
        default=[EventType.CREATED], description="Event types to respond to"
    )
    agent: AgentType = Field(
        default=AgentType.CLAUDE_CODE, description="Agent type to use for processing"
    )
    model: Optional[str] = Field(
        default="sonnet",
        description="Model to use for Claude Code (e.g., 'sonnet', 'opus', 'haiku')",
    )
    mcp_server_file: Optional[str] = Field(
        default=None, description="Path to MCP server configuration file (JSON or YAML)"
    )
    color: Optional[str] = Field(
        default="cyan",
        description="Color for console output (e.g., 'red', 'blue', 'green', 'cyan', 'yellow', 'magenta')",
    )
    create_zone_dir_if_not_exists: bool = Field(
        default=False,
        description="Create zone directory if it doesn't exist (non-glob patterns only)",
    )

    @field_validator("zone_dirs")
    @classmethod
    def validate_zone_dirs(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("zone_dirs must contain at least one directory")
        return v

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[EventType]) -> list[EventType]:
        if not v:
            raise ValueError("events must contain at least one event type")
        return v


class DropsConfig(BaseModel):
    """Root configuration for all drop zones."""

    drop_zones: list[DropZone] = Field(description="List of configured drop zones")


class Agents:
    """Agent implementations for processing drop zone files."""

    @staticmethod
    def build_prompt(reusable_prompt_path: str, file_path: str) -> str:
        """Build the full prompt by loading from file and replacing variables.

        Args:
            reusable_prompt_path: Path to the prompt file
            file_path: Path to the dropped file being processed

        Returns:
            The constructed prompt with variables replaced

        Raises:
            FileNotFoundError: If the prompt file doesn't exist
            Exception: If unable to read the prompt file
        """
        prompt_path = Path(reusable_prompt_path)

        # Ensure prompt file exists
        if not prompt_path.exists():
            error_msg = f"Reusable prompt file not found: {reusable_prompt_path}"
            console.print(f"[bold red]❌ {error_msg}[/bold red]")
            raise FileNotFoundError(error_msg)

        if not prompt_path.is_file():
            error_msg = f"Reusable prompt path is not a file: {reusable_prompt_path}"
            console.print(f"[bold red]❌ {error_msg}[/bold red]")
            raise ValueError(error_msg)

        # Load prompt from file
        console.print(f"[dim]   Loading prompt: {reusable_prompt_path}[/dim]")
        try:
            prompt_content = prompt_path.read_text()
        except Exception as e:
            error_msg = f"Failed to read prompt file {reusable_prompt_path}: {e}"
            console.print(f"[bold red]❌ {error_msg}[/bold red]")
            raise Exception(error_msg) from e

        # Replace FILE_PATH_PLACEHOLDER with actual file path
        if FILE_PATH_PLACEHOLDER in prompt_content:
            prompt_content = prompt_content.replace(FILE_PATH_PLACEHOLDER, file_path)

        return prompt_content

    @staticmethod
    async def prompt_claude_code(args: PromptArgs) -> None:
        """Process a file using Claude Code SDK."""
        # Build full prompt using the build_prompt method
        full_prompt = Agents.build_prompt(args.reusable_prompt, args.file_path)

        console.print(f"[cyan]ℹ️  Processing prompt with Claude Code...[/cyan]")
        if args.model:
            console.print(f"[dim]   Model: {args.model}[/dim]")

        # Get CLI path from environment or use default
        cli_path = os.getenv("CLAUDE_CODE_PATH", "claude")

        # If a custom path is set, update PATH environment variable
        if cli_path != "claude":
            # Extract directory from the CLI path
            cli_dir = os.path.dirname(cli_path) if os.path.dirname(cli_path) else "."
            current_path = os.environ.get("PATH", "")
            if cli_dir not in current_path:
                os.environ["PATH"] = f"{cli_dir}:{current_path}"

        # Create options with bypassPermissions mode and optional model
        options_dict = {
            "permission_mode": "bypassPermissions"  # Bypass all permission prompts
        }

        # Add model if specified
        if args.model:
            # Try the model value as-is first, if it fails, try with claude- prefix
            options_dict["model"] = args.model

        # Add MCP server file if specified
        if args.mcp_server_file:
            # Claude SDK accepts file paths directly and will handle loading
            options_dict["mcp_servers"] = args.mcp_server_file
            console.print(f"[dim]   MCP config: {args.mcp_server_file}[/dim]")

        options = ClaudeCodeOptions(**options_dict)

        # Minimal Claude Code setup - let errors propagate
        async with ClaudeSDKClient(options=options) as client:
            await client.query(full_prompt)

            # Stream response - output panels as content arrives
            file_name = Path(args.file_path).name
            has_response = False
            zone_workflow = (
                f"{args.zone_name} Workflow" if args.zone_name else "Workflow"
            )
            panel_color = args.zone_color or "cyan"

            async for message in client.receive_response():
                if hasattr(message, "content"):
                    for block in message.content:
                        if hasattr(block, "text") and block.text.strip():
                            has_response = True
                            # Output each text block in its own panel
                            console.print(
                                Panel(
                                    Text(block.text),
                                    title=f"[bold {panel_color}]🤖 Claude Code • {zone_workflow}[/bold {panel_color}]",
                                    subtitle=f"[dim]{file_name}[/dim]",
                                    border_style=panel_color,
                                    expand=False,
                                    padding=(1, 2),
                                )
                            )

            # If no response was received
            if not has_response:
                console.print(
                    Panel(
                        Text("[yellow]No response received[/yellow]"),
                        title=f"[bold yellow]🤖 Claude Code • {zone_workflow}[/bold yellow]",
                        subtitle=f"[dim]{file_name}[/dim]",
                        border_style="yellow",
                        expand=False,
                        padding=(1, 2),
                    )
                )

            console.print()

    @staticmethod
    async def prompt_gemini_cli(args: PromptArgs) -> None:
        """Process a file using Gemini CLI."""
        # Build full prompt using the build_prompt method
        full_prompt = Agents.build_prompt(args.reusable_prompt, args.file_path)

        console.print(f"[green]ℹ️  Processing prompt with Gemini CLI...[/green]")
        if args.model:
            console.print(f"[dim]   Model: {args.model}[/dim]")

        # Get CLI path from environment or use default
        gemini_path = os.getenv("GEMINI_CLI_PATH", "gemini")

        # Build command with flags
        cmd = [
            gemini_path,
            "--yolo",      # Auto-approve all tool calls
            "--sandbox",   # Enable sandboxing by default
            "-m", args.model or "gemini-2.5-pro",  # Model
            "-p", full_prompt  # Non-interactive prompt
        ]

        console.print(f"[dim]   Command: {' '.join(cmd[:4])}...[/dim]")

        try:
            # Create subprocess with asyncio
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()  # Pass environment variables
            )

            # Prepare for streaming display
            file_name = Path(args.file_path).name
            zone_workflow = (
                f"{args.zone_name} Workflow" if args.zone_name else "Workflow"
            )
            panel_color = args.zone_color or "green"
            has_output = False

            async def read_stream(stream, is_stderr=False):
                """Read and display stream output line by line."""
                nonlocal has_output
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    
                    decoded = line.decode('utf-8', errors='replace').rstrip()
                    if decoded:  # Only process non-empty lines
                        has_output = True
                        # Print each line in its own panel
                        console.print(
                            Panel(
                                Text(decoded),
                                title=f"[bold {panel_color}]🤖 Gemini CLI • {zone_workflow}[/bold {panel_color}]",
                                subtitle=f"[dim]{file_name}[/dim]",
                                border_style=panel_color,
                                expand=False,
                                padding=(1, 2),
                            )
                        )

            # Handle both streams concurrently
            await asyncio.gather(
                read_stream(process.stdout, is_stderr=False),
                read_stream(process.stderr, is_stderr=True)
            )

            # Wait for process to complete
            return_code = await process.wait()
            
            # Print completion status if needed
            if return_code != 0:
                console.print(
                    f"\n[yellow]⚠️ Process exited with code {return_code}[/yellow]"
                )
            
            # If no output was received, show a message
            if not has_output:
                console.print(
                    Panel(
                        "[yellow]No output received[/yellow]",
                        title=f"[bold yellow]🤖 Gemini CLI • {zone_workflow}[/bold yellow]",
                        subtitle=f"[dim]{file_name}[/dim]",
                        border_style="yellow",
                        expand=False,
                        padding=(1, 2),
                    )
                )

        except FileNotFoundError:
            console.print(
                f"[bold red]❌ Gemini CLI not found at '{gemini_path}'[/bold red]"
            )
            console.print(
                "[yellow]Please install Gemini CLI: npm install -g @google/gemini-cli[/yellow]"
            )
            console.print(
                "[dim]Or set GEMINI_CLI_PATH environment variable to the correct path[/dim]"
            )
        except Exception as e:
            console.print(f"[bold red]❌ Error running Gemini CLI: {e}[/bold red]")

        console.print()

    @staticmethod
    async def prompt_codex_cli(args: PromptArgs) -> None:
        """Process a file using Codex CLI."""
        # Build full prompt using the build_prompt method
        full_prompt = Agents.build_prompt(args.reusable_prompt, args.file_path)

        # TODO: Implement Codex CLI integration
        raise NotImplementedError("Codex CLI agent not yet implemented")

    @staticmethod
    async def process_with_agent(agent: AgentType, args: PromptArgs) -> None:
        """Route to appropriate agent based on type with enhanced monitoring."""
        import uuid

        # Generate unique workflow ID
        workflow_id = str(uuid.uuid4())[:8]

        # Start workflow monitoring
        workflow_monitor.start_workflow(
            workflow_id=workflow_id,
            zone_name=args.zone_name or "unknown",
            file_path=args.file_path,
            agent=agent.value,
            model=args.model or "default"
        )

        logger.info(f"Starting agent processing [ID: {workflow_id}]: {args.file_path} with {agent.value} ({args.model}) in {args.zone_name}")

        try:
            if agent == AgentType.CLAUDE_CODE:
                await Agents.prompt_claude_code(args)
            elif agent == AgentType.GEMINI_CLI:
                await Agents.prompt_gemini_cli(args)
            elif agent == AgentType.CODEX_CLI:
                await Agents.prompt_codex_cli(args)
            else:
                raise ValueError(f"Unknown agent type: {agent}")

            # Mark workflow as completed successfully
            await workflow_monitor.complete_workflow(workflow_id, WorkflowStatus.COMPLETED)

            logger.info(f"Agent processing completed successfully [ID: {workflow_id}]: {args.file_path}")

        except Exception as e:
            error_msg = str(e)

            # Mark workflow as failed
            await workflow_monitor.complete_workflow(
                workflow_id,
                WorkflowStatus.FAILED,
                error_message=error_msg
            )

            logger.error(f"Agent processing failed [ID: {workflow_id}]: {args.file_path} with {agent.value}: {error_msg}", exc_info=True)

            console.print(f"[bold red]❌ Agent processing failed: {e}[/bold red]")

            # Send error notification
            await notification_service.send_notification(
                NotificationLevel.ERROR,
                f"Agent Processing Failed: {args.zone_name}",
                f"File: {Path(args.file_path).name}\nAgent: {agent.value}\nError: {error_msg}",
                context={
                    "workflow_id": workflow_id,
                    "agent": agent.value,
                    "file_path": args.file_path,
                    "zone_name": args.zone_name
                }
            )


class DropZoneHandler(FileSystemEventHandler):
    """Handle file system events in the drop zone."""

    def __init__(self, drop_zone: DropZone):
        self.drop_zone = drop_zone
        super().__init__()

    def _should_process_event(self, event_type: str) -> bool:
        """Check if this event type should be processed."""
        event_map = {
            EVENT_TYPE_CREATED: EventType.CREATED,
            EVENT_TYPE_MODIFIED: EventType.MODIFIED,
            EVENT_TYPE_DELETED: EventType.DELETED,
            EVENT_TYPE_MOVED: EventType.MOVED,
        }
        return event_map.get(event_type) in self.drop_zone.events

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if not event.is_directory and self._should_process_event(EVENT_TYPE_CREATED):
            console.print(f"[green]✨ File created: {event.src_path}[/green]")
            self.process_file(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory and self._should_process_event(EVENT_TYPE_MODIFIED):
            console.print(f"[yellow]📝 File modified: {event.src_path}[/yellow]")
            self.process_file(event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if not event.is_directory and self._should_process_event(EVENT_TYPE_DELETED):
            console.print(f"[red]🗑️  File deleted: {event.src_path}[/red]")
            self.process_file(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move events."""
        if not event.is_directory and self._should_process_event(EVENT_TYPE_MOVED):
            console.print(
                f"[blue]📦 File moved: {event.src_path} -> {event.dest_path}[/blue]"
            )
            self.process_file(
                event.dest_path if hasattr(event, "dest_path") else event.src_path
            )

    def process_file(self, file_path: str) -> None:
        """Process a file that has been added or modified with enhanced logging."""
        path = Path(file_path)

        # Check if file matches any of the configured patterns
        if not any(path.match(pattern) for pattern in self.drop_zone.file_patterns):
            logger.debug(f"File ignored - pattern mismatch: {file_path} in {self.drop_zone.name}")
            return

        # Log file processing start
        file_size = path.stat().st_size if path.exists() else None
        logger.info(f"File processing started: {file_path} in {self.drop_zone.name} (agent: {self.drop_zone.agent.value}, size: {file_size} bytes)")

        zone_color = self.drop_zone.color or "green"
        console.print(
            f"\n[bold {zone_color}]📁 Drop Zone: {self.drop_zone.name}[/bold {zone_color}]"
        )
        console.print(f"[yellow]   File: {file_path}[/yellow]")
        console.print(f"[dim]   Agent: {self.drop_zone.agent}[/dim]")
        console.print(f"[dim]   Prompt: {self.drop_zone.reusable_prompt}[/dim]")
        if self.drop_zone.model:
            console.print(f"[dim]   Model: {self.drop_zone.model}[/dim]")
        if self.drop_zone.mcp_server_file:
            console.print(f"[dim]   MCP: {self.drop_zone.mcp_server_file}[/dim]")

        # Create PromptArgs
        prompt_args = PromptArgs(
            reusable_prompt=self.drop_zone.reusable_prompt,
            file_path=file_path,
            model=self.drop_zone.model,
            mcp_server_file=self.drop_zone.mcp_server_file,
            zone_name=self.drop_zone.name,
            zone_color=self.drop_zone.color,
        )

        try:
            # Run the agent in a new event loop since watchdog runs in a different thread
            asyncio.run(Agents.process_with_agent(self.drop_zone.agent, prompt_args))

            logger.info(f"File processing delegated to agent: {file_path} in {self.drop_zone.name}")

        except Exception as e:
            logger.error(f"File processing failed in handler: {file_path} in {self.drop_zone.name}: {e}", exc_info=True)
            console.print(f"[bold red]❌ File processing failed: {e}[/bold red]")


class AgenticDropZone:
    """Main application class for the Agentic Drop Zone."""

    def __init__(self, config_file: Path = Path("drops.yaml")):
        self.config_file = config_file
        self.config: Optional[DropsConfig] = None
        self.observers: list[Observer] = []
        self.base_path = Path.cwd()

    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if not self.config_file.exists():
                error_msg = f"Configuration file not found: {self.config_file}"
                console.print(f"[bold red]❌ {error_msg}[/bold red]")
                raise FileNotFoundError(error_msg)

            with open(self.config_file, "r") as f:
                data = yaml.safe_load(f)

            self.config = DropsConfig(**data)
            console.print(
                f"[green]✅ Loaded configuration from {self.config_file}[/green]"
            )
            console.print(
                f"[cyan]   Found {len(self.config.drop_zones)} drop zone(s)[/cyan]"
            )
        except FileNotFoundError:
            raise
        except Exception as e:
            console.print(f"[bold red]❌ Error loading configuration: {e}[/bold red]")
            raise

    def _expand_zone_dirs(self, drop_zone: DropZone) -> list[Path]:
        """Expand zone_dirs patterns to actual directories."""
        expanded_dirs = []

        for zone_dir in drop_zone.zone_dirs:
            if "*" in zone_dir:
                # Simple wildcard support - just use the pattern as-is
                matching_dirs = list(self.base_path.glob(zone_dir))
                # Filter to only directories
                matching_dirs = [d for d in matching_dirs if d.is_dir()]
                if matching_dirs:
                    expanded_dirs.extend(matching_dirs)
                    console.print(
                        f"[dim]   Pattern '{zone_dir}' matched {len(matching_dirs)} directories: {[d.name for d in matching_dirs]}[/dim]"
                    )
                else:
                    console.print(
                        f"[yellow]⚠️  Pattern '{zone_dir}' matched no directories[/yellow]"
                    )
            else:
                # Direct directory path (non-glob)
                dir_path = self.base_path / zone_dir
                if dir_path.exists() and dir_path.is_dir():
                    expanded_dirs.append(dir_path)
                elif not dir_path.exists():
                    # Directory doesn't exist
                    if drop_zone.create_zone_dir_if_not_exists:
                        # Create the directory
                        try:
                            dir_path.mkdir(parents=True, exist_ok=True)
                            console.print(
                                f"[green]✅ Created zone directory: {dir_path}[/green]"
                            )
                            expanded_dirs.append(dir_path)
                        except Exception as e:
                            console.print(
                                f"[bold red]❌ Failed to create directory {dir_path}: {e}[/bold red]"
                            )
                    else:
                        # Log error and ask user to create it
                        console.print(
                            f"[bold red]❌ Zone directory does not exist: {dir_path}[/bold red]"
                        )
                        console.print(
                            f"[yellow]   Please create the directory manually: mkdir -p {dir_path}[/yellow]"
                        )
                        console.print(
                            f"[dim]   Or set 'create_zone_dir_if_not_exists: true' in drops.yaml for zone '{drop_zone.name}'[/dim]"
                        )
                else:
                    console.print(
                        f"[yellow]⚠️  Path exists but is not a directory: {dir_path}[/yellow]"
                    )

        return expanded_dirs

    def start(self) -> None:
        """Start monitoring all configured drop zones."""
        if not self.config:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")

        for drop_zone in self.config.drop_zones:
            # Expand zone_dirs patterns
            zone_paths = self._expand_zone_dirs(drop_zone)

            if not zone_paths:
                console.print(
                    f"[yellow]⚠️  No valid directories found for drop zone '{drop_zone.name}'[/yellow]"
                )
                continue

            # Create observer for each directory
            for zone_path in zone_paths:
                observer = Observer()
                handler = DropZoneHandler(drop_zone)

                # Schedule non-recursive watching
                observer.schedule(handler, str(zone_path), recursive=False)
                observer.start()
                self.observers.append(observer)

                zone_color = drop_zone.color or "green"
                console.print(
                    f"\n[bold {zone_color}]✅ Started monitoring drop zone: {drop_zone.name}[/bold {zone_color}]"
                )
                console.print(f"[cyan]   📂 Path: {zone_path}[/cyan]")
                console.print(f"[dim]   - Patterns: {drop_zone.file_patterns}[/dim]")
                console.print(
                    f"[dim]   - Events: {[e.value for e in drop_zone.events]}[/dim]"
                )
                console.print(f"[dim]   - Prompt: {drop_zone.reusable_prompt}[/dim]")
                if drop_zone.model:
                    console.print(f"[dim]   - Model: {drop_zone.model}[/dim]")
                if drop_zone.mcp_server_file:
                    console.print(f"[dim]   - MCP: {drop_zone.mcp_server_file}[/dim]")

        if self.observers:
            console.print(
                f"\n[bold cyan]🎯 Total observers started: {len(self.observers)}[/bold cyan]"
            )
            console.print("[dim]Press Ctrl+C to stop...[/dim]\n")
        else:
            console.print(
                "[bold red]⚠️ No observers started. Check your configuration.[/bold red]"
            )

    def stop(self) -> None:
        """Stop monitoring all drop zones."""
        for observer in self.observers:
            observer.stop()

        for observer in self.observers:
            observer.join()

        console.print(f"[yellow]🛑 Stopped {len(self.observers)} observer(s)[/yellow]")
        self.observers.clear()

    async def _timeout_monitor_task(self) -> None:
        """Background task to monitor workflow timeouts."""
        while True:
            try:
                timed_out = await workflow_monitor.check_timeouts()
                if timed_out:
                    logger.warning(
                        "Workflows timed out",
                        timed_out_count=len(timed_out),
                        workflow_ids=timed_out
                    )

                # Check every 30 seconds
                await asyncio.sleep(30)
            except Exception as e:
                logger.error("Timeout monitor task failed", error=str(e), exc_info=True)
                await asyncio.sleep(30)

    async def run(self) -> None:
        """Run the drop zone monitor with enhanced monitoring."""
        self.load_config()
        self.start()

        # Start background tasks
        timeout_task = asyncio.create_task(self._timeout_monitor_task())
        health_server_task = asyncio.create_task(self._start_health_server())

        try:
            logger.info("Agentic Drop Zone started successfully")

            # Send startup notification
            await notification_service.send_notification(
                NotificationLevel.INFO,
                "Agentic Drop Zone Started",
                f"Monitoring {len(self.config.drop_zones)} drop zones",
                context={
                    "drop_zones": [zone.name for zone in self.config.drop_zones],
                    "active_workflows": workflow_monitor.get_active_count()
                }
            )

            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]⚡ Received interrupt signal[/yellow]")
            logger.info("Shutdown signal received")
        finally:
            # Cancel background tasks
            timeout_task.cancel()
            health_server_task.cancel()

            # Wait for tasks to complete
            await asyncio.gather(timeout_task, health_server_task, return_exceptions=True)

            self.stop()
            logger.info("Agentic Drop Zone stopped")

    async def _start_health_server(self) -> None:
        """Start the health check HTTP server."""
        try:
            from fastapi import FastAPI
            import uvicorn

            app = FastAPI(
                title="Agentic Drop Zone Health",
                description="Health monitoring for Agentic Drop Zone system",
                version="1.0.0"
            )

            @app.get("/health")
            async def health_check():
                """Basic health check endpoint."""
                return {
                    "status": "healthy",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "system": "agentic-drop-zone"
                }

            @app.get("/health/detailed")
            async def detailed_health():
                """Detailed health check with workflow metrics."""
                health_data = workflow_monitor.get_health_status()
                health_data.update({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "drop_zones": len(self.config.drop_zones) if self.config else 0,
                    "notification_config": {
                        "enabled": notification_config.enabled,
                        "webhook_configured": bool(notification_config.webhook_url),
                        "min_level": notification_config.min_level.value
                    }
                })
                return health_data

            @app.get("/workflows/active")
            async def active_workflows():
                """Get currently active workflows."""
                return {
                    "active_workflows": [
                        {
                            "workflow_id": wf_id,
                            "zone_name": wf.zone_name,
                            "file_path": wf.file_path,
                            "agent": wf.agent,
                            "start_time": wf.start_time.isoformat(),
                            "duration_seconds": (datetime.now(timezone.utc) - wf.start_time).total_seconds()
                        }
                        for wf_id, wf in workflow_monitor.active_workflows.items()
                    ]
                }

            @app.get("/workflows/recent")
            async def recent_workflows():
                """Get recent completed workflows."""
                recent = workflow_monitor.completed_workflows[-10:]  # Last 10
                return {
                    "recent_workflows": [
                        {
                            "workflow_id": wf.workflow_id,
                            "zone_name": wf.zone_name,
                            "file_path": wf.file_path,
                            "agent": wf.agent,
                            "status": wf.status.value,
                            "duration_seconds": wf.duration_seconds,
                            "end_time": wf.end_time.isoformat() if wf.end_time else None
                        }
                        for wf in recent
                    ]
                }

            # Start the server on a separate port
            health_host = os.getenv("HEALTH_SERVER_HOST", "127.0.0.1")
            health_port = int(os.getenv("HEALTH_SERVER_PORT", "8080"))

            config = uvicorn.Config(
                app=app,
                host=health_host,
                port=health_port,
                log_level="warning"  # Reduce uvicorn noise
            )
            server = uvicorn.Server(config)

            logger.info(f"Starting health check server on http://{health_host}:{health_port}")
            console.print(f"[dim]💚 Health check server: http://{health_host}:{health_port}/health[/dim]")

            await server.serve()

        except Exception as e:
            logger.error("Failed to start health server", error=str(e), exc_info=True)


async def main():
    """Main entry point."""
    # Display startup banner
    console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]      🚀 Agentic Drop Zone 🚀[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]\n")

    # Check environment variables
    check_environment_variables()

    drop_zone = AgenticDropZone(config_file=Path("drops.yaml"))
    await drop_zone.run()


if __name__ == "__main__":
    asyncio.run(main())
