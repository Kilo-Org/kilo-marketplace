#!/usr/bin/env python3
"""
Approval handler for tool prediction and user approval flow.
Predicts which tools Cortex needs and formats approval prompts for users.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Add scripts directory to path for predict_tools import
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from predict_tools import predict_tools as predict_tools_func


@dataclass
class ApprovalResult:
    """Result of approval process."""
    approved: bool
    allowed_tools: List[str]
    user_response: str


class ApprovalHandler:
    """
    Handles tool prediction and user approval flow.

    Predicts which tools Cortex needs based on user prompts,
    formats approval prompts with confidence scores and warnings,
    and parses user responses.
    """

    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize approval handler.

        Args:
            confidence_threshold: Minimum confidence for predictions (default 0.7)
        """
        self.confidence_threshold = confidence_threshold

    def predict_tools(self, prompt: str, envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict which tools will be needed for the given prompt.

        Args:
            prompt: User prompt to analyze
            envelope: Request envelope with capabilities and context

        Returns:
            dict with:
                - tools: list of predicted tool names
                - confidence: float 0-1 indicating prediction confidence
                - reasoning: str explaining the prediction
        """
        return predict_tools_func(prompt, envelope)

    def format_approval_prompt(
        self,
        tools: List[str],
        confidence: float,
        envelope: Dict[str, Any],
        reasoning: str
    ) -> str:
        """
        Format approval prompt for user.

        Args:
            tools: List of predicted tool names
            confidence: Prediction confidence (0-1)
            envelope: Request envelope with user_prompt and context
            reasoning: Explanation of tool prediction

        Returns:
            Formatted approval prompt string
        """
        user_prompt = envelope.get("user_prompt", "Unknown request")

        # Build approval prompt
        lines = []
        lines.append("=" * 70)
        lines.append("CORTEX TOOL APPROVAL REQUEST")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"User Request: {user_prompt}")
        lines.append("")
        lines.append(f"Predicted Tools ({len(tools)}):")
        for tool in tools:
            lines.append(f"  - {tool}")
        lines.append("")
        lines.append(f"Prediction Confidence: {confidence:.0%}")
        lines.append(f"Reasoning: {reasoning}")
        lines.append("")

        # Add warning if confidence is below threshold
        if confidence < self.confidence_threshold:
            lines.append("⚠️  WARNING: Low confidence prediction!")
            lines.append(f"   Confidence {confidence:.0%} is below threshold {self.confidence_threshold:.0%}")
            lines.append("   Tool predictions may be uncertain or incomplete.")
            lines.append("")

        lines.append("=" * 70)
        lines.append("APPROVAL OPTIONS:")
        lines.append("  approve      - Allow these specific tools for this request")
        lines.append("  approve_all  - Allow all tools (bypass future approvals)")
        lines.append("  deny         - Reject this request")
        lines.append("=" * 70)
        lines.append("")
        lines.append("Your response: ")

        return "\n".join(lines)

    def parse_user_response(self, response: str) -> ApprovalResult:
        """
        Parse user response to approval prompt.

        Args:
            response: User's response string

        Returns:
            ApprovalResult with approval decision and allowed tools
        """
        response_lower = response.strip().lower()

        if response_lower == "approve":
            return ApprovalResult(
                approved=True,
                allowed_tools=[],  # Will be filled by caller with predicted tools
                user_response="approve"
            )
        elif response_lower == "approve_all":
            return ApprovalResult(
                approved=True,
                allowed_tools=["*"],  # Wildcard for all tools
                user_response="approve_all"
            )
        elif response_lower == "deny":
            return ApprovalResult(
                approved=False,
                allowed_tools=[],
                user_response="deny"
            )
        else:
            # Unknown response - treat as deny for safety
            return ApprovalResult(
                approved=False,
                allowed_tools=[],
                user_response=response
            )
