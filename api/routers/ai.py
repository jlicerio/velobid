import json
import logging

from fastapi import APIRouter, HTTPException
from openai import APITimeoutError, APIConnectionError, APIError

from api.schemas.ai import RefineConfigRequest, RefineConfigResponse
from api.services.ai import refine_config, check_llm_health
from api.services.bids import (
    PROJECTS_DIR,
    TRADES_DIR,
    read_json,
    resolve_project_path,
    resolve_trade_path,
)

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

logger = logging.getLogger(__name__)


@router.post("/refine", response_model=RefineConfigResponse)
def ai_refine_config(request: RefineConfigRequest) -> RefineConfigResponse:
    """Refine a project or trade configuration using AI."""
    try:
        if request.project_id:
            path = resolve_project_path(request.project_id)
            current_config = read_json(path)
        elif request.trade:
            path = resolve_trade_path(request.trade)
            current_config = read_json(path)
        else:
            raise HTTPException(status_code=400, detail="Must provide either project_id or trade")

        # Pre-call health check - fail fast if LLM endpoint is unreachable
        check_llm_health()

        updated = refine_config(current_config, request.prompt)

        if request.save:
            with path.open("w", encoding="utf-8") as f:
                json.dump(updated, f, indent=2)
            message = f"Successfully updated and saved {path.name}"
        else:
            message = "Preview of AI refinement (not saved)"

        return RefineConfigResponse(updated_config=updated, message=message)

    except APITimeoutError as error:
        logger.error("AI refine request timed out: %s", error)
        raise HTTPException(
            status_code=504,
            detail="AI request timed out. The service is taking too long to respond. Please try again.",
        ) from error
    except APIConnectionError as error:
        logger.error("AI service connection failed: %s", error)
        raise HTTPException(
            status_code=503,
            detail="AI service is currently unavailable. Please try again later.",
        ) from error
    except APIError as error:
        logger.error("AI service returned an error: %s", error)
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {error}",
        ) from error
    except HTTPException:
        raise
    except Exception as error:
        logger.error("Unexpected error in AI refine endpoint: %s", error)
        raise HTTPException(status_code=500, detail=str(error)) from error

