# Integrated CI/CD Flow with Codegen

This example demonstrates a complete CI/CD pipeline using Codegen's components, creating a seamless workflow from requirements to deployment.

## Architecture

```
[Requirements] → [Planning] → [Development] → [Review] → [Testing] → [Deployment] → [Monitoring]
```

### Components

1. **Requirements & Planning Hub** (Linear + AI)
   - Captures and analyzes requirements from Linear
   - Breaks down complex tasks into manageable subtasks
   - Creates a development plan with dependencies

2. **AI-Assisted Development** (Local Checkout + Ticket-to-PR)
   - Checks out code locally for development
   - Uses AI to generate code changes based on requirements
   - Creates PRs with detailed documentation

3. **Comprehensive Code Review** (PR Review + Deep Analysis)
   - Reviews PRs with multiple perspectives (style, security, performance)
   - Performs deep code analysis to validate changes
   - Provides feedback via GitHub and Slack

4. **Continuous Knowledge & Assistance** (Slack Integration)
   - Provides context and assistance throughout the pipeline
   - Answers questions about the codebase and development process
   - Facilitates team communication and knowledge sharing

## Setup

1. Create a `.env` file with your credentials:

```
# Linear
LINEAR_ACCESS_TOKEN="your_linear_access_token"
LINEAR_SIGNING_SECRET="your_linear_signing_secret"
LINEAR_TEAM_ID="e30439bb-1547-4d4e-9934-eb757c9beb46"  # Zeeeepa team ID

# GitHub
GITHUB_TOKEN="your_github_token"

# Slack
SLACK_SIGNING_SECRET="your_slack_signing_secret"
SLACK_BOT_TOKEN="your_slack_bot_token"

# AI Providers
ANTHROPIC_API_KEY="your_anthropic_key"
OPENAI_API_KEY="your_openai_key"
```

2. Deploy with Modal:

```bash
modal deploy app.py
```

3. Configure webhooks:
   - Linear: Use the Modal URL + `/linear/events`
   - GitHub: Use the Modal URL + `/github/events`
   - Slack: Use the Modal URL + `/slack/events`

## Usage

1. Create a Linear issue with the "Codegen" label
2. The system will automatically:
   - Analyze the issue and create a development plan
   - Generate code changes based on the requirements
   - Create a GitHub PR with the changes
   - Review the PR and provide feedback
   - Post updates to Slack

## Components

- `app.py`: Main application with Modal deployment
- `models.py`: Shared data models
- `events.py`: Event handlers for Linear, GitHub, and Slack
- `agents.py`: AI agents for code generation and review
- `utils.py`: Utility functions