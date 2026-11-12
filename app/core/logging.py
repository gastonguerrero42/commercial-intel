import structlog, logging
def setup_logging():
    structlog.configure(processors=[structlog.processors.TimeStamper(fmt='iso'), structlog.processors.JSONRenderer()], wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))
def get_logger(name='app'): return structlog.get_logger(name)
