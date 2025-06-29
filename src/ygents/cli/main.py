"""Main CLI application."""

import asyncio
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

# Suppress deprecation warnings from dependencies
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", category=UserWarning, module="litellm")
# Suppress specific Pydantic warnings
warnings.filterwarnings("ignore", message=".*PydanticDeprecatedSince20.*")
warnings.filterwarnings("ignore", message=".*Support for class-based.*")
warnings.filterwarnings("ignore", message=".*dict.*deprecated.*model_dump.*")
warnings.filterwarnings("ignore", message=".*The `dict` method is deprecated.*")
# Suppress all warnings from specific modules
warnings.filterwarnings("ignore", module="litellm.litellm_core_utils.streaming_handler")
warnings.filterwarnings("ignore", module="pydantic._internal._config")
warnings.filterwarnings("ignore", module="pydantic.main")
# Catch-all for any remaining pydantic warnings
warnings.filterwarnings("ignore", message=".*Pydantic.*")

import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

from ..agent.core import Agent
from ..agent.exceptions import AgentError
from ..config.loader import ConfigLoader
from ..config.models import YgentsConfig

app = typer.Typer(
    name="ygents",
    help="🤖 YGents - LLM powered agent with MCP support",
    add_completion=False,
)

console = Console()


# Display functions for different item types
def create_content_panel(content: str) -> Panel:
    """Create panel for LLM content."""
    return Panel(
        Markdown(content),
        title="🤖 Response",
        border_style="blue",
        padding=(1, 1),
        expand=False,
    )


def create_tool_input_panel(tool_name: str, arguments: Dict[str, Any]) -> Panel:
    """Create panel for tool input."""
    args_str = str(arguments) if arguments else "{}"
    if len(args_str) > 100:
        args_str = args_str[:97] + "..."

    content = f"**Tool:** {tool_name}\n**Arguments:** `{args_str}`"
    return Panel(
        content,
        title="🔧 Tool Input",
        border_style="yellow",
        padding=(1, 1),
        expand=False,
    )


def create_tool_result_panel(tool_name: str, result: Any) -> Panel:
    """Create panel for tool result."""
    result_str = str(result) if result is not None else "None"
    if len(result_str) > 200:
        result_str = result_str[:197] + "..."

    content = f"**Tool:** {tool_name}\n**Result:** `{result_str}`"
    return Panel(
        content,
        title="✅ Tool Result",
        border_style="green",
        padding=(1, 1),
        expand=False,
    )


def create_error_panel(error_content: str, error_type: str = "Error") -> Panel:
    """Create panel for errors."""
    return Panel(
        f"⚠️ {error_content}",
        title=f"❌ {error_type}",
        border_style="red",
        padding=(1, 1),
        expand=False,
    )


def create_status_panel(status_content: str) -> Panel:
    """Create panel for status updates."""
    return Panel(
        f"ℹ️ {status_content}",
        title="📊 Status",
        border_style="cyan",
        padding=(1, 1),
        expand=False,
    )


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        # Try to get version from package metadata
        try:
            import importlib.metadata

            version = importlib.metadata.version("ygents")
        except importlib.metadata.PackageNotFoundError:
            version = "0.1.0-dev"

        console.print(f"ygents version {version}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """YGents - LLM powered agent with MCP support."""
    pass


def load_config(config_path: Optional[str] = None) -> YgentsConfig:
    """Load configuration from file or use defaults."""
    loader = ConfigLoader()

    if config_path:
        config_file = Path(config_path)
        if not config_file.exists():
            console.print(f"❌ Config file not found: {config_path}", style="red")
            raise typer.Exit(1)

        try:
            return loader.load_from_file(config_path)
        except Exception as e:
            console.print(f"❌ Failed to load config: {e}", style="red")
            raise typer.Exit(1)
    else:
        # Use default configuration
        return loader.load_from_dict({"litellm": {"model": "openai/gpt-3.5-turbo"}})


async def run_agent_query(config: YgentsConfig, query: str) -> None:
    """Run a single query with the agent."""
    try:
        async with Agent(config) as agent:
            console.print(f"🤔 **Query:** {query}")
            console.print()

            # Variables for tracking current state
            current_content_parts: List[str] = []
            current_live_content: Optional[Live] = None
            last_item_type: Optional[str] = None

            async for item in agent.run(query):
                if hasattr(item, "type"):
                    if item.type == "content":
                        # Handle streaming content with Live
                        # Clear content only if item type changed
                        if last_item_type != "content":
                            current_content_parts = []

                        current_content_parts.append(item.content)  # type: ignore
                        combined_content = "".join(current_content_parts)

                        if current_live_content is None:
                            # Start new Live display for content
                            content_panel = create_content_panel(combined_content)
                            current_live_content = Live(
                                content_panel, console=console, refresh_per_second=10
                            )
                            current_live_content.start()
                        else:
                            # Update existing Live display
                            content_panel = create_content_panel(combined_content)
                            current_live_content.update(content_panel)

                        last_item_type = "content"

                    elif item.type == "tool_input":
                        # End current Live content if active
                        if current_live_content:
                            current_live_content.stop()
                            current_live_content = None

                        # Display tool input panel immediately
                        panel = create_tool_input_panel(
                            item.tool_name,  # type: ignore
                            item.arguments,  # type: ignore
                        )
                        console.print(panel)

                        last_item_type = "tool_input"

                    elif item.type == "tool_result":
                        # Display tool result panel immediately
                        panel = create_tool_result_panel(
                            item.tool_name,  # type: ignore
                            item.result,  # type: ignore
                        )
                        console.print(panel)

                        last_item_type = "tool_result"

                    elif item.type == "tool_error":
                        # Display tool error panel immediately
                        panel = create_error_panel(item.content, "Tool Error")  # type: ignore
                        console.print(panel)

                        last_item_type = "tool_error"

                    elif item.type == "error":
                        # Display general error panel immediately
                        panel = create_error_panel(item.content, "Error")  # type: ignore
                        console.print(panel)

                        last_item_type = "error"

                    elif item.type == "status":
                        # Display status panel immediately
                        panel = create_status_panel(item.content)  # type: ignore
                        console.print(panel)

                        last_item_type = "status"

                else:
                    # Fallback for backward compatibility
                    if hasattr(item, "content"):
                        # Clear content only if item type changed
                        if last_item_type != "content":
                            current_content_parts = []

                        current_content_parts.append(item.content)
                        combined_content = "".join(current_content_parts)

                        if current_live_content is None:
                            content_panel = create_content_panel(combined_content)
                            current_live_content = Live(
                                content_panel, console=console, refresh_per_second=10
                            )
                            current_live_content.start()
                        else:
                            content_panel = create_content_panel(combined_content)
                            current_live_content.update(content_panel)

                        last_item_type = "content"

            # Clean up Live display if still active
            if current_live_content:
                current_live_content.stop()

    except AgentError as e:
        console.print(f"❌ Agent error: {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def run(
    query: Optional[str] = typer.Option(
        None,
        "--query",
        "-q",
        help="Query to send to the agent. If not provided, starts interactive mode.",
    ),
    config: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Run a single query with the agent or start interactive mode."""
    config_obj = load_config(config)

    if query is None:
        # No query provided, start interactive mode
        console.print(
            Panel(
                "[bold blue]🤖 YGents Interactive Mode[/bold blue]\n"
                "Type your queries and press Enter. Type 'exit', 'quit', or press Ctrl+C to exit.",
                title="Welcome",
                border_style="blue",
            )
        )

        try:
            asyncio.run(interactive_loop(config_obj))
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!", style="blue")
            raise typer.Exit(0)
    else:
        # Query provided, run single query
        try:
            asyncio.run(run_agent_query(config_obj, query))
        except KeyboardInterrupt:
            console.print("\n⏹️ Cancelled by user.", style="yellow")
            raise typer.Exit(130)


@app.command()
def interactive(
    config: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Start interactive mode."""
    config_obj = load_config(config)

    console.print(
        Panel(
            "[bold blue]🤖 YGents Interactive Mode[/bold blue]\n"
            "Type your queries and press Enter. Type 'exit', 'quit', or press Ctrl+C to exit.",
            title="Welcome",
            border_style="blue",
        )
    )

    try:
        asyncio.run(interactive_loop(config_obj))
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="blue")
        raise typer.Exit(0)


async def interactive_loop(config: YgentsConfig) -> None:
    """Run the interactive loop."""
    async with Agent(config) as agent:
        while True:
            try:
                query = Prompt.ask(
                    "\n[bold blue]❓ Your question[/bold blue]", console=console
                )

                if query.lower() in ["exit", "quit", "q"]:
                    console.print("👋 Goodbye!", style="blue")
                    break

                if not query.strip():
                    continue

                console.print()

                # Variables for tracking current state
                current_content_parts: List[str] = []
                current_live_content: Optional[Live] = None
                last_item_type: Optional[str] = None

                async for item in agent.run(query):
                    if hasattr(item, "type"):
                        if item.type == "content":
                            # Handle streaming content with Live
                            # Clear content only if item type changed
                            if last_item_type != "content":
                                current_content_parts = []

                            current_content_parts.append(item.content)  # type: ignore
                            combined_content = "".join(current_content_parts)

                            if current_live_content is None:
                                # Start new Live display for content
                                content_panel = create_content_panel(combined_content)
                                current_live_content = Live(
                                    content_panel,
                                    console=console,
                                    refresh_per_second=10,
                                )
                                current_live_content.start()
                            else:
                                # Update existing Live display
                                content_panel = create_content_panel(combined_content)
                                current_live_content.update(content_panel)

                            last_item_type = "content"

                        elif item.type == "tool_input":
                            # End current Live content if active
                            if current_live_content:
                                current_live_content.stop()
                                current_live_content = None

                            # Display tool input panel immediately
                            panel = create_tool_input_panel(
                                item.tool_name,  # type: ignore
                                item.arguments,  # type: ignore
                            )
                            console.print(panel)

                            last_item_type = "tool_input"

                        elif item.type == "tool_result":
                            # Display tool result panel immediately
                            panel = create_tool_result_panel(
                                item.tool_name,  # type: ignore
                                item.result,  # type: ignore
                            )
                            console.print(panel)

                            last_item_type = "tool_result"

                        elif item.type == "tool_error":
                            # Display tool error panel immediately
                            panel = create_error_panel(item.content, "Tool Error")  # type: ignore
                            console.print(panel)

                            last_item_type = "tool_error"

                        elif item.type == "error":
                            # Display general error panel immediately
                            panel = create_error_panel(item.content, "Error")  # type: ignore
                            console.print(panel)

                            last_item_type = "error"

                        elif item.type == "status":
                            # Display status panel immediately
                            panel = create_status_panel(item.content)  # type: ignore
                            console.print(panel)

                            last_item_type = "status"

                    else:
                        # Fallback for backward compatibility
                        if hasattr(item, "content"):
                            # Clear content only if item type changed
                            if last_item_type != "content":
                                current_content_parts = []

                            current_content_parts.append(item.content)
                            combined_content = "".join(current_content_parts)

                            if current_live_content is None:
                                content_panel = create_content_panel(combined_content)
                                current_live_content = Live(
                                    content_panel,
                                    console=console,
                                    refresh_per_second=10,
                                )
                                current_live_content.start()
                            else:
                                content_panel = create_content_panel(combined_content)
                                current_live_content.update(content_panel)

                            last_item_type = "content"

                # Clean up Live display if still active
                if current_live_content:
                    current_live_content.stop()

            except EOFError:
                console.print("\n👋 Goodbye!", style="blue")
                break
            except KeyboardInterrupt:
                console.print("\n👋 Goodbye!", style="blue")
                break
            except Exception as e:
                console.print(f"❌ Error: {e}", style="red")
                continue


@app.command()
def config_info(
    config: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Show configuration information."""
    config_obj = load_config(config)

    console.print(
        Panel(
            f"**Model:** {config_obj.litellm.get('model', 'Not specified')}\n"
            f"**MCP Servers:** {len(config_obj.mcp_servers)}\n"
            f"**System Prompt:** {'Configured' if config_obj.system_prompt else 'Default'}",
            title="📋 Configuration Info",
            border_style="green",
        )
    )

    if config_obj.mcp_servers:
        console.print("\n**MCP Servers:**")
        for name, server_config in config_obj.mcp_servers.items():
            console.print(f"  • {name}: {server_config}")

    if config_obj.system_prompt:
        console.print("\n**System Prompt:**")
        console.print(f"  • Type: {config_obj.system_prompt.type}")
        if config_obj.system_prompt.custom_prompt:
            console.print("  • Custom prompt configured")
        if config_obj.system_prompt.variables:
            console.print(
                f"  • Variables: {list(config_obj.system_prompt.variables.keys())}"
            )


if __name__ == "__main__":
    app()
