from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from routes.api import router as api_router
from models.schemas import APIResponse
from datetime import datetime

# Load environment variables
load_dotenv()

# Print environment status for debugging
print(f"🔧 SUPABASE_URL: {'✅ Set' if os.getenv('SUPABASE_URL') else '❌ Missing'}")
print(f"🔧 SUPABASE_KEY: {'✅ Set' if os.getenv('SUPABASE_KEY') else '❌ Missing'}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Transaction Risk Analytics API starting up...")
    
    # Verify required environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set these variables before starting the application")
    else:
        print("✅ All required environment variables are set")
    
    print("✅ Application startup complete")
    
    yield
    
    # Shutdown
    print("🛑 Transaction Risk Analytics API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Transaction Risk Scoring & Financial Behavior Analytics",
    description="""
    A comprehensive FastAPI backend that analyzes user transactions to generate detailed risk assessments 
    and financial behavior analytics. This API integrates with Supabase for data storage and provides 
    endpoints for both UI visualization and external service integration.
    
    ## Features
    
    * **Risk Assessment**: Comprehensive analysis of transaction patterns to generate risk scores
    * **Financial Analytics**: Detailed insights into spending patterns, income volatility, and savings behavior
    * **Behavioral Analysis**: Understanding of user financial habits and stability indicators
    * **Loan Eligibility**: Automated assessment based on financial behavior patterns
    * **External Integration**: Webhook support for Agentic AI and other backend services
    
    ## Core Metrics
    
    * Overall Risk Score (0-100 scale)
    * Monthly spending and savings analysis
    * Income and spending volatility
    * Behavioral pattern recognition
    * Transaction frequency analysis
    * Weekend vs weekday spending patterns
    * Essential vs discretionary spending ratios
    
    ## Database Integration
    
    * Supabase PostgreSQL for data persistence
    * Real-time transaction analysis
    * Historical data storage and retrieval
    * Automated result caching
    """,
    version="1.0.0",
    contact={
        "name": "Transaction Risk Analytics Team",
        "email": "support@transactionrisk.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development
        "http://localhost:3001",  # Alternative React port
        "https://*.vercel.app",   # Vercel deployments
        "https://*.netlify.app",  # Netlify deployments
        os.getenv("FRONTEND_URL", ""),  # Custom frontend URL
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint with API information"""
    return APIResponse(
        success=True,
        data={
            "name": "Transaction Risk Scoring & Financial Behavior Analytics API",
            "version": "1.0.0",
            "status": "operational",
            "endpoints": {
                "analyze": "/api/analyze?account_no=...&ifsc=...",
                "results": "/api/results/{user_id}",
                "webhook": "/api/webhook",
                "health": "/api/health",
                "docs": "/docs",
                "redoc": "/redoc"
            },
            "features": [
                "Transaction Risk Analysis",
                "Financial Behavior Analytics",
                "Loan Eligibility Assessment",
                "Real-time Processing",
                "Webhook Integration",
                "Supabase Integration"
            ]
        },
        message="Transaction Risk Analytics API is running successfully",
        timestamp=datetime.utcnow()
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content=APIResponse(
            success=False,
            data=None,
            message=f"Endpoint not found: {request.url.path}",
            timestamp=datetime.utcnow()
        ).dict()
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            data=None,
            message="Internal server error occurred",
            timestamp=datetime.utcnow()
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"🌟 Starting Transaction Risk Analytics API on {host}:{port}")
    print(f"📚 API Documentation available at: http://{host}:{port}/docs")
    print(f"📖 ReDoc Documentation available at: http://{host}:{port}/redoc")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )
