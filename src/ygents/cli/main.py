"""Main CLI application."""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

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

            # Initialize streaming response display
            content_parts: List[str] = []
            current_status = "Thinking..."

            def create_display() -> Panel:
                if content_parts:
                    response_text = "".join(content_parts)
                    return Panel(
                        Markdown(response_text),
                        title="🤖 Response",
                        border_style="blue",
                        padding=(1, 2),
                    )
                else:
                    return Panel(
                        f"[dim]{current_status}[/dim]",
                        title="🤖 Response",
                        border_style="blue",
                        padding=(1, 2),
                    )

            with Live(create_display(), console=console, refresh_per_second=10) as live:
                async for item in agent.run(query):
                    if hasattr(item, "type"):
                        if item.type == "content":
                            content_parts.append(item.content)  # type: ignore
                            live.update(create_display())
                        elif item.type == "tool_input":
                            current_status = f"Using tool: {item.tool_name}"  # type: ignore
                            live.update(create_display())
                        elif item.type == "tool_result":
                            current_status = "Processing result..."
                            live.update(create_display())
                        elif item.type == "error":
                            console.print(f"⚠️ Error: {item.message}", style="yellow")  # type: ignore
                    else:
                        # Fallback for backward compatibility
                        if hasattr(item, "content"):
                            content_parts.append(item.content)
                            live.update(create_display())

            # Display final message if no content was received
            if not content_parts:
                console.print("ℹ️ No response received.", style="dim")

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

                # Initialize streaming response display
                content_parts: List[str] = []
                current_status = "Thinking..."

                def create_display() -> Panel:
                    if content_parts:
                        response_text = "".join(content_parts)
                        return Panel(
                            Markdown(response_text),
                            title="🤖 Response",
                            border_style="blue",
                            padding=(1, 2),
                        )
                    else:
                        return Panel(
                            f"[dim]{current_status}[/dim]",
                            title="🤖 Response",
                            border_style="blue",
                            padding=(1, 2),
                        )

                with Live(
                    create_display(), console=console, refresh_per_second=10
                ) as live:
                    async for item in agent.run(query):
                        if hasattr(item, "type"):
                            if item.type == "content":
                                content_parts.append(item.content)  # type: ignore
                                live.update(create_display())
                            elif item.type == "tool_input":
                                current_status = f"Using tool: {item.tool_name}"  # type: ignore
                                live.update(create_display())
                            elif item.type == "tool_result":
                                current_status = "Processing result..."
                                live.update(create_display())
                            elif item.type == "error":
                                console.print(f"⚠️ Error: {item.message}", style="yellow")  # type: ignore
                        else:
                            # Fallback for backward compatibility
                            if hasattr(item, "content"):
                                content_parts.append(item.content)
                                live.update(create_display())

                # Display final message if no content was received
                if not content_parts:
                    console.print("ℹ️ No response received.", style="dim")

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
