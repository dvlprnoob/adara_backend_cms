from pydantic import BaseModel, Field

class UploadProof(BaseModel):
    proof_url: str = Field(min_length=1)
