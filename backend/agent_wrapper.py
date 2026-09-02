# backend/tracked_bedrock.py

import json
import time
from typing import Any, AsyncGenerator

from strands.models import BedrockModel


def save_llm_call(
    *,
    agent_name: str,
    model_id: str,
    messages: Any,
    system_prompt: str | None,
    response_events: list[Any],
    latency_ms: float,
    status: str,
    error: str | None = None,
):
    """
    Temporary database stub.

    Replace the body of this function with your actual
    database INSERT later.
    """

    record = {
        "agent_name": agent_name,
        "model_id": model_id,
        "messages": messages,
        "system_prompt": system_prompt,
        "response_events": response_events,
        "latency_ms": latency_ms,
        "status": status,
        "error": error,
    }

    # Temporary:
    print("\n========== LLM CALL LOG ==========")
    print(json.dumps(record, indent=2, default=str))
    print("==================================\n")


# ============================================================
# TRACKED BEDROCK MODEL
# ============================================================

class TrackedBedrockModel(BedrockModel):

    def __init__(
        self,
        *,
        agent_name: str,
        **kwargs,
    ):
        self.agent_name = agent_name

        super().__init__(**kwargs)

    # --------------------------------------------------------
    # Intercept every model invocation
    # --------------------------------------------------------

    async def stream(
        self,
        messages,
        tool_specs=None,
        system_prompt=None,
        *,
        tool_choice=None,
        system_prompt_content=None,
        invocation_state=None,
        cancel_signal=None,
        **kwargs,
    ) -> AsyncGenerator[Any, None]:

        start_time = time.perf_counter()

        response_events = []

        try:
            # Call the REAL BedrockModel
            async for event in super().stream(
                messages=messages,
                tool_specs=tool_specs,
                system_prompt=system_prompt,
                tool_choice=tool_choice,
                system_prompt_content=system_prompt_content,
                invocation_state=invocation_state,
                cancel_signal=cancel_signal,
                **kwargs,
            ):

                # Keep a copy for logging
                response_events.append(event)

                # IMPORTANT:
                # Still yield the event to Strands.
                #
                # This means the wrapper does not interfere
                # with normal Agent behavior.
                yield event

            latency_ms = (
                time.perf_counter() - start_time
            ) * 1000

            save_llm_call(
                agent_name=self.agent_name,
                model_id=self.get_config().model_id,
                messages=messages,
                system_prompt=system_prompt,
                response_events=response_events,
                latency_ms=latency_ms,
                status="success",
            )

        except Exception as e:

            latency_ms = (
                time.perf_counter() - start_time
            ) * 1000

            save_llm_call(
                agent_name=self.agent_name,
                model_id=self.get_config().model_id,
                messages=messages,
                system_prompt=system_prompt,
                response_events=response_events,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )

            # VERY IMPORTANT:
            # Do not swallow the exception.
            raise