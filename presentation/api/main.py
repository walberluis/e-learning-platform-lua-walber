"""
FastAPI main application.
Presentation Layer - API Package
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import os
from dotenv import load_dotenv

# Import routers
from presentation.api.routers import users, trilhas, content, chatbot, recommendations, trilhas_personalizadas

# Import database initialization
from infrastructure.database.connection import init_database

load_dotenv()

# Create FastAPI application
app = FastAPI(
    title="E-Learning System API",
    description="AI-powered e-learning platform with personalized recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="presentation/web/static"), name="static")

# Include API routers
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(trilhas.router, prefix="/api/v1/trilhas", tags=["Learning Paths"])
app.include_router(trilhas_personalizadas.router, prefix="/api/v1/trilhas-personalizadas", tags=["Custom Learning Paths"])
app.include_router(content.router, prefix="/api/v1/content", tags=["Content"])
app.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["AI Chatbot"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["AI Recommendations"])

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    print("🚀 Starting E-Learning System API...")
    
    # Initialize database
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    
    print("🎯 API is ready to serve requests!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    print("🛑 Shutting down E-Learning System API...")
    
    # Close database connections
    from infrastructure.database.connection import close_database
    close_database()
    
    print("✅ Cleanup completed")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    try:
        with open("presentation/web/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="""
            <html>
                <head><title>E-Learning System</title></head>
                <body>
                    <h1>🎓 E-Learning System</h1>
                    <p>Welcome to the AI-powered e-learning platform!</p>
                    <p><a href="/docs">📚 API Documentation</a></p>
                    <p><a href="/redoc">📖 ReDoc Documentation</a></p>
                </body>
            </html>
            """
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "e-learning-api",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.get("/api/v1/status")
async def api_status():
    """API status endpoint with system information."""
    from infrastructure.database.connection import engine
    from infrastructure.integration.message_queue import message_queue
    
    try:
        # Test database connection
        with engine.connect() as conn:
            db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    # Get message queue stats
    queue_stats = message_queue.get_queue_stats()
    
    return {
        "api_status": "operational",
        "database_status": db_status,
        "message_queue_stats": queue_stats,
        "features": {
            "ai_recommendations": True,
            "chatbot": True,
            "progress_tracking": True,
            "content_delivery": True
        }
    }

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # Run the application
    uvicorn.run(
        "presentation.api.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )
