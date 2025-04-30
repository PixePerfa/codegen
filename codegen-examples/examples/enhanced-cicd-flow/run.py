#!/usr/bin/env python
"""
Enhanced CI/CD Flow CLI

This script provides a command-line interface for running individual components
of the enhanced CI/CD flow.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import rich_click as click
from rich.console import Console

# Add the project root to Python path
project_root = str(Path(__file__).parent.absolute())
sys.path.append(project_root)

# Configure rich-click
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "yellow italic"
click.rich_click.ERRORS_SUGGESTION = "Try running the command with --help for more information"

console = Console()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """[bold blue]🚀 Enhanced CI/CD Flow CLI[/bold blue]

    Run individual components of the enhanced CI/CD flow.
    """
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind the server to")
@click.option("--port", default=8000, help="Port to bind the server to")
def run_all(host: str, port: int):
    """[bold green]Run the complete integrated CI/CD flow[/bold green]

    This command starts the integrated CI/CD flow with all components enabled.
    """
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Import the main app
    from app import cg
    
    # Run the app
    import uvicorn
    console.print("[bold blue]Starting the integrated CI/CD flow...[/bold blue]")
    uvicorn.run("app:cg.app", host=host, port=port, reload=True)


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind the server to")
@click.option("--port", default=8001, help="Port to bind the server to")
def ticket_handler(host: str, port: int):
    """[bold green]Run the Ticket Handler component[/bold green]

    This command starts the Ticket Handler component for converting Linear tickets to GitHub PRs.
    """
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Create a standalone app
    from codegen import CodegenApp
    from components.ticket_handler import register_ticket_handlers
    
    app = CodegenApp(name="ticket-handler")
    register_ticket_handlers(app)
    
    # Run the app
    import uvicorn
    console.print("[bold blue]Starting the Ticket Handler component...[/bold blue]")
    uvicorn.run(app.app, host=host, port=port, reload=True)


@cli.command()
@click.argument("repo_name", required=False)
@click.option("--query", "-q", default=None, help="Initial research query to start with")
def code_analyzer(repo_name: Optional[str] = None, query: Optional[str] = None):
    """[bold green]Run the Code Analyzer component[/bold green]

    This command starts the Code Analyzer CLI for deep code analysis.

    [blue]Arguments:[/blue]
        [yellow]REPO_NAME[/yellow]: GitHub repository in format 'owner/repo' (optional, will prompt if not provided)
    """
    from components.code_analyzer import research
    
    # Run the research function
    research(repo_name, query)


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind the server to")
@click.option("--port", default=8002, help="Port to bind the server to")
def pr_validator(host: str, port: int):
    """[bold green]Run the PR Validator component[/bold green]

    This command starts the PR Validator component for checking code quality in PRs.
    """
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Create a standalone app
    from codegen import CodegenApp
    from components.pr_validator import register_pr_validators
    
    app = CodegenApp(name="pr-validator")
    register_pr_validators(app)
    
    # Run the app
    import uvicorn
    console.print("[bold blue]Starting the PR Validator component...[/bold blue]")
    uvicorn.run(app.app, host=host, port=port, reload=True)


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind the server to")
@click.option("--port", default=8003, help="Port to bind the server to")
def integration_hub(host: str, port: int):
    """[bold green]Run the Integration Hub component[/bold green]

    This command starts the Integration Hub component for coordinating between services.
    """
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Create a standalone app
    from codegen import CodegenApp
    from components.integration_hub import register_integration_handlers
    
    app = CodegenApp(name="integration-hub")
    register_integration_handlers(app)
    
    # Run the app
    import uvicorn
    console.print("[bold blue]Starting the Integration Hub component...[/bold blue]")
    uvicorn.run(app.app, host=host, port=port, reload=True)


@cli.command()
def deploy():
    """[bold green]Deploy the integrated CI/CD flow to Modal[/bold green]

    This command deploys the integrated CI/CD flow to Modal.
    """
    import subprocess
    
    console.print("[bold blue]Deploying the integrated CI/CD flow to Modal...[/bold blue]")
    subprocess.run(["modal", "deploy", "app.py"])
    console.print("[bold green]Deployment complete![/bold green]")


if __name__ == "__main__":
    cli()