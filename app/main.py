from fastapi import FastAPI
from app.api.routes import router
from app.core.logging import setup_logging
from app.core.observability import setup_observability
setup_logging(); setup_observability()
app=FastAPI(title='Commercial Intelligence - CrewAI v2.1', version='2.1.0')
app.include_router(router, prefix='/api/v1')
@app.get('/health')
def health(): return {'status':'ok','version':'2.1.0'}
