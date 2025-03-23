# Integrated CI/CD Flow for Codegen

This example demonstrates a complete CI/CD pipeline using Codegen's components, providing a cohesive workflow from requirements to deployment.

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

3. **Comprehensive Code Review** (PR Review Bot + Deep Analysis)
   - Reviews PRs with multiple perspectives (style, security, performance)
   - Performs deep code analysis to validate changes
   - Provides feedback via GitHub and Slack

4. **Continuous Knowledge & Assistance** (Slack Integration)
   - Provides context and assistance throughout the pipeline
   - Answers questions about the codebase and development process
   - Facilitates team communication and knowledge sharing

## Key Features

- **Event-driven architecture**: Components communicate through an event bus
- **Modern semantic search**: Uses `FileIndex` instead of deprecated `VectorIndex`
- **Local development support**: Can be run locally or deployed with Modal
- **Comprehensive code analysis**: Deep code research throughout the pipeline
- **Slack integration**: Team communication and knowledge sharing

## Setup

### Environment Variables

Create a `.env` file with the following variables:

```
# Linear
LINEAR_ACCESS_TOKEN="your_linear_token"
LINEAR_SIGNING_SECRET="your_linear_signing_secret"
LINEAR_TEAM_ID="your_linear_team_id"

# GitHub
GITHUB_TOKEN="your_github_token"

# AI Providers
ANTHROPIC_API_KEY="your_anthropic_key"
OPENAI_API_KEY="your_openai_key"

# Slack
SLACK_BOT_TOKEN="your_slack_bot_token"
SLACK_SIGNING_SECRET="your_slack_signing_secret"
SLACK_CHANNEL_ID="your_slack_channel_id"
```

### Deployment

Deploy with Modal:

```bash
modal deploy app.py
```

This will create webhook endpoints for Linear, GitHub, and Slack.

### Webhook Configuration

1. **Linear Webhook**:
   - Go to Linear workspace settings → API → Webhooks → Create webhook
   - URL: `https://your-modal-app.modal.run/linear/events`
   - Events: Select "Issues" events
   - Secret: Use your `LINEAR_SIGNING_SECRET`

2. **GitHub Webhook**:
   - Go to your repository settings → Webhooks → Add webhook
   - URL: `https://your-modal-app.modal.run/github/events`
   - Events: Select "Pull requests" events
   - Secret: Not required (authentication handled by GitHub token)

3. **Slack App**:
   - Create a Slack app in the Slack API dashboard
   - Enable Event Subscriptions
   - URL: `https://your-modal-app.modal.run/slack/events`
   - Subscribe to bot events: `app_mention`
   - Install the app to your workspace

## Usage

1. Create a Linear issue with the "Codegen" label
2. The system will automatically:
   - Analyze the issue
   - Generate code changes
   - Create a GitHub PR
   - Review the PR
   - Notify the team via Slack

You can also interact with the system via Slack by mentioning the bot:
```
@codegen-bot How does the FileIndex work?
```

## Architecture Details

### Event Bus

The system uses a simple event bus for communication between components:

```python
class EventBus:
    def __init__(self):
        self.subscribers = {}
        
    def subscribe(self, event_type: str, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        
    def publish(self, event_type: str, data: Any):
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)
```

### Semantic Search

The system uses `FileIndex` for semantic search:

```python
def semantic_search(codebase: Codebase, query: str, k: int = 5) -> List[Tuple[str, float]]:
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
```

## Extending the System

You can extend the system by:

1. Adding new event types to the event bus
2. Creating new handlers for different event types
3. Integrating with additional tools and services
4. Customizing the code analysis and review process

## Troubleshooting

- **Missing dependencies**: Ensure all required packages are installed
- **Webhook errors**: Check webhook URLs and secrets
- **Authentication issues**: Verify API tokens and permissions
- **Modal deployment**: Check Modal logs for deployment errors