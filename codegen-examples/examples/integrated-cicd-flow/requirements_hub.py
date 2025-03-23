"""Requirements & Planning Hub for the integrated CI/CD flow.

This component handles Linear webhook events, analyzes requirements,
and breaks them down into manageable subtasks.
"""

import logging
import os
from typing import Any, Dict, List

import modal
from codegen.extensions.clients.linear import LinearClient
from codegen.extensions.events.codegen_app import CodegenApp

from shared import (
    EventType,
    create_event,
    event_bus,
    extract_subtasks,
    has_codegen_label,
    load_config_from_env,
    process_linear_event,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class RequirementsHub:
    """Requirements & Planning Hub for the integrated CI/CD flow."""

    def __init__(self, app: CodegenApp):
        """Initialize the requirements hub.

        Args:
            app: CodegenApp instance
        """
        self.app = app
        self.config = load_config_from_env()
        self.linear_client = LinearClient(access_token=self.config.linear.access_token)

    def handle_issue_created(self, data: Dict[str, Any]) -> None:
        """Handle Linear issue created event.

        Args:
            data: Linear webhook event data
        """
        logger.info("Handling Linear issue created event")
        
        # Process the event
        issue = process_linear_event(data)
        
        # Check if the issue has the Codegen label
        if "Codegen" not in issue.labels:
            logger.info(f"Skipping issue {issue.identifier} without Codegen label")
            return
        
        # Comment on the issue to acknowledge receipt
        self.linear_client.comment_on_issue(
            issue.id,
            "👋 I've received your request and I'm analyzing it now...",
        )
        
        # Analyze the issue and break it down into subtasks
        subtasks = extract_subtasks(issue.description)
        
        if subtasks:
            # Comment on the issue with the subtasks
            subtask_list = "\n".join([f"- {subtask}" for subtask in subtasks])
            self.linear_client.comment_on_issue(
                issue.id,
                f"I've analyzed your request and broken it down into the following subtasks:\n\n{subtask_list}\n\nI'll start working on these tasks now.",
            )
        else:
            # No subtasks found, proceed with the original issue
            self.linear_client.comment_on_issue(
                issue.id,
                "I'll start working on your request now.",
            )
        
        # Publish event to notify other components
        event = create_event(
            event_type=EventType.TICKET_CREATED,
            data={"issue": issue.__dict__, "subtasks": subtasks},
            source="requirements_hub",
        )
        event_bus.publish(event)

    def handle_issue_updated(self, data: Dict[str, Any]) -> None:
        """Handle Linear issue updated event.

        Args:
            data: Linear webhook event data
        """
        logger.info("Handling Linear issue updated event")
        
        # Process the event
        issue = process_linear_event(data)
        
        # Check if the issue has the Codegen label
        if "Codegen" not in issue.labels:
            logger.info(f"Skipping issue {issue.identifier} without Codegen label")
            return
        
        # Publish event to notify other components
        event = create_event(
            event_type=EventType.TICKET_UPDATED,
            data={"issue": issue.__dict__},
            source="requirements_hub",
        )
        event_bus.publish(event)

    def register_handlers(self) -> None:
        """Register Linear webhook handlers."""
        # Register issue created handler
        @self.app.linear.event("Issue", action="create", should_handle=has_codegen_label)
        def issue_created(data: Dict[str, Any]) -> None:
            self.handle_issue_created(data)

        # Register issue updated handler
        @self.app.linear.event("Issue", action="update", should_handle=has_codegen_label)
        def issue_updated(data: Dict[str, Any]) -> None:
            self.handle_issue_updated(data)


def create_requirements_hub(app: CodegenApp) -> RequirementsHub:
    """Create and initialize the requirements hub.

    Args:
        app: CodegenApp instance

    Returns:
        RequirementsHub instance
    """
    hub = RequirementsHub(app)
    hub.register_handlers()
    return hub