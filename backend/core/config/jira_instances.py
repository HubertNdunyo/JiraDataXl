import os
import json
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


def has_legacy_jira_config() -> bool:
    """Check if legacy JIRA environment variables are present."""
    return all([
        os.getenv('JIRA_URL_1'),
        os.getenv('JIRA_USERNAME_1'),
        os.getenv('JIRA_PASSWORD_1'),
        os.getenv('JIRA_URL_2'),
        os.getenv('JIRA_USERNAME_2'),
        os.getenv('JIRA_PASSWORD_2'),
    ])


def load_jira_instances() -> List[Dict]:
    """Load JIRA instance configurations from environment or config file."""
    jira_instances_env = os.getenv('JIRA_INSTANCES')
    if jira_instances_env:
        try:
            instances_data = json.loads(jira_instances_env)
            if isinstance(instances_data, list):
                instances = []
                for idx, inst in enumerate(instances_data):
                    instances.append({
                        "url": inst.get('url'),
                        "username": inst.get('username'),
                        "password": inst.get('api_token') or inst.get('password'),
                        "instance_type": inst.get('type', f'instance_{idx+1}'),
                        "name": inst.get('name', f'Instance {idx+1}'),
                        "enabled": inst.get('enabled', True),
                    })
                logger.info(
                    "Loaded %d JIRA instances from JIRA_INSTANCES environment variable",
                    len(instances),
                )
                return instances
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse JIRA_INSTANCES JSON: %s", exc)

    config_file_path = os.getenv('JIRA_CONFIG_FILE')
    if config_file_path:
        config_path = Path(config_file_path)
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                instances = []
                for inst in config_data.get('instances', []):
                    if inst.get('enabled', True):
                        instances.append({
                            "url": inst.get('url'),
                            "username": inst.get('username'),
                            "password": inst.get('api_token') or inst.get('password'),
                            "instance_type": inst.get('id') or inst.get('type'),
                            "name": inst.get('name', 'JIRA Instance'),
                            "enabled": True,
                        })
                logger.info(
                    "Loaded %d JIRA instances from config file: %s",
                    len(instances),
                    config_file_path,
                )
                return instances
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    "Failed to load JIRA config file %s: %s",
                    config_file_path,
                    exc,
                )

    if has_legacy_jira_config():
        logger.info("Using legacy JIRA configuration from environment variables")
        return [
            {
                "url": os.getenv('JIRA_URL_1'),
                "username": os.getenv('JIRA_USERNAME_1'),
                "password": os.getenv('JIRA_PASSWORD_1'),
                "instance_type": "instance_1",
                "name": "Instance 1",
                "enabled": True,
            },
            {
                "url": os.getenv('JIRA_URL_2'),
                "username": os.getenv('JIRA_USERNAME_2'),
                "password": os.getenv('JIRA_PASSWORD_2'),
                "instance_type": "instance_2",
                "name": "Instance 2",
                "enabled": True,
            },
        ]

    raise EnvironmentError(
        "No JIRA instances configured. Please set JIRA_INSTANCES environment variable, "
        "JIRA_CONFIG_FILE to point to a config file, or use legacy JIRA_URL_1/2 variables."
    )
