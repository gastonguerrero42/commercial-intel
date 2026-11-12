from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.crews.commercial_intel.crew import CommercialIntelCrew
from app.core.guardrails import check_input_guardrails, validate_report, sanitize_for_logging
from app.core.store import REPORTS
from app.core.logging import get_logger
import uuid, shutil
log=get_logger('api'); router=APIRouter()
class AnalyzeRequest(BaseModel):
    query: str; company: str='Demo Company'; context: str=''
class ApproveRequest(BaseModel):
    approved: bool; feedback: str=''
@router.post('/analyze')
async def analyze(req: AnalyzeRequest):
    guard=check_input_guardrails(req.query, req.context)
    if guard['blocked']: raise HTTPException(400, f"Blocked [{guard['category']}]: {guard['reason']}")
    rid=str(uuid.uuid4())[:8]
    try:
        crew=CommercialIntelCrew().crew(); raw=crew.kickoff(inputs={'query':req.query,'company':req.company,'context':req.context}).raw
    except Exception as e: raise HTTPException(500, f'Crew failed: {e}')
    validation=validate_report(raw); REPORTS[rid]={'status':'DRAFT','report':raw,'validation':validation,'query':req.query,'company':req.company,'feedback':''}
    return {'report_id':rid,'status':'DRAFT','validation':validation,'report':raw}
@router.get('/reports/{report_id}')
async def get_report(report_id: str):
    if report_id not in REPORTS: raise HTTPException(404,'Not found')
    return {'report_id':report_id, **REPORTS[report_id]}
@router.post('/reports/{report_id}/approve')
async def approve(report_id: str, req: ApproveRequest):
    if report_id not in REPORTS: raise HTTPException(404,'Not found')
    REPORTS[report_id]['status']='APPROVED' if req.approved else 'REJECTED'; REPORTS[report_id]['feedback']=req.feedback
    return {'report_id':report_id,'status':REPORTS[report_id]['status']}
@router.post('/ingest')
async def ingest(file: UploadFile=File(...)):
    path=f'data/docs/{file.filename}'
    with open(path,'wb') as f: shutil.copyfileobj(file.file,f)
    from app.tools.rag_tool import ingest_document; return {'file':file.filename,'chunks':ingest_document(path)}
