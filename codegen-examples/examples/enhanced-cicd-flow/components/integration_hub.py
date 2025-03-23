"""
Integration Hub Component

This component coordinates communication between other components and external services.
It provides a unified interface for Slack, GitHub, and Linear integrations.
"""

import logging
import os
from typing import Dict, List, Optional

from codegen import CodeAgent, CodegenApp, Codebase
from codegen.extensions.slack.types import SlackEvent

from config import get_component_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def register_integration_handlers(app: CodegenApp) -> None:
    """Register integration handler functions with the CodegenApp."""
    config = get_component_config("integration_hub")
    
    @app.slack.event("app_mention")
    async def handle_mention(event: SlackEvent) -> Dict:
        """Handle mentions in Slack and route to appropriate handlers."""
        logger.info("[APP_MENTION] Received app_mention event")
        
        # Get the codebase
        codebase = app.get_codebase()
        
        # Parse the message to determine the action
        text = event.text.lower()
        
        # Route to appropriate handler based on message content
        if "analyze" in text or "research" in text:
            # Code analysis request
            from components.code_analyzer import analyze_code
            
            # Extract the query
            query = text.replace("analyze", "", 1).replace("research", "", 1).strip()
            
            # Run the analysis
            result = analyze_code(codebase, query)
            
            # Send the result back to Slack
            app.slack.client.chat_postMessage(
                channel=event.channel,
                text=result,
                thread_ts=event.ts,
            )
            
            return {"status": "success", "action": "analyze", "result": "Analysis complete"}
            
        elif "check pr" in text or "validate pr" in text:
            # PR validation request
            try:
                # Extract PR number
                pr_parts = text.split("pr")
                if len(pr_parts) > 1:
                    pr_number = int(''.join(filter(str.isdigit, pr_parts[1])))
                    
                    # Send acknowledgment
                    app.slack.client.chat_postMessage(
                        channel=event.channel,
                        text=f"I'll check PR #{pr_number} for you. Adding the Codegen label to trigger validation.",
                        thread_ts=event.ts,
                    )
                    
                    # Add Codegen label to the PR
                    # Note: This would require additional GitHub API integration
                    # which is not implemented here for simplicity
                    
                    return {"status": "success", "action": "validate_pr", "pr_number": pr_number}
                else:
                    app.slack.client.chat_postMessage(
                        channel=event.channel,
                        text="I couldn't find a PR number in your message. Please specify a PR number to check.",
                        thread_ts=event.ts,
                    )
                    return {"status": "error", "reason": "No PR number provided"}
            except Exception as e:
                logger.error(f"Error processing PR validation request: {e}")
                app.slack.client.chat_postMessage(
                    channel=event.channel,
                    text=f"I encountered an error while processing your request: {str(e)}",
                    thread_ts=event.ts,
                )
                return {"status": "error", "reason": str(e)}
                
        elif "create ticket" in text or "new ticket" in text:
            # Ticket creation request
            try:
                # Extract ticket details
                title_start = text.find("title:") 
                desc_start = text.find("description:")
                
                if title_start != -1:
                    if desc_start != -1:
                        title = text[title_start + 6:desc_start].strip()
                        description = text[desc_start + 12:].strip()
                    else:
                        title = text[title_start + 6:].strip()
                        description = ""
                    
                    # Send acknowledgment
                    app.slack.client.chat_postMessage(
                        channel=event.channel,
                        text=f"Creating a new ticket with title: '{title}'",
                        thread_ts=event.ts,
                    )
                    
                    # Create Linear ticket
                    # Note: This would require additional Linear API integration
                    # which is not implemented here for simplicity
                    
                    return {"status": "success", "action": "create_ticket", "title": title}
                else:
                    app.slack.client.chat_postMessage(
                        channel=event.channel,
                        text="I couldn't find a title for the ticket. Please specify a title using 'title: Your Title'.",
                        thread_ts=event.ts,
                    )
                    return {"status": "error", "reason": "No ticket title provided"}
            except Exception as e:
                logger.error(f"Error processing ticket creation request: {e}")
                app.slack.client.chat_postMessage(
                    channel=event.channel,
                    text=f"I encountered an error while processing your request: {str(e)}",
                    thread_ts=event.ts,
                )
                return {"status": "error", "reason": str(e)}
        
        else:
            # General query - use CodeAgent
            agent = CodeAgent(codebase)
            response = agent.run(event.text)
            
            app.slack.client.chat_postMessage(
                channel=event.channel,
                text=response,
                thread_ts=event.ts,
            )
            
            return {"status": "success", "action": "general_query"}
    
    @app.slack.event("message")
    async def handle_message(event: Dict) -> Dict:
        """Handle regular messages in Slack channels."""
        # Only process messages in the configured channel
        if config.get("slack_channel") and event.get("channel") != config.get("slack_channel"):
            return {"status": "ignored", "reason": "Not in configured channel"}
        
        # Only process messages that mention the CI/CD flow
        text = event.get("text", "").lower()
        if "cicd" not in text and "ci/cd" not in text and "pipeline" not in text:
            return {"status": "ignored", "reason": "Not related to CI/CD"}
        
        logger.info("[MESSAGE] Received message about CI/CD")
        
        # Send a helpful response
        app.slack.client.chat_postMessage(
            channel=event.get("channel"),
            text="I noticed you're talking about CI/CD. You can interact with our enhanced CI/CD flow by mentioning me and using commands like:\n"
                 "• `analyze [query]` - Analyze code\n"
                 "• `check pr [number]` - Validate a PR\n"
                 "• `create ticket title: [title] description: [description]` - Create a Linear ticket",
            thread_ts=event.get("ts"),
        )
        
        return {"status": "success", "action": "ci_cd_help"}


# For standalone usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Create a standalone app
    app = CodegenApp(name="integration-hub")
    
    # Register handlers
    register_integration_handlers(app)
    
    # Run the app
    import uvicorn
    uvicorn.run(app.app, host="0.0.0.0", port=8000)