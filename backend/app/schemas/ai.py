from pydantic import BaseModel
from typing import Optional, List

class QueryRequest(BaseModel):
    document_id: str
    query: str

class QueryResponse(BaseModel):
    answer: str
    document_id: str

class AnalysisResponse(BaseModel):
    document_id: str
    risk_level: str
    risk_score: int
    summary: str
    detailed_summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    risks: Optional[List[dict]] = None
    clauses: Optional[List[dict]] = None
    parties: Optional[List[str]] = None
    important_dates: Optional[List[dict]] = None
    obligations: Optional[List[dict]] = None
    recommendations: Optional[List[str]] = None
    document_type: Optional[str] = None

class RiskAnalysisResponse(BaseModel):
    risk_level: str
    risk_score: int
    issues: List[dict]
    recommendations: List[str]
    risk_categories: Optional[dict] = None

class SummaryResponse(BaseModel):
    short_summary: str
    detailed_summary: str
    key_points: List[str]
    important_clauses: Optional[List[str]] = None
