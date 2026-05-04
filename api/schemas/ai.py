from typing import Any, Optional

from pydantic import BaseModel

class RefineConfigRequest(BaseModel):
    project_id: Optional[str] = None
    trade: Optional[str] = None
    prompt: str
    save: bool = False

    prompt: str
    save: bool = False

class RefineConfigResponse(BaseModel):
    updated_config: dict[str, Any]
    message: str
