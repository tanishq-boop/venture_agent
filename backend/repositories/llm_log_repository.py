from datetime import datetime
import json
import logging
from time import timezone
from database import SessionLocal
from models import LLMLog
from sqlalchemy import func

logger = logging.getLogger(__name__)


def log_llm_call(
    venture_name: str,
    agent_name: str,
    model_id: str,
    messages: list | dict | str,
    reply: str,
    status: str,
    system_prompt: str | None = None,
    latency_ms: int | None = None,
    error: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    total_tokens: int = 0,
) -> LLMLog | None:
    """Records an LLM execution and stores exact input, output, and total tokens."""
    # Fallback to sum input + output if total was not directly provided
    if total_tokens == 0 and (input_tokens > 0 or output_tokens > 0):
        total_tokens = input_tokens + output_tokens

    db = SessionLocal()
    try:
        llm_log = LLMLog(
            venture_name=venture_name,
            agent_name=agent_name,
            model_id=model_id,
            messages=json.dumps(messages, default=str)
            if not isinstance(messages, str)
            else messages,
            system_prompt=system_prompt,
            reply=reply,
            latency_ms=latency_ms,
            status=status,
            error=error,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            created_at=datetime.now(timezone.utc),
        )
        db.add(llm_log)
        db.commit()
        db.refresh(llm_log)
        return llm_log
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to log LLM call: {e}")
        return None
    finally:
        db.close()


def get_token_usage_summary() -> dict:
    """Aggregates input, output, and total tokens consumed across all successful calls."""
    db = SessionLocal()
    try:
        stats = (
            db.query(
                func.coalesce(func.sum(LLMLog.input_tokens), 0).label("input"),
                func.coalesce(func.sum(LLMLog.output_tokens), 0).label("output"),
                func.coalesce(func.sum(LLMLog.total_tokens), 0).label("total"),
                func.count(LLMLog.id).label("calls"),
            )
            .filter(LLMLog.status == "SUCCESS")
            .one()
        )

        return {
            "total_calls": int(stats.calls),
            "tokens_consumed": {
                "input_tokens": int(stats.input),
                "output_tokens": int(stats.output),
                "total_tokens": int(stats.total),
            },
        }
    except Exception as e:
        logger.error(f"Failed to aggregate token usage: {e}")
        return {}
    finally:
        db.close()