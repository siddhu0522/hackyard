from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ApiSpecificationCreate(BaseModel):
    name: str = Field(..., description="API Name, e.g. Customer API")
    version: str = Field(..., description="API Version, e.g. 1.2.0")
    content: str = Field(..., description="OpenAPI spec content in JSON or YAML string")
    format: str = Field("json", description="Spec format: json or yaml")
    source_type: str = Field("upload", description="Source: upload, url, or github")
    source_url: Optional[str] = None

class ApiSpecificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    version: str
    format: str
    source_type: str
    source_url: Optional[str] = None
    created_at: datetime
    content_json: str
