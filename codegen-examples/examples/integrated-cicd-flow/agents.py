"""AI agents for the integrated CI/CD flow."""

import logging
import os
from typing import Dict, List, Optional

from codegen import CodeAgent, Codebase
from codegen.extensions.index.file_index import FileIndex
from codegen.extensions.langchain.agent import create_agent_with_tools
from codegen.extensions.langchain.tools import (
    ListDirectoryTool,
    RevealSymbolTool,
    RipGrepTool,
    SemanticSearchTool,
    ViewFileTool,
)
from langchain_core.messages import SystemMessage
from openai import OpenAI

from models import CodeReview, DevelopmentPlan, GitHubPR, LinearIssue

logger = logging.getLogger(__name__)


class PlanningAgent:
    """Agent for planning development work."""

    def __init__(self, codebase: Codebase):
        """Initialize the planning agent.

        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.client = OpenAI()

    def create_plan(self, issue: LinearIssue) -> DevelopmentPlan:
        """Create a development plan for a Linear issue.

        Args:
            issue: The Linear issue

        Returns:
            A development plan
        """
        logger.info(f"Creating development plan for issue {issue.identifier}")

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
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a software development planner."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        # Parse the response
        import json
        plan_data = json.loads(response.choices[0].message.content)

        # Create code changes
        from models import CodeChange
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


class DevelopmentAgent:
    """Agent for generating code changes."""

    def __init__(self, codebase: Codebase):
        """Initialize the development agent.

        Args:
            codebase: The codebase to modify
        """
        self.codebase = codebase
        self.code_agent = CodeAgent(codebase=codebase)

    def generate_changes(self, plan: DevelopmentPlan) -> List[Dict]:
        """Generate code changes based on a development plan.

        Args:
            plan: The development plan

        Returns:
            A list of code changes
        """
        logger.info(f"Generating code changes for plan: {plan.summary}")

        # Format the plan as a query for the code agent
        query = f"""
        # {plan.issue.title}

        ## Summary
        {plan.summary}

        ## Steps
        {chr(10).join([f"- {step}" for step in plan.steps])}

        ## Changes Needed
        {chr(10).join([f"- {change.filepath}: {change.description}" for change in plan.code_changes])}
        """

        # Run the code agent to generate changes
        result = self.code_agent.run(query)

        return result


class CodeResearchAgent:
    """Agent for deep code research."""

    RESEARCH_AGENT_PROMPT = """You are a code research expert. Your goal is to help users understand codebases by:
    1. Finding relevant code through semantic and text search
    2. Analyzing symbol relationships and dependencies
    3. Exploring directory structures
    4. Reading and explaining code

    Always explain your findings in detail and provide context about how different parts of the code relate to each other.
    When analyzing code, consider:
    - The purpose and functionality of each component
    - How different parts interact
    - Key patterns and design decisions
    - Potential areas for improvement

    Break down complex concepts into understandable pieces and use examples when helpful."""

    def __init__(self, codebase: Codebase):
        """Initialize the code research agent.

        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        
        # Create research tools
        tools = [
            ViewFileTool(codebase),
            ListDirectoryTool(codebase),
            RipGrepTool(codebase),
            SemanticSearchTool(codebase),
            RevealSymbolTool(codebase),
        ]
        
        # Initialize agent with research tools
        self.agent = create_agent_with_tools(
            codebase=codebase,
            tools=tools,
            system_message=SystemMessage(content=self.RESEARCH_AGENT_PROMPT)
        )

    def research(self, query: str) -> str:
        """Research a query in the codebase.

        Args:
            query: The research query

        Returns:
            The research findings
        """
        logger.info(f"Researching: {query}")
        
        # Run the agent
        result = self.agent.invoke(
            {"input": query},
            config={"configurable": {"thread_id": 1}},
        )
        
        return result["messages"][-1].content


class ReviewAgent:
    """Agent for reviewing PRs."""

    def __init__(self, codebase: Codebase):
        """Initialize the review agent.

        Args:
            codebase: The codebase to analyze
        """
        self.codebase = codebase
        self.client = OpenAI()
        self.research_agent = CodeResearchAgent(codebase)

    def review_pr(self, pr: GitHubPR) -> CodeReview:
        """Review a GitHub PR.

        Args:
            pr: The GitHub PR to review

        Returns:
            A code review
        """
        logger.info(f"Reviewing PR #{pr.number}: {pr.title}")
        
        # Get the diff
        diff = self.codebase.get_diff(pr.base_sha, pr.head_sha)
        
        # Research the changes
        research_query = f"Analyze the changes in PR #{pr.number}: {pr.title}"
        research_findings = self.research_agent.research(research_query)
        
        # Create a prompt for the review
        prompt = f"""
        You are an expert code reviewer. Review the following PR:
        
        # {pr.title}
        
        {pr.body}
        
        ## Diff
        ```diff
        {diff}
        ```
        
        ## Research Findings
        {research_findings}
        
        Provide a thorough review of the PR, including:
        1. A summary of the changes
        2. Specific comments on the code
        3. Suggestions for improvement
        4. Whether the PR should be approved
        
        Format your response as JSON with the following structure:
        {{
            "summary": "Brief summary of the changes",
            "comments": [
                {{
                    "filepath": "path/to/file",
                    "line": 123,
                    "comment": "Comment text"
                }}
            ],
            "suggestions": ["Suggestion 1", "Suggestion 2", ...],
            "approval": true/false
        }}
        """
        
        # Get the review from OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert code reviewer."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        # Parse the response
        import json
        review_data = json.loads(response.choices[0].message.content)
        
        # Create the code review
        return CodeReview(
            pr=pr,
            summary=review_data["summary"],
            comments=review_data["comments"],
            suggestions=review_data["suggestions"],
            approval=review_data["approval"]
        )