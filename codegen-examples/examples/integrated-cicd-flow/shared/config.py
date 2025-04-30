"""Configuration management for the integrated CI/CD flow."""

import os
from dataclasses import dataclass
from typing import Optional

import modal


@dataclass
class LinearConfig:
    """Configuration for Linear integration."""

    access_token: str
    signing_secret: str
    team_id: str
    label: str = "Codegen"


@dataclass
class GitHubConfig:
    """Configuration for GitHub integration."""

    token: str
    repo: str = "codegen-sh/codegen-sdk"


@dataclass
class SlackConfig:
    """Configuration for Slack integration."""

    bot_token: str
    signing_secret: str
    channel: str = "general"


@dataclass
class AIConfig:
    """Configuration for AI providers."""

    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None


@dataclass
class AppConfig:
    """Main application configuration."""

    linear: LinearConfig
    github: GitHubConfig
    slack: SlackConfig
    ai: AIConfig
    app_name: str = "codegen-cicd"


def load_config_from_env() -> AppConfig:
    """Load configuration from environment variables."""
    # Validate required environment variables
    required_vars = [
        "LINEAR_ACCESS_TOKEN",
        "LINEAR_SIGNING_SECRET",
        "LINEAR_TEAM_ID",
        "GITHUB_TOKEN",
        "SLACK_BOT_TOKEN",
        "SLACK_SIGNING_SECRET",
    ]

    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Create configuration objects
    linear_config = LinearConfig(
        access_token=os.environ["LINEAR_ACCESS_TOKEN"],
        signing_secret=os.environ["LINEAR_SIGNING_SECRET"],
        team_id=os.environ["LINEAR_TEAM_ID"],
    )

    github_config = GitHubConfig(
        token=os.environ["GITHUB_TOKEN"],
        repo=os.environ.get("GITHUB_REPO", "codegen-sh/codegen-sdk"),
    )

    slack_config = SlackConfig(
        bot_token=os.environ["SLACK_BOT_TOKEN"],
        signing_secret=os.environ["SLACK_SIGNING_SECRET"],
        channel=os.environ.get("SLACK_CHANNEL", "general"),
    )

    ai_config = AIConfig(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        openai_api_key=os.environ.get("OPENAI_API_KEY"),
    )

    return AppConfig(
        linear=linear_config,
        github=github_config,
        slack=slack_config,
        ai=ai_config,
        app_name=os.environ.get("APP_NAME", "codegen-cicd"),
    )


def get_modal_image() -> modal.Image:
    """Create a Modal image with all required dependencies."""
    return (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install("git")
        .pip_install(
            "fastapi[standard]",
            "codegen>=0.26.3",
            "slack-bolt>=1.18.0",
            "openai>=1.1.0",
            "anthropic>=0.5.0",
        )
    )


def get_modal_secret() -> modal.Secret:
    """Create a Modal secret from the .env file."""
    return modal.Secret.from_dotenv()