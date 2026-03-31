"""Client for calling a custom agent via REST API."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


class AgentClient:
    """Sends prompts to a custom agent deployed in Container App via REST API."""

    def __init__(self, endpoint=None, api_key=None):
        self.endpoint = endpoint or os.getenv("AGENT_ENDPOINT", "")
        self.api_key = api_key or os.getenv("AGENT_API_KEY", "")

        if not self.endpoint:
            raise ValueError(
                "AGENT_ENDPOINT must be set in .env or passed to constructor"
            )

    def call(self, query, conversation_id="eval-test"):
        """
        Send a query to the container app agent via REST API.

        Posts the user message to the agent endpoint and extracts the response.

        Args:
            query: The user query to send
            conversation_id: Optional conversation ID (default: "eval-test")

        Returns:
            dict with keys: response (str), context (str)
        """
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            payload = {"query": query, "conversation_id": conversation_id}

            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=120,
            )

            response.raise_for_status()
            data = response.json()

            # Extract answer and sources from the API response
            assistant_reply = data.get("answer", "")
            sources = data.get("sources", [])

            # Format sources as context string with actual content
            if isinstance(sources, list):
                if sources:
                    # Extract preview text from each source for groundedness evaluation
                    context_parts = []
                    for idx, src in enumerate(sources, 1):
                        if isinstance(src, dict):
                            title = src.get("title", src.get("file_name", "Unknown"))
                            preview = src.get("preview", "")

                            # Format: [Source N: title]\npreview text\n
                            context_parts.append(f"[Source {idx}: {title}]")
                            if preview:
                                context_parts.append(preview)
                            context_parts.append("")  # Blank line between sources
                        else:
                            context_parts.append(str(src))
                    context = "\n".join(context_parts).strip()
                else:
                    context = ""
            else:
                context = str(sources) if sources else ""

            return {
                "response": assistant_reply if assistant_reply else "",
                "context": context,
            }

        except requests.exceptions.RequestException as e:
            return {"response": f"Agent API error: {str(e)}", "context": ""}
        except Exception as e:
            return {"response": f"Agent error: {str(e)}", "context": ""}
