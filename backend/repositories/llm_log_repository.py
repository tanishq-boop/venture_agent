import json
import logging
from database import SessionLocal
from models import LLMLog

logger = logging.getLogger(__name__)


def log_llm_call(
    venture_name,
    agent_name,
    model_id,
    messages,
    system_prompt,
    response_events,
    latency_ms,
    status,
    error=None,
):
    """Safely records an LLM call in an isolated database session."""
    db = SessionLocal()
    try:
        llm_log = LLMLog(
            venture_name=venture_name,
            agent_name=agent_name,
            model_id=model_id,
            messages=json.dumps(messages, default=str),
            system_prompt=system_prompt,
            response_events=json.dumps(response_events, default=str),
            latency_ms=latency_ms,
            status=status,
            error=error,
        )
        db.add(llm_log)
        db.commit()
        return llm_log
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to log LLM call to DB: {e}")
        return None
    finally:
        db.close()