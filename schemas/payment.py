from pydantic import BaseModel

class UploadProof(BaseModel):
    proof_url: str