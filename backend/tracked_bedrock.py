import json
import time
from typing import Any, AsyncGenerator

from strands.models import BedrockModel
from database import log_llm_call

def save_llm_call(
    *,
    venture_name: str,
    agent_name: str,
    model_id: str,
    messages: Any,
    system_prompt: str | None,
    response_events: list[Any],
    latency_ms: float,
    status: str,
    error: str | None = None,
):
    log_llm_call(
        venture_name=venture_name,
        agent_name=agent_name,
        model_id=model_id,
        messages=messages,
        system_prompt=system_prompt,
        response_events=response_events,
        latency_ms=latency_ms,
        status=status,
        error=error
    )

class TrackedBedrockModel(BedrockModel):

    def __init__(
        self,
        *,
        agent_name: str,
        venture_name: str = "Unknown",
        **kwargs,
    ):
        self.agent_name = agent_name
        self.venture_name = venture_name
        super().__init__(**kwargs)

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
                response_events.append(event)
                yield event

            latency_ms = (time.perf_counter() - start_time) * 1000

            save_llm_call(
                venture_name=self.venture_name,
                agent_name=self.agent_name,
                model_id=self.get_config().model_id,
                messages=messages,
                system_prompt=system_prompt,
                response_events=response_events,
                latency_ms=latency_ms,
                status="success",
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000

            save_llm_call(
                venture_name=self.venture_name,
                agent_name=self.agent_name,
                model_id=self.get_config().model_id,
                messages=messages,
                system_prompt=system_prompt,
                response_events=response_events,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )
            raise