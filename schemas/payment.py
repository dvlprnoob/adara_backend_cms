from pydantic import BaseModel
from datetime import datetime

class UploadProof(BaseModel):
    proof_url: str
    
class InstallmentPaymentResponse(BaseModel):
    id : int
    installment_id : int
    term_number: int
    proof_url : str
    status: str
    created_at : datetime
    approved_at: datetime | None
    
    class config:
        from_attributes = True