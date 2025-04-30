"""Development Engine for the integrated CI/CD flow.

This component handles code generation and PR creation based on Linear tickets.
It uses the CodeAgent to analyze the codebase and generate code changes.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import modal
from codegen import Codebase, CodeAgent
from codegen.extensions.clients.linear import LinearClient
from codegen.extensions.tools.github.create_pr import create_pr
from codegen.shared.enums.programming_language import ProgrammingLanguage

from shared import (
    EventType,
    create_codebase,
    create_event,
    event_bus,
    format_linear_message,
    generate_branch_name,
    load_config_from_env,
    perform_code_research,
)
from shared.models import Event, LinearIssue

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DevelopmentEngine:
    """Development Engine for the integrated CI/CD flow."""

    def __init__(self):
        """Initialize the development engine."""
        self.config = load_config_from_env()
        self.linear_client = LinearClient(access_token=self.config.linear.access_token)
        self.codebase = None
        
        # Subscribe to events
        event_bus.subscribe(EventType.TICKET_CREATED, self.handle_ticket_created)
        event_bus.subscribe(EventType.TICKET_UPDATED, self.handle_ticket_updated)

    def initialize_codebase(self) -> None:
        """Initialize the codebase if not already initialized."""
        if self.codebase is None:
            logger.info(f"Initializing codebase for {self.config.github.repo}")
            self.codebase = create_codebase(self.config.github.repo, ProgrammingLanguage.PYTHON)

    def handle_ticket_created(self, event: Event) -> None:
        """Handle ticket created event.

        Args:
            event: Ticket created event
        """
        logger.info("Handling ticket created event")
        
        # Extract issue data
        issue_data = event.data.get("issue", {})
        subtasks = event.data.get("subtasks", [])
        
        # Create LinearIssue object
        issue = LinearIssue(**issue_data)
        
        # Process the ticket
        self.process_ticket(issue, subtasks)

    def handle_ticket_updated(self, event: Event) -> None:
        """Handle ticket updated event.

        Args:
            event: Ticket updated event
        """
        logger.info("Handling ticket updated event")
        
        # Extract issue data
        issue_data = event.data.get("issue", {})
        
        # Create LinearIssue object
        issue = LinearIssue(**issue_data)
        
        # Check if we need to process the ticket
        # For now, we'll only process tickets that have been updated with the Codegen label
        if "Codegen" in issue.labels:
            self.process_ticket(issue, [])

    def process_ticket(self, issue: LinearIssue, subtasks: List[str]) -> None:
        """Process a Linear ticket and generate code changes.

        Args:
            issue: Linear issue
            subtasks: List of subtasks extracted from the issue
        """
        logger.info(f"Processing ticket {issue.identifier}")
        
        # Initialize codebase
        self.initialize_codebase()
        
        # Perform code research to understand the context
        research_query = f"Research context for: {issue.title}"
        research_result = perform_code_research(self.codebase, research_query)
        
        # Comment on the issue with research findings
        self.linear_client.comment_on_issue(
            issue.id,
            f"I've researched the codebase and found relevant context for your request. Here's what I found:\n\n{research_result.findings}\n\nRelevant files:\n" + "\n".join([f"- {file}" for file in research_result.relevant_files]),
        )
        
        # Format the message for the code agent
        query = format_linear_message(issue.title, issue.description)
        
        # Create a CodeAgent to generate code changes
        agent = CodeAgent(self.codebase)
        
        # Run the agent to generate code changes
        logger.info("Generating code changes")
        agent.run(query)
        
        # Create a PR with the changes
        branch_name = generate_branch_name(issue.identifier, issue.title)
        pr_title = f"[{issue.identifier}] {issue.title}"
        pr_body = f"Codegen generated PR for issue: {issue.url}\n\n{issue.description}"
        
        logger.info(f"Creating PR with branch {branch_name}")
        create_pr_result = create_pr(self.codebase, pr_title, pr_body, head_branch=branch_name)
        
        # Comment on the issue with the PR link
        self.linear_client.comment_on_issue(
            issue.id,
            f"I've created a PR with the changes: {create_pr_result.url}",
        )
        
        # Publish event to notify other components
        event = create_event(
            event_type=EventType.PR_CREATED,
            data={
                "issue_id": issue.id,
                "pr_number": create_pr_result.number,
                "pr_url": create_pr_result.url,
                "branch": branch_name,
            },
            source="development_engine",
        )
        event_bus.publish(event)
        
        # Reset the codebase for the next request
        self.codebase.reset()


def create_development_engine() -> DevelopmentEngine:
    """Create and initialize the development engine.

    Returns:
        DevelopmentEngine instance
    """
    return DevelopmentEngine()