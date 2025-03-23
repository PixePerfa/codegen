"""Utility functions for the integrated CI/CD flow."""

import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from codegen import Codebase, CodeAgent
from codegen.extensions.index.file_index import FileIndex
from codegen.shared.enums.programming_language import ProgrammingLanguage

from shared.models import CodeResearchResult, Event, EventType, LinearIssue

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_codebase(repo_name: str, language: ProgrammingLanguage = ProgrammingLanguage.PYTHON) -> Codebase:
    """Create a codebase instance for the given repository.

    Args:
        repo_name: GitHub repository name (owner/repo)
        language: Programming language of the repository

    Returns:
        Codebase instance
    """
    logger.info(f"Creating codebase for {repo_name}")
    return Codebase.from_repo(repo_name, language=language)


def create_event(event_type: EventType, data: Dict[str, Any], source: str) -> Event:
    """Create an event in the CI/CD flow.

    Args:
        event_type: Type of the event
        data: Event data
        source: Component that generated the event

    Returns:
        Event instance
    """
    return Event(
        type=event_type,
        timestamp=datetime.now(),
        data=data,
        source=source,
        id=str(uuid.uuid4()),
    )


def format_linear_message(title: str, description: str) -> str:
    """Format Linear issue title and description for the code agent.

    Args:
        title: Issue title
        description: Issue description

    Returns:
        Formatted message for the code agent
    """
    return f"""
Task: {title}

Description:
{description}

Please implement the changes described above.
"""


def has_codegen_label(data: Dict[str, Any]) -> bool:
    """Check if a Linear issue has the Codegen label.

    Args:
        data: Linear webhook event data

    Returns:
        True if the issue has the Codegen label, False otherwise
    """
    if "labels" not in data:
        return False

    for label in data["labels"]:
        if label.get("name") == "Codegen":
            return True

    return False


def process_linear_event(data: Dict[str, Any]) -> LinearIssue:
    """Process a Linear webhook event and extract issue information.

    Args:
        data: Linear webhook event data

    Returns:
        LinearIssue instance
    """
    issue_data = data.get("data", {})
    
    return LinearIssue(
        id=issue_data.get("id", ""),
        title=issue_data.get("title", ""),
        description=issue_data.get("description", ""),
        identifier=issue_data.get("identifier", ""),
        url=issue_data.get("url", ""),
        labels=[label.get("name", "") for label in issue_data.get("labels", [])],
        assignee_id=issue_data.get("assigneeId"),
        state_id=issue_data.get("stateId"),
        project_id=issue_data.get("projectId"),
        team_id=issue_data.get("teamId"),
        created_at=datetime.fromisoformat(issue_data.get("createdAt", "").replace("Z", "+00:00")) if issue_data.get("createdAt") else None,
        updated_at=datetime.fromisoformat(issue_data.get("updatedAt", "").replace("Z", "+00:00")) if issue_data.get("updatedAt") else None,
    )


def perform_code_research(codebase: Codebase, query: str) -> CodeResearchResult:
    """Perform code research using semantic search.

    Args:
        codebase: Codebase instance
        query: Research query

    Returns:
        CodeResearchResult instance
    """
    logger.info(f"Performing code research for query: {query}")
    
    # Initialize file index
    index = FileIndex(codebase)
    
    # Try to load existing index or create new one
    index_path = os.path.join(codebase.repo_path, ".codegen", "file_index.pkl")
    try:
        index.load(index_path)
    except FileNotFoundError:
        logger.info("Creating new file index")
        index.create()
        index.save(index_path)
    
    # Perform semantic search
    results = index.similarity_search(query, k=5)
    
    # Extract relevant files
    relevant_files = [file.filepath for file, _ in results]
    
    # Use CodeAgent to analyze findings
    agent = CodeAgent(codebase)
    findings = agent.run(f"Research the following in the codebase: {query}")
    
    return CodeResearchResult(
        query=query,
        findings=findings,
        relevant_files=relevant_files,
        timestamp=datetime.now(),
    )


def extract_subtasks(description: str) -> List[str]:
    """Extract subtasks from a Linear issue description.

    Args:
        description: Issue description

    Returns:
        List of subtask descriptions
    """
    # Look for lists in the description
    subtasks = []
    
    # Match Markdown lists (both - and *)
    list_pattern = r"(?:^|\n)(?:\s*[-*]\s+)(.+)(?:\n|$)"
    matches = re.findall(list_pattern, description)
    
    if matches:
        subtasks.extend(matches)
    
    # If no lists found, try to split by newlines and filter out empty lines
    if not subtasks:
        lines = [line.strip() for line in description.split("\n") if line.strip()]
        if len(lines) > 1:
            subtasks = lines
    
    return subtasks


def generate_branch_name(issue_identifier: str, title: str) -> str:
    """Generate a branch name from a Linear issue identifier and title.

    Args:
        issue_identifier: Linear issue identifier (e.g., "ABC-123")
        title: Issue title

    Returns:
        Branch name
    """
    # Convert title to kebab case
    kebab_title = re.sub(r"[^a-zA-Z0-9\s]", "", title.lower())
    kebab_title = re.sub(r"\s+", "-", kebab_title)
    
    # Truncate to reasonable length
    if len(kebab_title) > 50:
        kebab_title = kebab_title[:50]
    
    # Add unique identifier to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{issue_identifier.lower()}-{kebab_title}-{unique_id}"