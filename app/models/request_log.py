"""Starter placeholder for a request log model."""

from pydantic import BaseModel


class RequestLog(BaseModel):
    prompt: str
    selected_model: str
