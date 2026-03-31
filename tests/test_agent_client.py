"""Tests for the custom agent REST API client."""

import pytest
from unittest.mock import patch, MagicMock
from agent_eval.utils.agent_client import AgentClient


class TestAgentClient:
    def test_custom_config(self):
        client = AgentClient(
            endpoint="https://test-app.azurecontainerapps.io/api/chat",
            api_key="test-key-123",
        )
        assert client.endpoint == "https://test-app.azurecontainerapps.io/api/chat"
        assert client.api_key == "test-key-123"

    def test_missing_endpoint_raises(self):
        with pytest.raises(ValueError, match="AGENT_ENDPOINT must be set"):
            AgentClient(endpoint="")

    @patch("agent_eval.utils.agent_client.requests.post")
    def test_successful_call(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Hello from container app!",
            "context": "Retrieved from knowledge base",
        }
        mock_post.return_value = mock_response

        client = AgentClient(endpoint="https://test-app.azurecontainerapps.io/api/chat")
        result = client.call("Hi")

        assert result["response"] == "Hello from container app!"
        assert result["context"] == "Retrieved from knowledge base"
        mock_post.assert_called_once()

    @patch("agent_eval.utils.agent_client.requests.post")
    def test_successful_call_with_list_context(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Answer",
            "context": ["source1.pdf", "source2.pdf"],
        }
        mock_post.return_value = mock_response

        client = AgentClient(endpoint="https://test-app.azurecontainerapps.io/api/chat")
        result = client.call("Query")

        assert result["response"] == "Answer"
        assert result["context"] == "source1.pdf\nsource2.pdf"

    @patch("agent_eval.utils.agent_client.requests.post")
    def test_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("500 Server Error")
        mock_post.return_value = mock_response

        client = AgentClient(endpoint="https://test-app.azurecontainerapps.io/api/chat")
        result = client.call("Hi")

        assert "Agent API error" in result["response"]

    @patch("agent_eval.utils.agent_client.requests.post")
    def test_exception_handling(self, mock_post):
        mock_post.side_effect = Exception("Connection refused")

        client = AgentClient(endpoint="https://test-app.azurecontainerapps.io/api/chat")
        result = client.call("Hi")

        assert "Agent API error" in result["response"]

    @patch("agent_eval.utils.agent_client.requests.post")
    def test_bearer_token_auth(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "OK", "context": ""}
        mock_post.return_value = mock_response

        client = AgentClient(
            endpoint="https://test-app.azurecontainerapps.io/api/chat",
            api_key="secret-token",
        )
        client.call("Test")

        # Verify Bearer token in headers
        call_args = mock_post.call_args
        headers = call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer secret-token"
