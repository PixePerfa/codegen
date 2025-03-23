"""
Integrated CI/CD Flow for Codegen

This example demonstrates a complete CI/CD pipeline using Codegen's components:
1. Requirements & Planning Hub (Linear + AI)
2. AI-Assisted Development (Local Checkout + Ticket-to-PR)
3. Comprehensive Code Review (PR Review Bot + Deep Analysis)
4. Continuous Knowledge & Assistance (Slack Integration)

Environment variables required:
- LINEAR_ACCESS_TOKEN: Linear API token
- LINEAR_SIGNING_SECRET: Linear webhook signing secret
- LINEAR_TEAM_ID: Linear team ID
- GITHUB_TOKEN: GitHub personal access token
- ANTHROPIC_API_KEY: Anthropic API key for Claude
- OPENAI_API_KEY: OpenAI API key
- SLACK_BOT_TOKEN: Slack bot token
- SLACK_SIGNING_SECRET: Slack signing secret
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import modal
from fastapi import FastAPI, Request
from openai import OpenAI
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

from codegen import CodeAgent, Codebase
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent
from codegen.extensions.index.file_index import FileIndex
from codegen.extensions.linear.types import LinearEvent
from codegen.extensions.slack.types import SlackEvent
from codegen.extensions.tools.github.create_pr import create_pr
from codegen.extensions.tools.github.create_pr_comment import create_pr_comment
from codegen.shared.enums.programming_language import ProgrammingLanguage

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create the base image with dependencies
base_image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install(
        "codegen>=0.26.3",
        "openai>=1.1.0",
        "fastapi[standard]",
        "slack_sdk>=1.18.0",
        "anthropic>=0.5.0",
    )
)

# Create Modal app
app = modal.App("codegen-integrated-cicd")

# Create Codegen app
cg = CodegenApp(name="codegen-integrated-cicd")

# Create persistent volume for storing indices
volume = modal.Volume.from_name("codegen-indices", create_if_missing=True)

# Event bus for communication between components
class EventBus:
    """Simple event bus for communication between components."""
    
    def __init__(self):
        self.subscribers = {}
        
    def subscribe(self, event_type: str, callback):
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        
    def publish(self, event_type: str, data: Any):
        """Publish an event to all subscribers."""
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)

# Create event bus instance
event_bus = EventBus()

# Shared utilities
def format_linear_message(title: str, description: str) -> str:
    """Format Linear issue title and description for the code agent."""
    return f"# {title}\n\n{description}"

def has_codegen_label(data: Dict) -> bool:
    """Check if a Linear issue has the 'Codegen' label."""
    if "labels" in data and data["labels"]:
        return any(label["name"] == "Codegen" for label in data["labels"])
    return False

def semantic_search(codebase: Codebase, query: str, k: int = 5) -> List[Tuple[str, float]]:
    """Perform semantic search on the codebase using FileIndex."""
    # Initialize file index
    index = FileIndex(codebase)
    
    # Try to load existing index or create new one
    index_path = f"/root/.codegen/indices/{codebase.repo_name.replace('/', '_')}.pkl"
    try:
        index.load(index_path)
    except FileNotFoundError:
        # Create new index if none exists
        index.create()
        index.save(index_path)
    
    # Find relevant files
    results = index.similarity_search(query, k=k)
    
    # Return file paths and scores
    return [(file.filepath, score) for file, score in results]

def generate_answer(query: str, context: str) -> str:
    """Generate an answer using RAG."""
    prompt = f"""You are a code expert. Given the following code context and question,
provide a clear and accurate answer.

Note: Keep it short and sweet - 2 paragraphs max.

Question: {query}

Relevant code:
{context}

Answer:"""

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a code expert. Answer questions about the given repo based on RAG'd results."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    return response.choices[0].message.content

def analyze_code_changes(codebase: Codebase, pr_number: int) -> str:
    """Analyze code changes in a PR using deep code research."""
    # Get the PR diff
    diffs = codebase.get_diffs()
    
    # Collect context from changed files
    context = ""
    for diff in diffs:
        if diff.a_path:
            file = codebase.get_file(diff.a_path)
            if file:
                context += f"File: {file.filepath}\n```\n{file.content}\n```\n\n"
        if diff.b_path and diff.b_path != diff.a_path:
            file = codebase.get_file(diff.b_path)
            if file:
                context += f"File: {file.filepath}\n```\n{file.content}\n```\n\n"
    
    # Generate analysis
    prompt = f"""You are a code review expert. Analyze the following code changes and provide feedback.
Focus on:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Security implications

Changed files:
{context}

Analysis:"""

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a code review expert. Provide detailed analysis of code changes."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    
    return response.choices[0].message.content

########################################################################################################################
# COMPONENTS
########################################################################################################################

# 1. Requirements & Planning Hub (Linear + AI)
@cg.linear.event("Issue", should_handle=has_codegen_label)
def handle_linear_issue(data: dict, event: LinearEvent):
    """Handle incoming Linear issue events."""
    logger.info(f"[LINEAR] Received issue event: {event.action}")
    
    # Comment on the issue to acknowledge receipt
    cg.linear.client.comment_on_issue(event.issue_id, "I'm on it! Starting to analyze your request... 👍")
    
    # Format the issue for the code agent
    query = format_linear_message(event.title, event.description)
    
    # Publish event for the development component
    event_bus.publish("new_development_task", {
        "issue_id": event.issue_id,
        "title": event.title,
        "description": event.description,
        "identifier": event.identifier,
        "issue_url": event.issue_url,
        "query": query
    })
    
    return {"status": "success", "message": "Issue received and processing started"}

# 2. AI-Assisted Development (Local Checkout + Ticket-to-PR)
@app.function(secrets=[modal.Secret.from_dotenv()], volumes={"/root/.codegen/indices": volume})
def development_task_handler(task_data: Dict):
    """Handle development tasks from Linear issues."""
    logger.info(f"[DEVELOPMENT] Processing task: {task_data['title']}")
    
    # Initialize codebase
    codebase = Codebase.from_repo("codegen-sh/codegen-sdk", language=ProgrammingLanguage.PYTHON)
    
    # Initialize code agent
    agent = CodeAgent(codebase=codebase)
    
    # Run the code agent with the query
    logger.info("[DEVELOPMENT] Running code agent")
    agent.run(task_data["query"])
    
    # Create a PR with the changes
    pr_title = f"[{task_data['identifier']}] {task_data['title']}"
    pr_body = f"Codegen generated PR for issue: {task_data['issue_url']}\n\n{task_data['description']}"
    
    create_pr_result = create_pr(codebase, pr_title, pr_body)
    logger.info(f"[DEVELOPMENT] PR created: {create_pr_result.url}")
    
    # Comment on the Linear issue with the PR link
    cg.linear.client.comment_on_issue(
        task_data["issue_id"], 
        f"I've created a PR with my proposed changes: {create_pr_result.url}"
    )
    
    # Publish event for the review component
    event_bus.publish("new_pr_for_review", {
        "pr_number": create_pr_result.number,
        "pr_url": create_pr_result.url,
        "issue_id": task_data["issue_id"]
    })
    
    # Reset the codebase
    codebase.reset()
    
    return {"status": "success", "pr_url": create_pr_result.url}

# Subscribe to development task events
event_bus.subscribe("new_development_task", development_task_handler)

# 3. Comprehensive Code Review (PR Review Bot + Deep Analysis)
@cg.github.event("pull_request:labeled")
def handle_pr_labeled(event: PullRequestLabeledEvent):
    """Handle PR labeled events for code review."""
    logger.info(f"[PR_REVIEW] PR #{event.number} labeled with: {event.label.name}")
    
    if event.label.name == "Codegen":
        # Notify Slack
        cg.slack.client.chat_postMessage(
            channel=os.environ.get("SLACK_CHANNEL_ID", "general"),
            text=f"PR #{event.number} labeled with Codegen, starting review: {event.pull_request.html_url}"
        )
        
        # Initialize codebase
        codebase = cg.get_codebase()
        
        # Check out the PR commit
        logger.info(f"[PR_REVIEW] Checking out commit: {event.pull_request.head.sha}")
        codebase.checkout(commit=event.pull_request.head.sha)
        
        # Analyze code changes
        analysis = analyze_code_changes(codebase, event.number)
        
        # Create PR comment with analysis
        create_pr_comment(codebase, event.number, f"## Code Review Analysis\n\n{analysis}")
        
        # Notify Slack with analysis summary
        cg.slack.client.chat_postMessage(
            channel=os.environ.get("SLACK_CHANNEL_ID", "general"),
            text=f"Completed review of PR #{event.number}. See the PR for detailed comments."
        )
        
        return {"status": "success", "message": "PR review completed"}

# 4. Continuous Knowledge & Assistance (Slack Integration)
@cg.slack.event("app_mention")
async def handle_slack_mention(event: SlackEvent):
    """Handle Slack mentions for code assistance."""
    logger.info(f"[SLACK] Received app_mention event: {event.text}")
    
    # Initialize codebase
    codebase = cg.get_codebase()
    
    # Extract the query from the message
    query = event.text.split(">", 1)[1].strip() if ">" in event.text else event.text
    
    if not query:
        cg.slack.client.chat_postMessage(
            channel=event.channel,
            text="Please ask a question about the codebase!",
            thread_ts=event.ts
        )
        return {"status": "success", "message": "Empty query"}
    
    # Add typing indicator
    cg.slack.client.reactions_add(
        channel=event.channel,
        timestamp=event.ts,
        name="thinking_face"
    )
    
    try:
        # Perform semantic search
        search_results = semantic_search(codebase, query)
        
        # Collect context from relevant files
        context = ""
        for filepath, score in search_results:
            file = codebase.get_file(filepath)
            if file:
                context += f"File: {filepath}\n```\n{file.content[:1000]}...\n```\n\n"
        
        # Generate answer
        answer = generate_answer(query, context)
        
        # Format response with file links
        response = f"*Answer:*\n{answer}\n\n*Relevant Files:*\n"
        for filepath, score in search_results:
            github_link = f"https://github.com/codegen-sh/codegen-sdk/blob/develop/{filepath}"
            response += f"• <{github_link}|{filepath}> (score: {score:.2f})\n"
        
        # Send response
        cg.slack.client.chat_postMessage(
            channel=event.channel,
            text=response,
            thread_ts=event.ts
        )
        
        # Remove typing indicator
        cg.slack.client.reactions_remove(
            channel=event.channel,
            timestamp=event.ts,
            name="thinking_face"
        )
        
        return {"status": "success", "message": "Response sent"}
        
    except Exception as e:
        logger.exception(f"[SLACK] Error handling mention: {e}")
        cg.slack.client.chat_postMessage(
            channel=event.channel,
            text=f"Error: {str(e)}",
            thread_ts=event.ts
        )
        return {"status": "error", "message": str(e)}

########################################################################################################################
# MODAL DEPLOYMENT
########################################################################################################################

@app.function(image=base_image, secrets=[modal.Secret.from_dotenv()], volumes={"/root/.codegen/indices": volume})
@modal.asgi_app()
def fastapi_app():
    """Create FastAPI app with all handlers."""
    logger.info("Starting integrated CI/CD flow app")
    return cg.app