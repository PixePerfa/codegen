"""Shared data models for the integrated CI/CD flow."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class EventType(str, Enum):
    """Types of events in the CI/CD flow."""

    TICKET_CREATED = "ticket_created"
    TICKET_UPDATED = "ticket_updated"
    PR_CREATED = "pr_created"
    PR_UPDATED = "pr_updated"
    PR_REVIEWED = "pr_reviewed"
    CODE_GENERATED = "code_generated"
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DEPLOYMENT_FAILED = "deployment_failed"


@dataclass
class LinearIssue:
    """Representation of a Linear issue."""

    id: str
    title: str
    description: str
    identifier: str
    url: str
    labels: List[str]
    assignee_id: Optional[str] = None
    state_id: Optional[str] = None
    project_id: Optional[str] = None
    team_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class GitHubPR:
    """Representation of a GitHub PR."""

    number: int
    title: str
    body: str
    url: str
    branch: str
    base_branch: str
    author: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    merged: bool = False
    closed: bool = False
    labels: List[str] = None


@dataclass
class CodeChange:
    """Representation of a code change."""

    filepath: str
    content: str
    action: str  # "create", "modify", "delete"
    old_content: Optional[str] = None


@dataclass
class CodeReviewComment:
    """Representation of a code review comment."""

    body: str
    filepath: str
    line: int
    pr_number: int
    author: str
    created_at: datetime
    commit_id: Optional[str] = None


@dataclass
class Event:
    """Event in the CI/CD flow."""

    type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str  # Component that generated the event
    id: Optional[str] = None  # Unique identifier for the event


@dataclass
class CodeResearchResult:
    """Result of code research."""

    query: str
    findings: str
    relevant_files: List[str]
    timestamp: datetime