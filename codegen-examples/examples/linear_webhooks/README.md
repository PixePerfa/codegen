# Linear Webhooks Example

This example demonstrates how to set up a webhook endpoint to receive events from Linear using the Codegen framework.

## Prerequisites

- Python 3.13 or later
- [Modal](https://modal.com/) account
- Linear account with API access

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or using uv:

```bash
uv pip install -r requirements.txt
```

2. Create a `.env` file with your Linear credentials:

```
LINEAR_ACCESS_TOKEN="your_linear_access_token"
LINEAR_SIGNING_SECRET="your_linear_signing_secret"
LINEAR_TEAM_ID="your_linear_team_id"
```

You can find your Linear Team ID in your Linear workspace settings → Teams → Select your team → The Team ID will be in the URL (e.g., `https://linear.app/your-workspace/team/team-id/settings`).

## Running the Example

### Local Development

For local development and testing, you can run the example using Modal:

```bash
modal serve webhooks.py
```

This will start a local server that you can use for testing.

### Deployment

To deploy the example to Modal:

```bash
modal deploy webhooks.py
```

After deployment, Modal will provide a URL that you can use as your webhook endpoint in Linear.

## Setting Up the Linear Webhook

1. Go to your Linear workspace settings → API → Webhooks → Create webhook
2. Enter the Modal URL provided after deployment
3. Select the events you want to receive (e.g., Issue created, Issue updated)
4. Save the webhook

## How It Works

The example sets up a webhook endpoint that listens for Linear events. When an event is received, it prints the event data to the console. You can extend this example to perform custom actions based on the event data.

The key components are:

- `CodegenApp`: Handles the webhook events
- `@app.linear.event("Issue")`: Decorator that registers a handler for Issue events
- `app.linear.subscribe_all_handlers()`: Subscribes to all registered handlers
- `app.linear.unsubscribe_all_handlers()`: Unsubscribes from all handlers when the app is shut down

## Troubleshooting

If you encounter any issues, check the following:

- Make sure your Linear credentials are correct
- Verify that the webhook URL is accessible from the internet
- Check the Modal logs for any errors

## Further Reading

- [Linear API Documentation](https://developers.linear.app/docs/)
- [Modal Documentation](https://modal.com/docs/)