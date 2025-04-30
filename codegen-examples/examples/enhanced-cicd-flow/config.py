"""
Configuration for the Enhanced CI/CD Flow.

This module contains configuration settings for all components of the CI/CD flow.
Each component can access these settings or override them with component-specific settings.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Default repository to use for examples
DEFAULT_REPO = "codegen-sh/codegen-sdk"

# Component settings
COMPONENTS = {
    "ticket_handler": {
        "enabled": True,
        "linear_team_id": os.environ.get("LINEAR_TEAM_ID", ""),
        "linear_webhook_path": "/linear/webhook",
    },
    "code_analyzer": {
        "enabled": True,
        "cli_enabled": True,
        "max_tokens": 4000,
    },
    "pr_validator": {
        "enabled": True,
        "github_webhook_path": "/github/events",
        "check_import_cycles": True,
        "check_code_quality": True,
    },
    "integration_hub": {
        "enabled": True,
        "slack_webhook_path": "/slack/events",
        "slack_channel": os.environ.get("SLACK_CHANNEL", ""),
    },
}

# Event routing configuration
EVENT_ROUTING = {
    "linear:issue:created": ["ticket_handler.handle_issue_created"],
    "linear:issue:updated": ["ticket_handler.handle_issue_updated"],
    "github:pull_request:labeled": ["pr_validator.handle_pr_labeled"],
    "github:pull_request:opened": ["pr_validator.handle_pr_opened"],
    "slack:app_mention": ["integration_hub.handle_mention"],
}

# Modal deployment settings
MODAL_DEPLOYMENT = {
    "app_name": "enhanced-cicd-flow",
    "image_name": "enhanced-cicd-flow-image",
    "python_version": "3.13",
    "keep_warm": 1,
}

# API settings
API_SETTINGS = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": os.environ.get("DEBUG", "False").lower() == "true",
}

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": True
        },
    }
}

def get_component_config(component_name: str) -> Dict:
    """Get configuration for a specific component."""
    return COMPONENTS.get(component_name, {})