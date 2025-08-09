import json
import json

import pytest

from core.config.jira_instances import load_jira_instances


def test_load_jira_instances_from_env(monkeypatch):
    sample = [{
        "url": "https://example.atlassian.net",
        "username": "user",
        "api_token": "token",
        "name": "Example",
        "enabled": True,
    }]
    monkeypatch.setenv("JIRA_INSTANCES", json.dumps(sample))
    monkeypatch.delenv("JIRA_CONFIG_FILE", raising=False)

    instances = load_jira_instances()

    assert len(instances) == 1
    assert instances[0]["url"] == sample[0]["url"]
    assert instances[0]["username"] == sample[0]["username"]
    assert instances[0]["password"] == sample[0]["api_token"]
    assert instances[0]["name"] == sample[0]["name"]


def test_load_jira_instances_from_file(tmp_path, monkeypatch):
    config = {
        "instances": [
            {
                "id": "test",
                "url": "https://example.net",
                "username": "user",
                "api_token": "token",
                "enabled": True,
            }
        ]
    }
    config_file = tmp_path / "instances.json"
    config_file.write_text(json.dumps(config))

    monkeypatch.delenv("JIRA_INSTANCES", raising=False)
    monkeypatch.setenv("JIRA_CONFIG_FILE", str(config_file))

    instances = load_jira_instances()

    assert len(instances) == 1
    assert instances[0]["instance_type"] == "test"


def test_load_jira_instances_missing(monkeypatch):
    for var in [
        "JIRA_INSTANCES",
        "JIRA_CONFIG_FILE",
        "JIRA_URL_1",
        "JIRA_USERNAME_1",
        "JIRA_PASSWORD_1",
        "JIRA_URL_2",
        "JIRA_USERNAME_2",
        "JIRA_PASSWORD_2",
    ]:
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(EnvironmentError):
        load_jira_instances()
