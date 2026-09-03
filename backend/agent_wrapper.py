import json
import time
from typing import Any, AsyncGenerator

from backend.repositories.llm_log_repository import log_llm_call
from strands.models import BedrockModel

def _reconstruct_reply_message(response_events: list[Any]) -> dict[str, Any]:
    """Collapses streaming event fragments into a single coherent Converse message."""
    text_chunks = []
    tool_uses = []
    current_tool = None

    for event in response_events:
        # Dictionary chunks (Bedrock converse_stream format)
        if isinstance(event, dict):
            # 1. Collect streamed text
            text = (
                event.get("contentBlockDelta", {})
                .get("delta", {})
                .get("text")
            )
            if text:
                text_chunks.append(text)

            # 2. Collect tool use initialization
            tool_start = (
                event.get("contentBlockStart", {})
                .get("start", {})
                .get("toolUse")
            )
            if tool_start:
                current_tool = {
                    "toolUseId": tool_start.get("toolUseId"),
                    "name": tool_start.get("name"),
                    "input": "",
                }
                tool_uses.append(current_tool)

            # 3. Collect streaming tool input JSON arguments
            tool_delta = (
                event.get("contentBlockDelta", {})
                .get("delta", {})
                .get("toolUse", {})
                .get("input")
            )
            if tool_delta and current_tool:
                current_tool["input"] += tool_delta

    # Assemble into standard Bedrock message format
    content = []
    if text_chunks:
        content.append({"text": "".join(text_chunks)})

    if tool_uses:
        for tool in tool_uses:
            try:
                parsed_input = json.loads(tool["input"])
            except Exception:
                parsed_input = tool["input"]
            content.append(
                {
                    "toolUse": {
                        "toolUseId": tool["toolUseId"],
                        "name": tool["name"],
                        "input": parsed_input,
                    }
                }
            )

    return {"role": "assistant", "content": content}

def save_llm_call(
    *,
    venture_name: str,
    agent_name: str,
    model_id: str,
    messages: Any,
    system_prompt: str | None,
    reply: str | None,
    latency_ms: float,
    status: str,
    error: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    total_tokens: int = 0,
):
    log_llm_call(
        venture_name=venture_name,
        agent_name=agent_name,
        model_id=model_id,
        messages=messages,
        system_prompt=system_prompt,
        reply=reply,
        latency_ms=int(latency_ms),
        status=status,
        error=error,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )


class TrackedBedrockModel(BedrockModel):

    def __init__(
        self,
        *,
        agent_name: str = "orchestrator",
        venture_name: str = "Unknown",
        **kwargs,
    ):
        self.agent_name = agent_name
        self.venture_name = venture_name
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

            input_tokens = 0
            output_tokens = 0
            total_tokens = 0

            # Find the final Bedrock metadata event
            for event in reversed(response_events):
                metadata = (
                    event.get("metadata")
                    if isinstance(event, dict)
                    else getattr(event, "metadata", None)
                )
                if metadata:
                    usage = (
                        metadata.get("usage", {})
                        if isinstance(metadata, dict)
                        else getattr(metadata, "usage", {})
                    )
                    if usage:
                        get_val = (
                            lambda k: usage.get(k, 0)
                            if isinstance(usage, dict)
                            else getattr(usage, k, 0)
                        )
                        input_tokens = get_val("inputTokens")
                        output_tokens = get_val("outputTokens")
                        total_tokens = get_val("totalTokens")
                        break

            if total_tokens == 0 and (input_tokens > 0 or output_tokens > 0):
                total_tokens = input_tokens + output_tokens

            reply = _reconstruct_reply_message(response_events)

            save_llm_call(
                venture_name=self.venture_name,
                agent_name=self.agent_name,
                model_id=self.get_config().model_id,
                messages=messages,
                system_prompt=system_prompt,
                reply=reply,
                latency_ms=latency_ms,
                status="SUCCESS",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000

            save_llm_call(
                venture_name=self.venture_name,
                agent_name=self.agent_name,
                model_id=self.get_config().model_id,
                messages=messages,
                system_prompt=system_prompt,
                reply=reply,
                latency_ms=latency_ms,
                status="FAILED",
                error=str(e),
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
            )
            raise