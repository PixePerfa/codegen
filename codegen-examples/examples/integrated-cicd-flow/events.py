"""Event handlers for the integrated CI/CD flow."""

import logging
import os
from typing import Dict, List, Optional

from codegen import Codebase
from codegen.extensions.clients.linear import LinearClient
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent
from codegen.extensions.linear.types import LinearEvent
from codegen.extensions.slack.types import SlackEvent
from codegen.extensions.tools.github.create_pr_comment import create_pr_comment
from codegen.shared.enums.programming_language import ProgrammingLanguage

from agents import CodeResearchAgent, DevelopmentAgent, PlanningAgent, ReviewAgent
from event_bus import event_bus
from models import Event, EventType, GitHubPR, LinearIssue
from utils import (
    apply_code_changes,
    comment_on_linear_issue,
    create_codebase,
    create_github_pr,
    generate_code_changes,
    has_codegen_label,
    process_github_pr_event,
    process_linear_event,
)

logger = logging.getLogger(__name__)


async def handle_linear_issue_created(event: Event) -> None:
    """Handle a Linear issue created event.

    Args:
        event: The event to handle
    """
    logger.info("[LINEAR_ISSUE_CREATED] Handling Linear issue created event")
    
    # Process the Linear event
    issue = process_linear_event(event.payload)
    
    # Check if the issue has the Codegen label
    if "Codegen" not in issue.labels:
        logger.info(f"Issue {issue.identifier} does not have the Codegen label, skipping")
        return
    
    # Comment on the issue
    comment_on_linear_issue(issue.id, "I'm on it! 👍 Analyzing the issue and creating a development plan...")
    
    # Create a codebase
    repo_name = os.environ.get("GITHUB_REPO", "codegen-sh/codegen-sdk")
    codebase = create_codebase(repo_name)
    
    # Create a planning agent
    planning_agent = PlanningAgent(codebase)
    
    # Create a development plan
    plan = planning_agent.create_plan(issue)
    
    # Comment on the issue with the plan
    plan_comment = f"""
    ## Development Plan
    
    ### Summary
    {plan.summary}
    
    ### Steps
    {chr(10).join([f"- {step}" for step in plan.steps])}
    
    ### Changes
    {chr(10).join([f"- {change.filepath}: {change.description}" for change in plan.code_changes])}
    
    I'll start working on implementing these changes now.
    """
    comment_on_linear_issue(issue.id, plan_comment)
    
    # Create a development agent
    dev_agent = DevelopmentAgent(codebase)
    
    # Generate code changes
    dev_agent.generate_changes(plan)
    
    # Apply code changes
    updated_changes = generate_code_changes(plan, codebase)
    apply_code_changes(codebase, updated_changes)
    
    # Create a PR
    pr_result = create_github_pr(codebase, issue, plan)
    
    # Comment on the issue with the PR link
    pr_comment = f"I've created a PR with the changes: {pr_result['url']}"
    comment_on_linear_issue(issue.id, pr_comment)


async def handle_github_pr_created(event: Event) -> None:
    """Handle a GitHub PR created event.

    Args:
        event: The event to handle
    """
    logger.info("[GITHUB_PR_CREATED] Handling GitHub PR created event")
    
    # Process the GitHub PR event
    pr = process_github_pr_event(event.payload)
    
    # Check if the PR has the Codegen label
    if "Codegen" not in pr.labels:
        logger.info(f"PR #{pr.number} does not have the Codegen label, skipping")
        return
    
    # Create a codebase
    repo_name = os.environ.get("GITHUB_REPO", "codegen-sh/codegen-sdk")
    codebase = create_codebase(repo_name)
    
    # Create a review agent
    review_agent = ReviewAgent(codebase)
    
    # Review the PR
    review = review_agent.review_pr(pr)
    
    # Post a summary comment
    summary_comment = f"""
    ## Code Review

    {review.summary}
    
    ### Suggestions
    {chr(10).join([f"- {suggestion}" for suggestion in review.suggestions])}
    
    {"I approve this PR! ✅" if review.approval else "I have some concerns that should be addressed before merging. ❌"}
    """
    create_pr_comment(codebase, pr.number, summary_comment)
    
    # Post individual comments
    for comment in review.comments:
        create_pr_comment(
            codebase,
            pr.number,
            comment["comment"],
            commit_sha=pr.head_sha,
            path=comment["filepath"],
            line=comment["line"]
        )


async def handle_slack_message(event: Event) -> None:
    """Handle a Slack message event.

    Args:
        event: The event to handle
    """
    logger.info("[SLACK_MESSAGE] Handling Slack message event")
    
    # Get the Slack event data
    slack_event = event.payload
    
    # Check if it's a message mentioning the bot
    if "app_mention" not in slack_event.get("type", ""):
        return
    
    # Get the message text
    text = slack_event.get("text", "")
    
    # Remove the bot mention
    query = text.split(">", 1)[1].strip() if ">" in text else text
    
    # Create a codebase
    repo_name = os.environ.get("GITHUB_REPO", "codegen-sh/codegen-sdk")
    codebase = create_codebase(repo_name)
    
    # Create a research agent
    research_agent = CodeResearchAgent(codebase)
    
    # Research the query
    answer = research_agent.research(query)
    
    # Send the response
    from slack_sdk import WebClient
    client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    client.chat_postMessage(
        channel=slack_event["channel"],
        text=answer,
        thread_ts=slack_event.get("ts")
    )


# Register event handlers
async def setup_event_handlers() -> None:
    """Set up event handlers for the event bus."""
    event_bus.subscribe(EventType.LINEAR_ISSUE_CREATED, handle_linear_issue_created)
    event_bus.subscribe(EventType.LINEAR_ISSUE_UPDATED, handle_linear_issue_created)  # Reuse the same handler
    event_bus.subscribe(EventType.GITHUB_PR_CREATED, handle_github_pr_created)
    event_bus.subscribe(EventType.SLACK_MESSAGE, handle_slack_message)


# Linear webhook handler
def handle_linear_webhook(data: Dict) -> None:
    """Handle a Linear webhook event.

    Args:
        data: The webhook event data
    """
    logger.info("[LINEAR] Received Linear webhook event")
    
    # Check if it's an issue event
    if "issue" not in data.get("data", {}):
        return
    
    # Create an event
    event = Event(
        type=EventType.LINEAR_ISSUE_CREATED,
        payload=data
    )
    
    # Publish the event
    import asyncio
    asyncio.create_task(event_bus.publish(event))


# GitHub webhook handler
def handle_github_webhook(data: Dict) -> None:
    """Handle a GitHub webhook event.

    Args:
        data: The webhook event data
    """
    logger.info("[GITHUB] Received GitHub webhook event")
    
    # Check if it's a PR event
    if "pull_request" not in data:
        return
    
    # Create an event
    event = Event(
        type=EventType.GITHUB_PR_CREATED,
        payload=data
    )
    
    # Publish the event
    import asyncio
    asyncio.create_task(event_bus.publish(event))


# Slack webhook handler
def handle_slack_webhook(data: Dict) -> None:
    """Handle a Slack webhook event.

    Args:
        data: The webhook event data
    """
    logger.info("[SLACK] Received Slack webhook event")
    
    # Create an event
    event = Event(
        type=EventType.SLACK_MESSAGE,
        payload=data
    )
    
    # Publish the event
    import asyncio
    asyncio.create_task(event_bus.publish(event))