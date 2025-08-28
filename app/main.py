from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from datetime import datetime
import os
from app.config import settings
from app.logging.logging_config import setup_logging, get_logger, log_startup_info, log_shutdown_info
from app.controllers import chat_controller

# Setup logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    enable_file_logging=True,
    enable_console_logging=True
)

logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-AdaptLearn: An AI-driven adaptive learning platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and their responses."""
    start_time = datetime.now()
    
    # Log request
    logger.info(f"🌐 {request.method} {request.url.path} - Client: {request.client.host if request.client else 'Unknown'}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"✅ {request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.3f}s")
    
    return response

# Include routers
app.include_router(chat_controller.router)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    try:
        # Log startup information
        log_startup_info()
        
        # Persistence disabled; skip DB tables creation
        logger.info("ℹ️ Persistence disabled - skipping DB table creation")
        
        # Validate OpenAI API key
        if not settings.OPENAI_API_KEY:
            logger.warning("⚠️  Warning: OpenAI API key not configured")
        else:
            logger.info("✅ OpenAI API key configured")
            
        logger.info(f"🚀 {settings.APP_NAME} started successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    try:
        logger.info("🔄 Shutting down AI-AdaptLearn application...")
        log_shutdown_info()
        logger.info("✅ Application shutdown completed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application page."""
    try:
        logger.info("🌐 Serving main application page")
        with open("frontend/index.html", "r") as f:
            content = f.read()
            logger.info("✅ Main page served successfully")
            return HTMLResponse(content=content)
    except FileNotFoundError:
        logger.warning("⚠️  Frontend file not found, serving fallback page")
        return HTMLResponse(content="""
        <html>
            <head><title>AI-AdaptLearn</title></head>
            <body>
                <h1>AI-AdaptLearn Backend</h1>
                <p>The backend is running successfully!</p>
                <p><a href="/api/docs">View API Documentation</a></p>
            </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("🏥 Health check requested")
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0"
    }

@app.get("/api")
async def api_info():
    """API information endpoint."""
    logger.debug("📚 API info requested")
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "description": "AI-AdaptLearn API",
        "endpoints": {
            "docs": "/api/docs",
            "users": "/api/users",
            "settings": "/api/settings",
            "chat": "/api/chat",
            "questions": "/api/questions",
            "simulation": "/api/questions/simulation",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
