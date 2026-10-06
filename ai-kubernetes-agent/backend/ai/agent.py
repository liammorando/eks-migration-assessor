"""AI Agent - orchestrates LLM reasoning for Kubernetes troubleshooting."""

import json
from typing import Any

from ai.llm_client import LLMClient, OpenRouterError, get_llm_client
from ai.prompt_builder import build_investigation_prompt
from core.logging import logger


class AIError(Exception):
    """Custom exception for AI agent errors."""
    pass


class AIKubernetesAgent:
    """AI agent for Kubernetes root cause analysis."""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client or get_llm_client()

    def diagnose(self, investigation: dict[str, Any]) -> dict[str, Any]:
        """Run AI diagnosis on investigation evidence."""
        logger.info("Starting AI diagnosis...")

        try:
            # Build prompt
            messages = build_investigation_prompt(investigation)

            # Call LLM
            response = self.llm_client.chat_completion_sync(messages, max_tokens=4000)

            # Parse response
            diagnosis = self._parse_response(response)

            logger.info(f"AI diagnosis complete: {diagnosis.get('root_cause', 'unknown')} (confidence: {diagnosis.get('confidence', 0)}%)")
            return diagnosis

        except OpenRouterError as e:
            logger.error(f"OpenRouter error: {e}")
            raise AIError(f"LLM API error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise AIError(f"Failed to parse AI response: {str(e)}")
        except Exception as e:
            logger.error(f"AI diagnosis failed: {e}")
            raise AIError(f"Diagnosis failed: {str(e)}")

    def _parse_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """Parse LLM response into structured diagnosis."""
        # Extract content from OpenRouter response
        choices = response.get("choices", [])
        if not choices:
            raise AIError("No choices in LLM response")

        content = choices[0].get("message", {}).get("content", "").strip()

        # Try to parse JSON
        try:
            diagnosis = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
                diagnosis = json.loads(content)
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
                diagnosis = json.loads(content)
            else:
                raise AIError(f"LLM response is not valid JSON: {content[:200]}")

        # Validate required fields
        required = ["root_cause", "explanation", "fix", "kubectl_commands", "prevention", "confidence"]
        for field in required:
            if field not in diagnosis:
                raise AIError(f"Missing required field in diagnosis: {field}")

        # Ensure confidence is int
        try:
            diagnosis["confidence"] = int(diagnosis["confidence"])
        except (ValueError, TypeError):
            diagnosis["confidence"] = 0

        # Clamp confidence
        diagnosis["confidence"] = max(0, min(100, diagnosis["confidence"]))

        # Ensure kubectl_commands is list
        if not isinstance(diagnosis["kubectl_commands"], list):
            diagnosis["kubectl_commands"] = [str(diagnosis["kubectl_commands"])]

        return diagnosis


def run_diagnosis(investigation: dict[str, Any]) -> dict[str, Any]:
    """Convenience function to run AI diagnosis."""
    agent = AIKubernetesAgent()
    return agent.diagnose(investigation)
