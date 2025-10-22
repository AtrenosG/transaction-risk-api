from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from uuid import UUID
import httpx
import os
from datetime import datetime

from models.schemas import (
    APIResponse, MLAnalysisResult, AnalyzeRequest, 
    WebhookPayload, MLResult
)
from services.supabase_service import SupabaseService
from transaction_risk_model import TransactionRiskModel

router = APIRouter(prefix="/api", tags=["analytics"])

# Dependency to get Supabase service
def get_supabase_service() -> SupabaseService:
    return SupabaseService()

# Dependency to get ML model
def get_ml_model() -> TransactionRiskModel:
    return TransactionRiskModel()


@router.get("/analyze", response_model=APIResponse)
async def analyze_transactions(
    account_no: str = Query(..., description="Account number"),
    ifsc: str = Query(..., description="IFSC code"),
    supabase: SupabaseService = Depends(get_supabase_service),
    ml_model: TransactionRiskModel = Depends(get_ml_model)
):
    """
    Analyze user transactions and generate risk assessment
    
    This endpoint:
    1. Fetches user by account_no and ifsc_code
    2. Retrieves 180 days of transaction history
    3. Runs ML analysis to generate risk metrics
    4. Saves results to database
    5. Optionally sends webhook to external service
    6. Returns comprehensive analysis results
    """
    try:
        # Get user by account details
        user = await supabase.get_user_by_account(account_no, ifsc)
        if not user:
            raise HTTPException(
                status_code=404, 
                detail=f"User not found with account_no: {account_no} and ifsc: {ifsc}"
            )
        
        # Get user transactions (last 180 days)
        transactions = await supabase.get_user_transactions(user.id, days=180)
        
        if not transactions:
            raise HTTPException(
                status_code=404,
                detail="No transactions found for the specified user in the last 180 days"
            )
        
        # Run ML analysis
        analysis_result = ml_model.analyze_transactions(transactions)
        
        # Save results to database
        ml_result = await supabase.save_ml_result(user.id, analysis_result)
        if not ml_result:
            raise HTTPException(
                status_code=500,
                detail="Failed to save analysis results to database"
            )
        
        # Send webhook if configured
        webhook_url = os.getenv("WEBHOOK_URL")
        if webhook_url:
            try:
                await send_webhook(user.id, analysis_result, webhook_url)
            except Exception as e:
                print(f"Webhook failed: {e}")
                # Don't fail the main request if webhook fails
        
        return APIResponse(
            success=True,
            data=analysis_result.dict(),
            message=f"Analysis completed successfully for user {user.name}",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during analysis: {str(e)}"
        )


@router.get("/results/{user_id}", response_model=APIResponse)
async def get_user_results(
    user_id: UUID,
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    Get the latest ML analysis results for a specific user
    
    This endpoint is designed for integration with external services
    like the Agentic AI recommender system.
    """
    try:
        # Get latest ML result for user
        ml_result = await supabase.get_latest_ml_result(user_id)
        
        if not ml_result:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis results found for user {user_id}"
            )
        
        return APIResponse(
            success=True,
            data=ml_result.dict(),
            message="Latest analysis results retrieved successfully",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Results retrieval error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error retrieving results: {str(e)}"
        )


@router.post("/webhook", response_model=APIResponse)
async def trigger_webhook(
    user_id: UUID,
    webhook_url: str,
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    Manually trigger webhook for a user's latest analysis results
    
    This is useful for re-sending data to external services or
    sending to different webhook URLs.
    """
    try:
        # Get latest ML result
        ml_result = await supabase.get_latest_ml_result(user_id)
        
        if not ml_result:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis results found for user {user_id}"
            )
        
        # Convert MLResult back to MLAnalysisResult for webhook
        analysis_result = MLAnalysisResult(**ml_result.metrics)
        
        # Send webhook
        await send_webhook(user_id, analysis_result, webhook_url)
        
        return APIResponse(
            success=True,
            data={"webhook_url": webhook_url, "user_id": str(user_id)},
            message="Webhook sent successfully",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Webhook trigger error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send webhook: {str(e)}"
        )


@router.get("/test", response_model=APIResponse)
async def test_endpoint():
    """Simple test endpoint that doesn't require database"""
    return APIResponse(
        success=True,
        data={
            "message": "API is working",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        },
        message="Test endpoint working successfully",
        timestamp=datetime.utcnow()
    )


@router.get("/health", response_model=APIResponse)
async def health_check(
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """Health check endpoint to verify service status"""
    try:
        # Check Supabase connection
        supabase_healthy = await supabase.health_check()
        
        return APIResponse(
            success=True,
            data={
                "status": "healthy",
                "supabase": "connected" if supabase_healthy else "disconnected",
                "ml_model": "ready",
                "supabase_status": supabase_healthy
            },
            message="Service is running" + (" with Supabase" if supabase_healthy else " without Supabase"),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        print(f"Health check error: {e}")
        return APIResponse(
            success=False,
            data={
                "status": "unhealthy",
                "error": str(e)
            },
            message=f"Health check failed: {str(e)}",
            timestamp=datetime.utcnow()
        )


async def send_webhook(user_id: UUID, analysis_result: MLAnalysisResult, webhook_url: str):
    """Send analysis results to external webhook URL"""
    webhook_payload = WebhookPayload(
        user_id=user_id,
        analysis_result=analysis_result,
        timestamp=datetime.utcnow()
    )
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            webhook_url,
            json=webhook_payload.dict(),
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
    print(f"Webhook sent successfully to {webhook_url} for user {user_id}")
