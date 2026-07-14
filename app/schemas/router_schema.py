from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    prompt: str
    force_run: bool = False


class BudgetLimitUpdate(BaseModel):
    limit: float = Field(..., gt=0, description="New monthly budget limit in USD.")
    reset_usage: bool = Field(
        default=True,
        description="When true, clear request logs so spend resets to $0.00.",
    )


class BudgetWarningResponse(BaseModel):
    status: str = "budget_warning"
    message: str
    estimated_cost: float
    remaining_budget: float


class RouteResponse(BaseModel):
    answer: str
    difficulty: str
    difficulty_score: int
    difficulty_reasons: list[str]
    selected_tier: str
    selected_model: str
    provider: str
    estimated_input_tokens: int
    estimated_cost: float = Field(
        description="Pre-call estimated input cost used for budget gating."
    )
    billable_cost: float = Field(
        description="Actual billable cost from provider usage (input + output)."
    )
    latency_ms: float
    budget_status: str
    llm_mode: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
