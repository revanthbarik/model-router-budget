from pydantic import BaseModel


class RouteRequest(BaseModel):
    prompt: str


class RouteResponse(BaseModel):
    answer: str
    selected_model: str
    estimated_cost: float
    difficulty: str
