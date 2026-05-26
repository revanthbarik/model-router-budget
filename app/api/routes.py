import time

#importing from fastapi
from fastapi import APIRouter, HTTPException

#importing functions from services, schemas and config
from app.config import MAX_PROMPT_CHARS, get_llm_provider
from app.schemas.router_schema import RouteRequest, RouteResponse
from app.services.cost_calculator import calculate_real_cost, estimate_cost_for_model
from app.services.budget_manager import check_budget, get_budget_status
from app.services.difficulty_estimator import estimate_difficulty
from app.services.llm_client import call_llm
from app.services.model_router import choose_model
from app.services.request_logger import get_logs, get_metrics, log_request

#creating a router for the api for organization of routes
router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "api router in the backend is running",
    }


@router.get("/budget")
def budget_status():
    return get_budget_status()


@router.get("/logs")
def logs():
    return get_logs()


@router.get("/metrics")
def metrics():
    return get_metrics()


@router.post("/route", response_model=RouteResponse)
def route_prompt(request: RouteRequest): 
    start_time = time.perf_counter()
    prompt = request.prompt.strip()
    provider = get_llm_provider()

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    if len(prompt) > MAX_PROMPT_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"Prompt is too long. Max length is {MAX_PROMPT_CHARS} characters.",
        )

    difficulty_result = estimate_difficulty(prompt)
    model_result = choose_model(difficulty_result["difficulty"], provider)
    pre_call_cost = estimate_cost_for_model(
        prompt=prompt,
        selected_model=model_result["selected_model"],
        selected_tier=model_result["selected_tier"],
    )
    budget_result = check_budget(estimated_cost=pre_call_cost)

    if budget_result["budget_status"] == "blocked":
        end_time = time.perf_counter()
        latency_ms = round((end_time - start_time) * 1000, 2)
        blocked_answer = "Budget exceeded — request was not routed to the LLM."

        log_request(
            prompt=prompt,
            answer=blocked_answer,
            provider=model_result["provider"],
            difficulty=difficulty_result["difficulty"],
            difficulty_score=difficulty_result["score"],
            selected_tier=model_result["selected_tier"],
            selected_model=model_result["selected_model"],
            estimated_cost=pre_call_cost,
            billable_cost=0.0,
            latency_ms=latency_ms,
            budget_status="blocked",
            llm_mode="not_called",
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
        )

        return {
            "answer": blocked_answer,
            "difficulty": difficulty_result["difficulty"],
            "difficulty_score": difficulty_result["score"],
            "difficulty_reasons": difficulty_result["reasons"],
            "selected_tier": model_result["selected_tier"],
            "selected_model": model_result["selected_model"],
            "provider": model_result["provider"],
            "estimated_cost": pre_call_cost,
            "latency_ms": latency_ms,
            "budget_status": "blocked",
            "llm_mode": "not_called",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

    llm_result = call_llm(
        prompt=prompt,
        selected_model=model_result["selected_model"],
        provider=model_result["provider"],
    )

    if llm_result["input_tokens"] > 0 or llm_result["output_tokens"] > 0:
        final_cost = calculate_real_cost(
            selected_model=model_result["selected_model"],
            input_tokens=llm_result["input_tokens"],
            output_tokens=llm_result["output_tokens"],
            prompt=prompt,
            selected_tier=model_result["selected_tier"],
        )
    else:
        final_cost = pre_call_cost

    billable_cost = final_cost if model_result["provider"] in {"openai", "deepseek"} and llm_result["llm_mode"] in {"openai", "deepseek"} else 0.0

    end_time = time.perf_counter()
    latency_ms = round((end_time - start_time) * 1000, 2)

    log_request(
        prompt=prompt,
        answer=llm_result["answer"],
        provider=model_result["provider"],
        difficulty=difficulty_result["difficulty"],
        difficulty_score=difficulty_result["score"],
        selected_tier=model_result["selected_tier"],
        selected_model=model_result["selected_model"],
        estimated_cost=final_cost,
        billable_cost=billable_cost,
        latency_ms=latency_ms,
        budget_status="allowed",
        llm_mode=llm_result["llm_mode"],
        input_tokens=llm_result["input_tokens"],
        output_tokens=llm_result["output_tokens"],
        total_tokens=llm_result["total_tokens"],
    )

    return {
        "answer": llm_result["answer"],
        "difficulty": difficulty_result["difficulty"],
        "difficulty_score": difficulty_result["score"],
        "difficulty_reasons": difficulty_result["reasons"],
        "selected_tier": model_result["selected_tier"],
        "selected_model": model_result["selected_model"],
        "provider": model_result["provider"],
        "estimated_cost": final_cost,
        "latency_ms": latency_ms,
        "budget_status": "allowed",
        "llm_mode": llm_result["llm_mode"],
        "input_tokens": llm_result["input_tokens"],
        "output_tokens": llm_result["output_tokens"],
        "total_tokens": llm_result["total_tokens"],
    }
