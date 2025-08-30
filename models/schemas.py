from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    query: str

class UploadStatus(BaseModel):
    message: str
    index_name: str