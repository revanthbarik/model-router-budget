import time

from fastapi import APIRouter, HTTPException

from app.config import MAX_PROMPT_CHARS, get_llm_provider
from app.database import probe_database
from app.schemas.router_schema import BudgetLimitUpdate, RouteRequest
from app.services.budget_manager import (
    check_budget,
    get_budget_status,
    update_monthly_budget,
)
from app.services.cost_calculator import (
    calculate_cost_breakdown,
    estimate_input_cost_for_model,
    estimate_input_tokens,
)
from app.services.difficulty_estimator import estimate_difficulty
from app.services.llm_client import call_llm
from app.services.model_router import choose_model
from app.services.request_logger import get_logs, get_metrics, log_request

router = APIRouter()


@router.get("/health")
def health_check():
    db = probe_database()
    ready = db["database"] == "ready"
    return {
        "status": "ok" if ready else "degraded",
        "message": "api router in the backend is running",
        "database": db["database"],
        "error": db["error"],
    }


@router.get("/budget")
def budget_status():
    return get_budget_status()


def _apply_budget_limit(body: BudgetLimitUpdate):
    try:
        return update_monthly_budget(
            new_limit=body.limit,
            reset_usage=body.reset_usage,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/api/budget/limit")
def patch_budget_limit(body: BudgetLimitUpdate):
    """Admin control: set the monthly budget limit (optionally reset spend)."""
    return _apply_budget_limit(body)


@router.post("/api/budget/limit")
def post_budget_limit(body: BudgetLimitUpdate):
    """Same as PATCH — available for clients that prefer POST."""
    return _apply_budget_limit(body)


@router.get("/logs")
def logs():
    return get_logs()


@router.get("/metrics")
def metrics():
    return get_metrics()


@router.post("/route")
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
    estimated_input_tokens = estimate_input_tokens(prompt)
    # Budget gate uses estimated *input* cost only — output is unknown pre-call.
    pre_call_input_cost = estimate_input_cost_for_model(
        prompt=prompt,
        selected_model=model_result["selected_model"],
        selected_tier=model_result["selected_tier"],
    )
    budget_result = check_budget(estimated_cost=pre_call_input_cost)

    # Soft gate: warn + let the UI offer bypass via force_run.
    if budget_result["budget_status"] == "blocked" and not request.force_run:
        return {
            "status": "budget_warning",
            "message": "This prompt is estimated to exceed your remaining budget.",
            "estimated_cost": pre_call_input_cost,
            "remaining_budget": budget_result["remaining_budget"],
        }

    llm_result = call_llm(
        prompt=prompt,
        selected_model=model_result["selected_model"],
        provider=model_result["provider"],
    )

    actual_input = llm_result["input_tokens"]
    actual_output = llm_result["output_tokens"]
    is_billable = (
        model_result["provider"] in {"openai", "deepseek"}
        and llm_result["llm_mode"] in {"openai", "deepseek"}
    )

    if is_billable and (actual_input > 0 or actual_output > 0):
        costs = calculate_cost_breakdown(
            selected_model=model_result["selected_model"],
            input_tokens=actual_input,
            output_tokens=actual_output,
        )
        input_cost = costs["input_cost"]
        output_cost = costs["output_cost"]
        billable_cost = costs["total_cost"]
    else:
        # Fake / fallback paths are not charged against the monthly budget.
        input_cost = 0.0
        output_cost = 0.0
        billable_cost = 0.0

    was_forced = budget_result["budget_status"] == "blocked" and request.force_run
    final_budget_status = "forced" if was_forced else "allowed"

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
        estimated_cost=pre_call_input_cost,
        billable_cost=billable_cost,
        latency_ms=latency_ms,
        budget_status=final_budget_status,
        llm_mode=llm_result["llm_mode"],
        input_tokens=actual_input,
        output_tokens=actual_output,
        total_tokens=llm_result["total_tokens"],
    )

    return {
        "status": "success",
        "answer": llm_result["answer"],
        "difficulty": difficulty_result["difficulty"],
        "difficulty_score": difficulty_result["score"],
        "difficulty_reasons": difficulty_result["reasons"],
        "selected_tier": model_result["selected_tier"],
        "selected_model": model_result["selected_model"],
        "provider": model_result["provider"],
        "estimated_input_tokens": estimated_input_tokens,
        "estimated_cost": pre_call_input_cost,
        "billable_cost": billable_cost,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "actual_cost": billable_cost,
        "forced": was_forced,
        "latency_ms": latency_ms,
        "budget_status": final_budget_status,
        "llm_mode": llm_result["llm_mode"],
        "input_tokens": actual_input,
        "output_tokens": actual_output,
        "total_tokens": llm_result["total_tokens"],
    }
