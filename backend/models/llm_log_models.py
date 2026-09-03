from database import Base
from sqlalchemy import Column, Integer, String, Text


class LLMLog(Base):
    __tablename__ = "llm_logs"

    id = Column(Integer, primary_key=True, index=True)

    venture_name = Column(String, nullable=False)
    agent_name = Column(String, nullable=False)
    model_id = Column(String, nullable=False)

    messages = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    reply = Column(Text, nullable=False)

    latency_ms = Column(Integer, nullable=True)
    status = Column(String, nullable=False)
    error = Column(Text, nullable=True)

    # Core Token Metrics
    input_tokens = Column(
        Integer, default=0, server_default="0", nullable=False
    )
    output_tokens = Column(
        Integer, default=0, server_default="0", nullable=False
    )
    total_tokens = Column(
        Integer, default=0, server_default="0", nullable=False
    )