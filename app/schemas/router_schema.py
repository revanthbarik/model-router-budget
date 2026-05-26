from pydantic import BaseModel


class RouteRequest(BaseModel):
    prompt: str


class RouteResponse(BaseModel):
    answer: str
    difficulty: str
    difficulty_score: int
    difficulty_reasons: list[str]
    selected_tier: str
    selected_model: str
    provider: str
    estimated_cost: float
    latency_ms: float
    budget_status: str
    llm_mode: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
