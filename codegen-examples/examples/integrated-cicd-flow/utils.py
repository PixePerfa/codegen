"""Utility functions for the integrated CI/CD flow."""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from codegen import Codebase
from codegen.extensions.clients.linear import LinearClient
from codegen.extensions.index.file_index import FileIndex
from codegen.extensions.tools.github.create_pr import create_pr
from codegen.extensions.tools.github.create_pr_comment import create_pr_comment
from codegen.shared.enums.programming_language import ProgrammingLanguage
from openai import OpenAI

from models import CodeChange, DevelopmentPlan, GitHubPR, LinearIssue

logger = logging.getLogger(__name__)


def create_codebase(repo_name: str, language: ProgrammingLanguage = ProgrammingLanguage.PYTHON) -> Codebase:
    """Create a codebase instance.

    Args:
        repo_name: The name of the repository to clone
        language: The programming language of the repository

    Returns:
        A codebase instance
    """
    logger.info(f"Creating codebase for {repo_name}")
    return Codebase.from_repo(repo_name, language=language)


def format_linear_message(title: str, description: str) -> str:
    """Format a Linear issue for the code agent.

    Args:
        title: The issue title
        description: The issue description

    Returns:
        A formatted message for the code agent
    """
    return f"# {title}\n\n{description}"


def has_codegen_label(data: Dict[str, Any]) -> bool:
    """Check if a Linear issue has the Codegen label.

    Args:
        data: The webhook event data

    Returns:
        True if the issue has the Codegen label, False otherwise
    """
    codegen_label = os.environ.get("CODEGEN_LABEL", "Codegen")
    
    # Check if the issue has labels
    if "labels" in data.get("data", {}).get("issue", {}):
        for label in data["data"]["issue"]["labels"]:
            if label["name"].lower() == codegen_label.lower():
                return True
    return False


def process_linear_event(data: Dict[str, Any]) -> LinearIssue:
    """Process a Linear webhook event.

    Args:
        data: The webhook event data

    Returns:
        A LinearIssue object
    """
    issue_data = data["data"]["issue"]
    
    # Extract labels
    labels = []
    if "labels" in issue_data:
        labels = [label["name"] for label in issue_data["labels"]]
    
    # Create LinearIssue object
    return LinearIssue(
        id=issue_data["id"],
        title=issue_data["title"],
        description=issue_data.get("description", ""),
        identifier=issue_data["identifier"],
        url=f"https://linear.app/issue/{issue_data['identifier']}",
        labels=labels,
        assignee_id=issue_data.get("assigneeId")
    )


def process_github_pr_event(data: Dict[str, Any]) -> GitHubPR:
    """Process a GitHub PR webhook event.

    Args:
        data: The webhook event data

    Returns:
        A GitHubPR object
    """
    pr_data = data["pull_request"]
    
    # Extract labels
    labels = [label["name"] for label in pr_data.get("labels", [])]
    
    # Create GitHubPR object
    return GitHubPR(
        number=pr_data["number"],
        title=pr_data["title"],
        body=pr_data.get("body", ""),
        url=pr_data["html_url"],
        head_sha=pr_data["head"]["sha"],
        base_sha=pr_data["base"]["sha"],
        labels=labels
    )


def create_development_plan(issue: LinearIssue, codebase: Codebase) -> DevelopmentPlan:
    """Create a development plan for a Linear issue.

    Args:
        issue: The Linear issue
        codebase: The codebase to analyze

    Returns:
        A development plan
    """
    logger.info(f"Creating development plan for issue {issue.identifier}")
    
    # Use OpenAI to analyze the issue and create a plan
    client = OpenAI()
    
    # Create a prompt for the development plan
    prompt = f"""
    You are an expert software developer. Create a development plan for the following issue:
    
    # {issue.title}
    
    {issue.description}
    
    Your plan should include:
    1. A summary of the issue
    2. A list of steps to implement the solution
    3. A list of files that need to be created or modified
    
    Format your response as JSON with the following structure:
    {{
        "summary": "Brief summary of the issue",
        "steps": ["Step 1", "Step 2", ...],
        "code_changes": [
            {{
                "filepath": "path/to/file",
                "description": "What needs to be changed"
            }}
        ]
    }}
    """
    
    # Get the development plan from OpenAI
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a software development planner."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )
    
    # Parse the response
    plan_data = json.loads(response.choices[0].message.content)
    
    # Create code changes
    code_changes = []
    for change in plan_data["code_changes"]:
        code_changes.append(
            CodeChange(
                filepath=change["filepath"],
                content="",  # Will be filled in later
                description=change["description"]
            )
        )
    
    # Create the development plan
    return DevelopmentPlan(
        issue=issue,
        summary=plan_data["summary"],
        steps=plan_data["steps"],
        code_changes=code_changes
    )


def semantic_search(codebase: Codebase, query: str, k: int = 5) -> List[Tuple[str, float]]:
    """Perform semantic search on a codebase.

    Args:
        codebase: The codebase to search
        query: The search query
        k: The number of results to return

    Returns:
        A list of (filepath, score) tuples
    """
    # Initialize file index
    index = FileIndex(codebase)
    
    # Create index if it doesn't exist
    index.create()
    
    # Perform search
    results = index.similarity_search(query, k=k)
    
    return results


def generate_code_changes(plan: DevelopmentPlan, codebase: Codebase) -> List[CodeChange]:
    """Generate code changes based on a development plan.

    Args:
        plan: The development plan
        codebase: The codebase to modify

    Returns:
        A list of code changes
    """
    logger.info(f"Generating code changes for plan: {plan.summary}")
    
    # Use OpenAI to generate code changes
    client = OpenAI()
    
    # Updated code changes
    updated_changes = []
    
    # Generate code for each change
    for change in plan.code_changes:
        # Check if the file exists
        file_exists = False
        try:
            file = codebase.get_file(change.filepath)
            file_content = file.content
            file_exists = True
        except:
            file_content = ""
        
        # Create a prompt for the code change
        prompt = f"""
        You are an expert software developer. Generate code for the following change:
        
        # Issue: {plan.issue.title}
        
        ## Summary
        {plan.summary}
        
        ## File: {change.filepath}
        
        ## Description of change
        {change.description}
        
        {"## Existing file content" if file_exists else "## This is a new file"}
        ```
        {file_content}
        ```
        
        Generate the {"updated" if file_exists else "new"} file content. Return ONLY the code, no explanations.
        """
        
        # Get the code from OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a code generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        # Update the code change
        updated_changes.append(
            CodeChange(
                filepath=change.filepath,
                content=response.choices[0].message.content,
                description=change.description
            )
        )
    
    return updated_changes


def apply_code_changes(codebase: Codebase, changes: List[CodeChange]) -> None:
    """Apply code changes to a codebase.

    Args:
        codebase: The codebase to modify
        changes: The code changes to apply
    """
    logger.info(f"Applying {len(changes)} code changes")
    
    # Apply each change
    for change in changes:
        # Check if the file exists
        try:
            file = codebase.get_file(change.filepath)
            # Update existing file
            file.content = change.content
        except:
            # Create new file
            codebase.create_file(change.filepath, change.content)


def create_github_pr(codebase: Codebase, issue: LinearIssue, plan: DevelopmentPlan) -> Dict:
    """Create a GitHub PR for a Linear issue.

    Args:
        codebase: The codebase with changes
        issue: The Linear issue
        plan: The development plan

    Returns:
        The PR creation result
    """
    logger.info(f"Creating GitHub PR for issue {issue.identifier}")
    
    # Create PR title and body
    pr_title = f"[{issue.identifier}] {issue.title}"
    
    pr_body = f"""
    ## {issue.title}
    
    This PR addresses Linear issue [{issue.identifier}]({issue.url}).
    
    ### Summary
    {plan.summary}
    
    ### Implementation
    {chr(10).join([f"- {step}" for step in plan.steps])}
    
    ### Changes
    {chr(10).join([f"- {change.filepath}: {change.description}" for change in plan.code_changes])}
    """
    
    # Create the PR
    result = create_pr(codebase, pr_title, pr_body)
    
    return result


def comment_on_linear_issue(issue_id: str, comment: str) -> None:
    """Comment on a Linear issue.

    Args:
        issue_id: The Linear issue ID
        comment: The comment text
    """
    logger.info(f"Commenting on Linear issue {issue_id}")
    
    # Create Linear client
    linear_client = LinearClient(access_token=os.environ["LINEAR_ACCESS_TOKEN"])
    
    # Comment on the issue
    linear_client.comment_on_issue(issue_id, comment)