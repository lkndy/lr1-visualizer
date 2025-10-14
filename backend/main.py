"""Main FastAPI application entry point."""

from api.routes import router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Create FastAPI app
app = FastAPI(
    title="LR(1) Parser Visualizer API",
    description="Interactive LR(1) parser visualizer with step-by-step execution",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "LR(1) Parser Visualizer"}


# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    """Root endpoint with basic information."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LR(1) Parser Visualizer API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .method { font-weight: bold; color: #0066cc; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>LR(1) Parser Visualizer API</h1>
            <p>Welcome to the LR(1) Parser Visualizer API. This service provides
            endpoints for:</p>
            <div class="endpoint">
                <span class="method">POST</span> /api/v1/grammar/validate - Validate grammar
                definitions
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /api/v1/parser/table - Generate parsing
                tables
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /api/v1/parser/parse - Parse input strings
            </div>
            <div class="endpoint">
                <span class="method">GET</span> /api/v1/examples - Get example grammars
            </div>
            <div class="endpoint">
                <span class="method">WebSocket</span> /api/v1/ws/parse - Real-time parsing
                updates
            </div>
            <p><a href="/api/docs">View API Documentation</a></p>
            <p><a href="/health">Health Check</a></p>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
