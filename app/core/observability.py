import os
def setup_observability():
    if os.getenv('PHOENIX_ENABLED','true').lower()=='true':
        try:
            import phoenix as px; px.launch_app(); print('Phoenix at http://localhost:6006')
        except Exception as e: print(f'Phoenix unavailable: {e}')
