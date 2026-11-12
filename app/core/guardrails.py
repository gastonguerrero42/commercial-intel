import re
INJECTION_PATTERNS=[r'ignore (your|all|previous) (instructions|prompts|rules)',r'jailbreak',r'dan mode',r'no restrictions',r'bypass (your|the) (safety|guardrails|filters)',r'system prompt']
PII_PATTERNS={'email':r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}','credit_card':r'\b(?:\d[ -]*?){13,16}\b','colombian_id':r'\b\d{8,10}\b'}
def check_input_guardrails(query, context=''):
    text=f'{query} {context}'.lower()
    for pat in INJECTION_PATTERNS:
        if re.search(pat, text, re.IGNORECASE): return {'blocked':True,'category':'prompt_injection','reason':f'Injection: {pat}'}
    for label, pat in PII_PATTERNS.items():
        if re.search(pat, query): return {'blocked':True,'category':'pii','reason':f'PII: {label}'}
    if len(query.strip())<5: return {'blocked':True,'category':'invalid_input','reason':'Query too short'}
    return {'blocked':False,'category':'ok','reason':''}
def sanitize_for_logging(text):
    r=text
    for pat in PII_PATTERNS.values(): r=re.sub(pat,'[REDACTED]',r)
    return r[:500]
def validate_report(text):
    numbers=re.findall(r'\$?\d+[.,]?\d*\s?%', text); has_source=('SOURCE' in text or 'Source:' in text); issues=[]
    if numbers and not has_source: issues.append('Numbers without source')
    if len(text)<500: issues.append('Report too short')
    return {'valid':len(issues)==0,'issues':issues,'numbers_found':len(numbers),'has_source':has_source}
