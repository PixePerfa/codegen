"""
Standalone version of the Integrated CI/CD Flow for Codegen

This version can be run locally without Modal for development and testing.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import uvicorn
from dotenv import load_dotenv
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

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create Codegen app
cg = CodegenApp(name="codegen-integrated-cicd")

# Create FastAPI app
app = FastAPI()

# Create Slack app
slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
slack_handler = SlackRequestHandler(slack_app)

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
    index_path = f"./.codegen/indices/{codebase.repo_name.replace('/', '_')}.pkl"
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
@app.post("/linear/events")
async def handle_linear_webhook(request: Request):
    """Handle incoming Linear webhook events."""
    data = await request.json()
    
    # Check if this is a Linear issue event with the Codegen label
    if "action" in data and data["action"] == "create" and has_codegen_label(data):
        logger.info(f"[LINEAR] Received issue event: {data['action']}")
        
        # Extract issue details
        issue_id = data["id"]
        title = data["title"]
        description = data.get("description", "")
        identifier = data["identifier"]
        issue_url = f"https://linear.app/issue/{identifier}"
        
        # Comment on the issue to acknowledge receipt
        cg.linear.client.comment_on_issue(issue_id, "I'm on it! Starting to analyze your request... 👍")
        
        # Format the issue for the code agent
        query = format_linear_message(title, description)
        
        # Publish event for the development component
        event_bus.publish("new_development_task", {
            "issue_id": issue_id,
            "title": title,
            "description": description,
            "identifier": identifier,
            "issue_url": issue_url,
            "query": query
        })
        
        return {"status": "success", "message": "Issue received and processing started"}
    
    return {"status": "ignored", "message": "Event ignored"}

# 2. AI-Assisted Development (Local Checkout + Ticket-to-PR)
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
@app.post("/github/events")
async def handle_github_webhook(request: Request):
    """Handle GitHub webhook events."""
    data = await request.json()
    
    # Check if this is a PR labeled event
    if "action" in data and data["action"] == "labeled" and "pull_request" in data:
        label_name = data["label"]["name"]
        pr_number = data["pull_request"]["number"]
        
        logger.info(f"[PR_REVIEW] PR #{pr_number} labeled with: {label_name}")
        
        if label_name == "Codegen":
            # Notify Slack
            slack_app.client.chat_postMessage(
                channel=os.environ.get("SLACK_CHANNEL_ID", "general"),
                text=f"PR #{pr_number} labeled with Codegen, starting review: {data['pull_request']['html_url']}"
            )
            
            # Initialize codebase
            codebase = Codebase.from_repo("codegen-sh/codegen-sdk", language=ProgrammingLanguage.PYTHON)
            
            # Check out the PR commit
            logger.info(f"[PR_REVIEW] Checking out commit: {data['pull_request']['head']['sha']}")
            codebase.checkout(commit=data["pull_request"]["head"]["sha"])
            
            # Analyze code changes
            analysis = analyze_code_changes(codebase, pr_number)
            
            # Create PR comment with analysis
            create_pr_comment(codebase, pr_number, f"## Code Review Analysis\n\n{analysis}")
            
            # Notify Slack with analysis summary
            slack_app.client.chat_postMessage(
                channel=os.environ.get("SLACK_CHANNEL_ID", "general"),
                text=f"Completed review of PR #{pr_number}. See the PR for detailed comments."
            )
            
            return {"status": "success", "message": "PR review completed"}
    
    return {"status": "ignored", "message": "Event ignored"}

# 4. Continuous Knowledge & Assistance (Slack Integration)
@app.post("/slack/events")
async def handle_slack_events(request: Request):
    """Handle Slack events."""
    return await slack_handler.handle(request)

@slack_app.event("app_mention")
def handle_slack_mention(event, say):
    """Handle Slack mentions for code assistance."""
    logger.info(f"[SLACK] Received app_mention event: {event['text']}")
    
    # Initialize codebase
    codebase = Codebase.from_repo("codegen-sh/codegen-sdk", language=ProgrammingLanguage.PYTHON)
    
    # Extract the query from the message
    query = event["text"].split(">", 1)[1].strip() if ">" in event["text"] else event["text"]
    
    if not query:
        say(
            text="Please ask a question about the codebase!",
            thread_ts=event["ts"]
        )
        return
    
    # Add typing indicator
    slack_app.client.reactions_add(
        channel=event["channel"],
        timestamp=event["ts"],
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
        say(
            text=response,
            thread_ts=event["ts"]
        )
        
        # Remove typing indicator
        slack_app.client.reactions_remove(
            channel=event["channel"],
            timestamp=event["ts"],
            name="thinking_face"
        )
        
    except Exception as e:
        logger.exception(f"[SLACK] Error handling mention: {e}")
        say(
            text=f"Error: {str(e)}",
            thread_ts=event["ts"]
        )

########################################################################################################################
# MAIN
########################################################################################################################

if __name__ == "__main__":
    # Create indices directory if it doesn't exist
    os.makedirs("./.codegen/indices", exist_ok=True)
    
    # Run the FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=8000)