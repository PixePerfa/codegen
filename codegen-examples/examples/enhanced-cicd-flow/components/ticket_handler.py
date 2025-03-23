"""
Ticket Handler Component

This component handles the conversion of Linear tickets to GitHub PRs.
It listens for Linear webhook events and creates PRs with AI-generated code.
"""

import logging
import os
from typing import Dict

from codegen import CodeAgent, CodegenApp, Codebase
from codegen.extensions.clients.linear import LinearClient
from codegen.extensions.linear.types import LinearEvent
from codegen.extensions.tools.github.create_pr import create_pr
from codegen.shared.enums.programming_language import ProgrammingLanguage

from config import get_component_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def has_codegen_label(data: Dict) -> bool:
    """Check if the Linear issue has the Codegen label."""
    if "labels" not in data:
        return False
    
    for label in data.get("labels", []):
        if label.get("name", "").lower() == "codegen":
            return True
    
    return False


def format_linear_message(title: str, description: str) -> str:
    """Format the Linear issue title and description into a query for the agent."""
    return f"""
    Linear Issue: {title}
    
    Description:
    {description}
    
    Please implement the changes described in this ticket.
    """


def create_codebase(repo_name: str, language: ProgrammingLanguage = ProgrammingLanguage.PYTHON) -> Codebase:
    """Create a codebase instance for the specified repository."""
    return Codebase.from_repo(repo_name, language=language)


def process_update_event(data: Dict) -> LinearEvent:
    """Process a Linear update event and extract relevant information."""
    issue_id = data.get("id")
    issue_identifier = data.get("identifier", "")
    issue_title = data.get("title", "")
    issue_description = data.get("description", "")
    issue_url = data.get("url", "")
    
    return LinearEvent(
        issue_id=issue_id,
        identifier=issue_identifier,
        title=issue_title,
        description=issue_description,
        issue_url=issue_url,
    )


def register_ticket_handlers(app: CodegenApp) -> None:
    """Register ticket handler functions with the CodegenApp."""
    config = get_component_config("ticket_handler")
    
    @app.linear.event("Issue", should_handle=has_codegen_label)
    def handle_issue_created(data: Dict) -> Dict:
        """Handle incoming Linear issue creation events."""
        linear_client = LinearClient(access_token=os.environ["LINEAR_API_TOKEN"])
        
        event = process_update_event(data)
        linear_client.comment_on_issue(event.issue_id, "I'm on it 👍")
        
        # Get the codebase
        codebase = app.get_codebase()
        
        # Run the agent
        query = format_linear_message(event.title, event.description)
        agent = CodeAgent(codebase)
        agent.run(query)
        
        # Create a PR
        pr_title = f"[{event.identifier}] {event.title}"
        pr_body = f"Codegen generated PR for issue: {event.issue_url}\n\n{event.description}"
        create_pr_result = create_pr(codebase, pr_title, pr_body)
        
        logger.info(f"PR created: {create_pr_result.url}")
        
        # Comment on the Linear issue with the PR link
        linear_client.comment_on_issue(
            event.issue_id, 
            f"I've created a PR to address this issue: {create_pr_result.url}"
        )
        
        # Reset the codebase
        codebase.reset()
        
        return {"status": "success", "pr_url": create_pr_result.url}
    
    @app.linear.event("Issue", should_handle=has_codegen_label)
    def handle_issue_updated(data: Dict) -> Dict:
        """Handle incoming Linear issue update events."""
        # Similar to handle_issue_created but for updates
        linear_client = LinearClient(access_token=os.environ["LINEAR_API_TOKEN"])
        
        event = process_update_event(data)
        linear_client.comment_on_issue(event.issue_id, "I'm updating the PR based on the changes 👍")
        
        # Get the codebase
        codebase = app.get_codebase()
        
        # Run the agent
        query = format_linear_message(event.title, event.description)
        agent = CodeAgent(codebase)
        agent.run(query)
        
        # Create a PR
        pr_title = f"[{event.identifier}] {event.title}"
        pr_body = f"Updated PR for issue: {event.issue_url}\n\n{event.description}"
        create_pr_result = create_pr(codebase, pr_title, pr_body)
        
        logger.info(f"PR updated: {create_pr_result.url}")
        
        # Comment on the Linear issue with the PR link
        linear_client.comment_on_issue(
            event.issue_id, 
            f"I've updated the PR to address the changes: {create_pr_result.url}"
        )
        
        # Reset the codebase
        codebase.reset()
        
        return {"status": "success", "pr_url": create_pr_result.url}


# For standalone usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Create a standalone app
    app = CodegenApp(name="ticket-handler")
    
    # Register handlers
    register_ticket_handlers(app)
    
    # Run the app
    import uvicorn
    uvicorn.run(app.app, host="0.0.0.0", port=8000)