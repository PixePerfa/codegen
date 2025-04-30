"""Knowledge Assistant for the integrated CI/CD flow.

This component provides a Slack chatbot that answers questions about the codebase
and the CI/CD pipeline.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import modal
import openai
from codegen import Codebase
from codegen.extensions.index.file_index import FileIndex
from codegen.shared.enums.programming_language import ProgrammingLanguage
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from fastapi import FastAPI, Request

from shared import (
    EventType,
    create_codebase,
    event_bus,
    load_config_from_env,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class KnowledgeAssistant:
    """Knowledge Assistant for the integrated CI/CD flow."""

    def __init__(self):
        """Initialize the knowledge assistant."""
        self.config = load_config_from_env()
        self.codebase = None
        self.index = None
        self.slack_app = App(
            token=self.config.slack.bot_token,
            signing_secret=self.config.slack.signing_secret,
        )
        self.responded = {}  # Store responded messages to avoid duplicates
        
        # Register Slack event handlers
        self.register_slack_handlers()
        
        # Subscribe to CI/CD events
        event_bus.subscribe(EventType.TICKET_CREATED, self.handle_ticket_created)
        event_bus.subscribe(EventType.PR_CREATED, self.handle_pr_created)
        event_bus.subscribe(EventType.PR_REVIEWED, self.handle_pr_reviewed)

    def initialize_codebase(self) -> None:
        """Initialize the codebase and index if not already initialized."""
        if self.codebase is None:
            logger.info(f"Initializing codebase for {self.config.github.repo}")
            self.codebase = create_codebase(self.config.github.repo, ProgrammingLanguage.PYTHON)
            
            # Initialize file index
            self.index = FileIndex(self.codebase)
            
            # Try to load existing index or create new one
            index_path = os.path.join(self.codebase.repo_path, ".codegen", "file_index.pkl")
            try:
                self.index.load(index_path)
            except FileNotFoundError:
                logger.info("Creating new file index")
                self.index.create()
                self.index.save(index_path)

    def register_slack_handlers(self) -> None:
        """Register Slack event handlers."""
        @self.slack_app.event("app_mention")
        def handle_mention(event: Dict[str, Any], say: Any) -> None:
            """Handle mentions of the bot in channels."""
            logger.info(f"Received Slack mention: {event}")
            
            # Skip if we've already answered this question
            if event["ts"] in self.responded:
                return
            self.responded[event["ts"]] = True
            
            # Get message text without the bot mention
            query = event["text"].split(">", 1)[1].strip()
            if not query:
                say("Please ask a question about the codebase or CI/CD pipeline!")
                return
            
            try:
                # Add typing indicator emoji
                self.slack_app.client.reactions_add(
                    channel=event["channel"],
                    timestamp=event["ts"],
                    name="writing_hand",
                )
                
                # Get answer using RAG
                answer, context = self.answer_question(query)
                
                # Format and send response in thread
                response = self.format_response(answer, context)
                say(text=response, thread_ts=event["ts"])
                
            except Exception as e:
                # Send error message in thread
                say(text=f"Error: {str(e)}", thread_ts=event["ts"])

    def answer_question(self, query: str) -> tuple[str, list[tuple[str, float]]]:
        """Answer a question about the codebase or CI/CD pipeline.

        Args:
            query: Question to answer

        Returns:
            Tuple of (answer, context)
        """
        logger.info(f"Answering question: {query}")
        
        # Initialize codebase and index if needed
        self.initialize_codebase()
        
        # Check if the question is about the CI/CD pipeline
        if any(keyword in query.lower() for keyword in ["pipeline", "ci/cd", "workflow", "process"]):
            return self.answer_pipeline_question(query), []
        
        # Otherwise, use RAG to answer questions about the codebase
        return self.answer_codebase_question(query)

    def answer_codebase_question(self, query: str) -> tuple[str, list[tuple[str, float]]]:
        """Answer a question about the codebase using RAG.

        Args:
            query: Question to answer

        Returns:
            Tuple of (answer, context)
        """
        # Perform semantic search
        results = self.index.similarity_search(query, k=5)
        
        # Collect context from relevant files
        context = []
        for file, score in results:
            context.append((file.filepath, score))
            
        # Format context for prompt
        context_str = "\n\n".join([f"File: {filepath}\nScore: {score:.3f}\n```\n{self.codebase.get_file(filepath).content[:1000]}...\n```" for filepath, score in context])
        
        # Create prompt for OpenAI
        prompt = f"""Given the following code context and question, provide a clear and accurate answer.
Focus on the specific code shown in the context.

Note that your response will be rendered in Slack, so make sure to use Slack markdown. Keep it short + sweet, like 2 paragraphs + some code blocks max.

Question: {query}

Relevant code:
{context_str}

Answer:"""
        
        # Get answer from OpenAI
        client = openai.OpenAI(api_key=self.config.ai.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a code expert. Answer questions about the given repo based on RAG'd results."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        
        return response.choices[0].message.content, context

    def answer_pipeline_question(self, query: str) -> str:
        """Answer a question about the CI/CD pipeline.

        Args:
            query: Question to answer

        Returns:
            Answer to the question
        """
        # Create prompt for OpenAI
        prompt = f"""You are an expert on the Codegen CI/CD pipeline. Answer the following question about the pipeline:

Question: {query}

The Codegen CI/CD pipeline consists of the following components:

1. Requirements & Planning Hub (Linear + AI)
   - Captures and analyzes requirements from Linear
   - Breaks down complex tasks into manageable subtasks
   - Creates a development plan with dependencies

2. AI-Assisted Development (Local Checkout + Ticket-to-PR)
   - Checks out code locally for development
   - Uses AI to generate code changes based on requirements
   - Creates PRs with detailed documentation

3. Comprehensive Code Review (PR Review Bot + Deep Analysis)
   - Reviews PRs with multiple perspectives (style, security, performance)
   - Performs deep code analysis to validate changes
   - Provides feedback via GitHub and Slack

4. Continuous Knowledge & Assistance (Slack Chatbot)
   - Provides context and assistance throughout the pipeline
   - Answers questions about the codebase and development process
   - Facilitates team communication and knowledge sharing

Answer:"""
        
        # Get answer from OpenAI
        client = openai.OpenAI(api_key=self.config.ai.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert on CI/CD pipelines. Answer questions about the Codegen CI/CD pipeline."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        
        return response.choices[0].message.content

    def format_response(self, answer: str, context: list[tuple[str, float]]) -> str:
        """Format the response for Slack with file links.

        Args:
            answer: Answer to the question
            context: List of (filepath, score) tuples

        Returns:
            Formatted response for Slack
        """
        response = f"*Answer:*\n{answer}"
        
        if context:
            response += "\n\n*Relevant Files:*\n"
            for filepath, score in context:
                github_link = f"https://github.com/{self.config.github.repo}/blob/main/{filepath}"
                response += f"• <{github_link}|{filepath}> (score: {score:.2f})\n"
        
        return response

    def handle_ticket_created(self, event: Any) -> None:
        """Handle ticket created event.

        Args:
            event: Ticket created event
        """
        # Extract issue data
        issue_data = event.data.get("issue", {})
        
        # Notify Slack
        self.slack_app.client.chat_postMessage(
            channel=self.config.slack.channel,
            text=f"New ticket created: {issue_data.get('identifier')} - {issue_data.get('title')}\n<{issue_data.get('url')}|View in Linear>",
        )

    def handle_pr_created(self, event: Any) -> None:
        """Handle PR created event.

        Args:
            event: PR created event
        """
        # Extract PR data
        pr_number = event.data.get("pr_number")
        pr_url = event.data.get("pr_url")
        
        # Notify Slack
        self.slack_app.client.chat_postMessage(
            channel=self.config.slack.channel,
            text=f"New PR created: <{pr_url}|#{pr_number}>",
        )

    def handle_pr_reviewed(self, event: Any) -> None:
        """Handle PR reviewed event.

        Args:
            event: PR reviewed event
        """
        # Extract PR data
        pr_number = event.data.get("pr_number")
        comments = event.data.get("comments", 0)
        
        # Notify Slack
        self.slack_app.client.chat_postMessage(
            channel=self.config.slack.channel,
            text=f"PR #{pr_number} reviewed with {comments} comments",
        )

    def create_fastapi_app(self) -> FastAPI:
        """Create a FastAPI app with Slack handlers.

        Returns:
            FastAPI app
        """
        web_app = FastAPI()
        handler = SlackRequestHandler(self.slack_app)
        
        @web_app.post("/")
        async def endpoint(request: Request):
            """Handle Slack events and verify requests."""
            return await handler.handle(request)
        
        @web_app.post("/slack/verify")
        async def verify(request: Request):
            """Handle Slack URL verification challenge."""
            data = await request.json()
            if data["type"] == "url_verification":
                return {"challenge": data["challenge"]}
            return await handler.handle(request)
        
        return web_app


def create_knowledge_assistant() -> KnowledgeAssistant:
    """Create and initialize the knowledge assistant.

    Returns:
        KnowledgeAssistant instance
    """
    return KnowledgeAssistant()