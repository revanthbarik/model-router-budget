from fastapi import APIRouter

from app.schemas.router_schema import RouteRequest, RouteResponse


router = APIRouter()

@router.get("/health")
def health_check():
    return{
        
           "status": "ok",
           "message": "api router in the backend is running"
        }

@router.post("/route", response_model = RouteResponse)
def route_prompt(request: RouteRequest ):
    return {
         "answer": request.prompt,
         "selected_model": "default_model",
         "estimated_cost": 0.0,
         "difficulty": "medium",
         "selected_tier": "standard",
         "latency_ms": 100.0,
         "budget_status": "within_budget"
    }
    