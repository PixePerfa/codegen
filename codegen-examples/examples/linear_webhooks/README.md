# Linear Webhooks Example

This example demonstrates how to set up a webhook endpoint to receive events from Linear using Codegen.

## Setup

### Prerequisites

- Python 3.10+
- Linear account with API access
- (Optional) ngrok or similar tool for exposing local endpoints

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/codegen-sh/codegen.git
   cd codegen/codegen-examples/examples/linear_webhooks
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the template:
   ```bash
   cp .env.template .env
   ```

5. Edit the `.env` file with your Linear credentials:
   ```
   LINEAR_ACCESS_TOKEN="your_linear_access_token"
   LINEAR_SIGNING_SECRET="your_linear_signing_secret"
   LINEAR_TEAM_ID="e30439bb-1547-4d4e-9934-eb757c9beb46"  # Zeeeepa team ID
   ```

## Running the Example

### Standalone Version (No Modal)

Run the standalone version with:

```bash
python standalone.py
```

This will start a FastAPI server on http://0.0.0.0:8000.

To expose your local server to the internet (required for Linear webhooks), you can use ngrok:

```bash
ngrok http 8000
```

Then configure your Linear webhook to point to the ngrok URL + `/linear/events` (e.g., `https://your-ngrok-url.ngrok.io/linear/events`).

### Modal Version (Serverless)

To deploy the Modal version:

1. Install Modal:
   ```bash
   pip install modal
   ```

2. Set up your Modal account:
   ```bash
   modal token new
   ```

3. Deploy the app:
   ```bash
   modal deploy webhooks.py
   ```

Modal will provide a URL that you can use as your webhook endpoint in Linear.

## Configuring Linear Webhooks

1. Go to your Linear workspace settings
2. Navigate to API → Webhooks
3. Click "Create webhook"
4. Enter your webhook URL (ngrok URL or Modal URL)
5. Select the events you want to receive (e.g., Issues)
6. Save the webhook

## Troubleshooting

- **Import Error**: If you get an import error for `codegen`, make sure you've installed it with `pip install codegen>=0.22.2`
- **Authentication Error**: Verify your Linear credentials in the `.env` file
- **Webhook Not Receiving Events**: Check that your ngrok URL is correct and that the Linear webhook is properly configured

## Customizing the Example

To handle different Linear events, modify the `@app.linear.event()` decorator in `webhooks.py` or add a new handler in `standalone.py`.

For example, to handle Project events:

```python
@app.linear.event("Project")
def handle_project(self, data: dict):
    print(f"Project event: {data}")
```