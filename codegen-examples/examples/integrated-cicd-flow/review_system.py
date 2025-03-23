"""Review System for the integrated CI/CD flow.

This component handles PR review and analysis, providing feedback on code changes.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import modal
import openai
from codegen import Codebase, CodeAgent
from codegen.extensions.clients.linear import LinearClient
from codegen.extensions.langchain.agent import create_agent_with_tools
from codegen.extensions.langchain.tools import (
    ListDirectoryTool,
    RevealSymbolTool,
    RipGrepTool,
    SemanticSearchTool,
    ViewFileTool,
)
from codegen.extensions.tools.github.create_pr_comment import create_pr_comment
from codegen.shared.enums.programming_language import ProgrammingLanguage
from langchain_core.messages import SystemMessage
from slack_sdk import WebClient

from shared import (
    EventType,
    create_codebase,
    create_event,
    event_bus,
    load_config_from_env,
)
from shared.models import CodeReviewComment, Event

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ReviewSystem:
    """Review System for the integrated CI/CD flow."""

    def __init__(self):
        """Initialize the review system."""
        self.config = load_config_from_env()
        self.linear_client = LinearClient(access_token=self.config.linear.access_token)
        self.slack_client = WebClient(token=self.config.slack.bot_token)
        self.codebase = None
        
        # Subscribe to events
        event_bus.subscribe(EventType.PR_CREATED, self.handle_pr_created)
        event_bus.subscribe(EventType.PR_UPDATED, self.handle_pr_updated)

    def initialize_codebase(self) -> None:
        """Initialize the codebase if not already initialized."""
        if self.codebase is None:
            logger.info(f"Initializing codebase for {self.config.github.repo}")
            self.codebase = create_codebase(self.config.github.repo, ProgrammingLanguage.PYTHON)

    def handle_pr_created(self, event: Event) -> None:
        """Handle PR created event.

        Args:
            event: PR created event
        """
        logger.info("Handling PR created event")
        
        # Extract PR data
        pr_number = event.data.get("pr_number")
        pr_url = event.data.get("pr_url")
        issue_id = event.data.get("issue_id")
        branch = event.data.get("branch")
        
        if not pr_number:
            logger.error("PR number not found in event data")
            return
        
        # Notify Slack
        self.slack_client.chat_postMessage(
            channel=self.config.slack.channel,
            text=f"New PR created: <{pr_url}|#{pr_number}> - Starting review...",
        )
        
        # Review the PR
        self.review_pr(pr_number, issue_id, branch)

    def handle_pr_updated(self, event: Event) -> None:
        """Handle PR updated event.

        Args:
            event: PR updated event
        """
        logger.info("Handling PR updated event")
        
        # Extract PR data
        pr_number = event.data.get("pr_number")
        pr_url = event.data.get("pr_url")
        issue_id = event.data.get("issue_id")
        branch = event.data.get("branch")
        
        if not pr_number:
            logger.error("PR number not found in event data")
            return
        
        # Notify Slack
        self.slack_client.chat_postMessage(
            channel=self.config.slack.channel,
            text=f"PR updated: <{pr_url}|#{pr_number}> - Starting review...",
        )
        
        # Review the PR
        self.review_pr(pr_number, issue_id, branch)

    def review_pr(self, pr_number: int, issue_id: Optional[str] = None, branch: Optional[str] = None) -> None:
        """Review a PR and provide feedback.

        Args:
            pr_number: PR number
            issue_id: Linear issue ID
            branch: PR branch name
        """
        logger.info(f"Reviewing PR #{pr_number}")
        
        # Initialize codebase
        self.initialize_codebase()
        
        # Checkout the PR branch
        if branch:
            logger.info(f"Checking out branch {branch}")
            self.codebase.checkout_branch(branch)
        
        # Get the PR diff
        diff = self.codebase.get_pr_diff(pr_number)
        
        if not diff:
            logger.error(f"No diff found for PR #{pr_number}")
            return
        
        # Analyze the PR
        analysis_result = self.analyze_pr(pr_number, diff)
        
        # Post comments on the PR
        self.post_review_comments(pr_number, analysis_result)
        
        # Notify Slack
        self.slack_client.chat_postMessage(
            channel=self.config.slack.channel,
            text=f"Completed review of PR #{pr_number}. Found {len(analysis_result)} issues.",
        )
        
        # Notify Linear if issue_id is provided
        if issue_id:
            self.linear_client.comment_on_issue(
                issue_id,
                f"I've reviewed the PR and found {len(analysis_result)} issues. See the PR for details.",
            )
        
        # Publish event to notify other components
        event = create_event(
            event_type=EventType.PR_REVIEWED,
            data={
                "pr_number": pr_number,
                "issue_id": issue_id,
                "comments": len(analysis_result),
            },
            source="review_system",
        )
        event_bus.publish(event)
        
        # Reset the codebase for the next request
        self.codebase.reset()

    def analyze_pr(self, pr_number: int, diff: str) -> List[CodeReviewComment]:
        """Analyze a PR and generate review comments.

        Args:
            pr_number: PR number
            diff: PR diff

        Returns:
            List of review comments
        """
        logger.info(f"Analyzing PR #{pr_number}")
        
        # Create research tools
        tools = [
            ViewFileTool(self.codebase),
            ListDirectoryTool(self.codebase),
            RipGrepTool(self.codebase),
            SemanticSearchTool(self.codebase),
            RevealSymbolTool(self.codebase),
        ]
        
        # Initialize agent with research tools
        agent = create_agent_with_tools(
            codebase=self.codebase,
            tools=tools,
            system_message=SystemMessage(content=self.get_review_prompt()),
        )
        
        # Run the agent to analyze the PR
        result = agent.invoke(
            {"input": f"Review the following PR diff:\n\n{diff}"},
            config={"configurable": {"thread_id": pr_number}},
        )
        
        # Parse the agent's response to extract review comments
        return self.parse_review_comments(pr_number, result["messages"][-1].content)

    def parse_review_comments(self, pr_number: int, review_text: str) -> List[CodeReviewComment]:
        """Parse review comments from the agent's response.

        Args:
            pr_number: PR number
            review_text: Agent's review text

        Returns:
            List of review comments
        """
        # For now, we'll use a simple approach to extract comments
        # In a real implementation, this would be more sophisticated
        
        comments = []
        
        # Split the review text into sections
        sections = review_text.split("## ")
        
        for section in sections:
            if not section.strip():
                continue
            
            # Try to extract file path and line number
            lines = section.split("\n")
            if not lines:
                continue
            
            header = lines[0].strip()
            if ":" not in header:
                continue
            
            try:
                filepath, line_info = header.split(":", 1)
                filepath = filepath.strip()
                
                # Extract line number
                line_number = 1
                if "line" in line_info.lower():
                    line_match = re.search(r"line\s+(\d+)", line_info.lower())
                    if line_match:
                        line_number = int(line_match.group(1))
                
                # Extract comment body
                body = "\n".join(lines[1:]).strip()
                
                if body:
                    comments.append(
                        CodeReviewComment(
                            body=body,
                            filepath=filepath,
                            line=line_number,
                            pr_number=pr_number,
                            author="codegen-bot",
                            created_at=datetime.now(),
                        )
                    )
            except Exception as e:
                logger.error(f"Error parsing review comment: {e}")
        
        return comments

    def post_review_comments(self, pr_number: int, comments: List[CodeReviewComment]) -> None:
        """Post review comments on the PR.

        Args:
            pr_number: PR number
            comments: List of review comments
        """
        logger.info(f"Posting {len(comments)} review comments on PR #{pr_number}")
        
        for comment in comments:
            try:
                # Get the latest commit SHA
                commit_sha = self.codebase.get_latest_commit_sha()
                
                # Create PR comment
                create_pr_comment(
                    self.codebase,
                    pr_number=comment.pr_number,
                    body=comment.body,
                    commit_sha=commit_sha,
                    path=comment.filepath,
                    line=comment.line,
                )
                
                logger.info(f"Posted comment on {comment.filepath}:{comment.line}")
            except Exception as e:
                logger.error(f"Error posting review comment: {e}")

    def get_review_prompt(self) -> str:
        """Get the prompt for the review agent.

        Returns:
            Review prompt
        """
        return """You are a code review expert. Your goal is to provide thorough and constructive feedback on pull requests.

When reviewing code, consider:
1. Code quality and best practices
2. Potential bugs and edge cases
3. Performance implications
4. Security concerns
5. Architecture and design patterns
6. Consistency with the existing codebase

For each issue you find, provide:
1. The file path and line number
2. A clear description of the issue
3. The potential impact or risk
4. A suggested improvement or fix

Format your review as follows:
## filepath.py: line X
Issue: [Brief description of the issue]
Impact: [Potential impact or risk]
Suggestion: [Suggested improvement or fix]

Be specific, actionable, and constructive in your feedback. Focus on the most important issues first."""


def create_review_system() -> ReviewSystem:
    """Create and initialize the review system.

    Returns:
        ReviewSystem instance
    """
    return ReviewSystem()