"""Data models for the integrated CI/CD flow."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union


class EventType(str, Enum):
    """Types of events in the CI/CD flow."""

    LINEAR_ISSUE_CREATED = "linear_issue_created"
    LINEAR_ISSUE_UPDATED = "linear_issue_updated"
    GITHUB_PR_CREATED = "github_pr_created"
    GITHUB_PR_UPDATED = "github_pr_updated"
    GITHUB_PR_REVIEWED = "github_pr_reviewed"
    SLACK_MESSAGE = "slack_message"


@dataclass
class Event:
    """Base event class for the event bus."""

    type: EventType
    payload: Dict
    metadata: Optional[Dict] = None


@dataclass
class LinearIssue:
    """Linear issue data."""

    id: str
    title: str
    description: str
    identifier: str  # e.g., "ZEE-123"
    url: str
    labels: List[str]
    assignee_id: Optional[str] = None


@dataclass
class GitHubPR:
    """GitHub PR data."""

    number: int
    title: str
    body: str
    url: str
    head_sha: str
    base_sha: str
    labels: List[str]


@dataclass
class CodeChange:
    """Code change data."""

    filepath: str
    content: str
    description: str


@dataclass
class DevelopmentPlan:
    """Development plan data."""

    issue: LinearIssue
    summary: str
    steps: List[str]
    code_changes: List[CodeChange]


@dataclass
class CodeReview:
    """Code review data."""

    pr: GitHubPR
    summary: str
    comments: List[Dict]
    suggestions: List[str]
    approval: bool


@dataclass
class SlackMessage:
    """Slack message data."""

    channel: str
    text: str
    thread_ts: Optional[str] = None
    blocks: Optional[List[Dict]] = None