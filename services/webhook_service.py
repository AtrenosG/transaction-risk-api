import httpx
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os

from models.schemas import WebhookPayload, MLAnalysisResult
from uuid import UUID


class WebhookService:
    def __init__(self):
        self.timeout = 30.0
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
    async def send_webhook(self, 
                          webhook_url: str, 
                          user_id: UUID, 
                          analysis_result: MLAnalysisResult,
                          headers: Optional[Dict[str, str]] = None) -> bool:
        """
        Send webhook with analysis results to external service
        
        Args:
            webhook_url: The URL to send the webhook to
            user_id: User ID for the analysis
            analysis_result: The ML analysis results
            headers: Optional additional headers
            
        Returns:
            bool: True if webhook was sent successfully, False otherwise
        """
        
        # Prepare webhook payload
        payload = WebhookPayload(
            user_id=user_id,
            analysis_result=analysis_result,
            timestamp=datetime.utcnow()
        )
        
        # Default headers
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "TransactionRiskAnalytics/1.0",
            "X-Webhook-Source": "transaction-risk-api"
        }
        
        # Add custom headers if provided
        if headers:
            default_headers.update(headers)
        
        # Add authentication header if webhook secret is configured
        webhook_secret = os.getenv("WEBHOOK_SECRET")
        if webhook_secret:
            default_headers["X-Webhook-Secret"] = webhook_secret
        
        # Attempt to send webhook with retries
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        webhook_url,
                        json=payload.dict(),
                        headers=default_headers
                    )
                    
                    # Check if request was successful
                    response.raise_for_status()
                    
                    print(f"✅ Webhook sent successfully to {webhook_url} for user {user_id}")
                    print(f"📊 Response status: {response.status_code}")
                    
                    return True
                    
            except httpx.TimeoutException:
                print(f"⏰ Webhook timeout (attempt {attempt + 1}/{self.max_retries}): {webhook_url}")
                
            except httpx.HTTPStatusError as e:
                print(f"❌ Webhook HTTP error (attempt {attempt + 1}/{self.max_retries}): {e.response.status_code} - {webhook_url}")
                
                # Don't retry for client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    print(f"🚫 Client error, not retrying: {e.response.status_code}")
                    return False
                    
            except httpx.RequestError as e:
                print(f"🌐 Webhook request error (attempt {attempt + 1}/{self.max_retries}): {e} - {webhook_url}")
                
            except Exception as e:
                print(f"💥 Unexpected webhook error (attempt {attempt + 1}/{self.max_retries}): {e} - {webhook_url}")
            
            # Wait before retrying (exponential backoff)
            if attempt < self.max_retries - 1:
                delay = self.retry_delay * (2 ** attempt)
                print(f"⏳ Waiting {delay}s before retry...")
                await asyncio.sleep(delay)
        
        print(f"❌ Failed to send webhook after {self.max_retries} attempts: {webhook_url}")
        return False
    
    async def send_multiple_webhooks(self, 
                                   webhook_urls: list[str], 
                                   user_id: UUID, 
                                   analysis_result: MLAnalysisResult) -> Dict[str, bool]:
        """
        Send webhooks to multiple URLs concurrently
        
        Args:
            webhook_urls: List of webhook URLs
            user_id: User ID for the analysis
            analysis_result: The ML analysis results
            
        Returns:
            Dict[str, bool]: Dictionary mapping URLs to success status
        """
        
        # Create tasks for concurrent webhook sending
        tasks = []
        for url in webhook_urls:
            task = asyncio.create_task(
                self.send_webhook(url, user_id, analysis_result)
            )
            tasks.append((url, task))
        
        # Wait for all webhooks to complete
        results = {}
        for url, task in tasks:
            try:
                success = await task
                results[url] = success
            except Exception as e:
                print(f"💥 Task error for {url}: {e}")
                results[url] = False
        
        return results
    
    async def validate_webhook_url(self, webhook_url: str) -> bool:
        """
        Validate that a webhook URL is reachable
        
        Args:
            webhook_url: The webhook URL to validate
            
        Returns:
            bool: True if URL is reachable, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Send a HEAD request to check if URL is reachable
                response = await client.head(webhook_url)
                
                # Accept any response that's not a connection error
                return response.status_code < 500
                
        except Exception as e:
            print(f"🔍 Webhook URL validation failed for {webhook_url}: {e}")
            return False
    
    def create_test_payload(self, user_id: UUID) -> WebhookPayload:
        """
        Create a test webhook payload for testing purposes
        
        Args:
            user_id: User ID for the test
            
        Returns:
            WebhookPayload: Test payload
        """
        from models.schemas import (
            MLAnalysisResult, FinancialSummary, BehavioralAnalysis, 
            BehavioralPatterns, RiskAssessmentDetails, RiskCategory, SpendingStability
        )
        
        # Create test analysis result
        test_result = MLAnalysisResult(
            overall_risk_score=45.5,
            risk_category=RiskCategory.MEDIUM,
            loan_eligibility=True,
            eligibility_reason="Test eligibility assessment",
            financial_summary=FinancialSummary(
                monthly_spendings={"2024-01": 5000.0, "2024-02": 4800.0},
                monthly_savings={"2024-01": 2000.0, "2024-02": 2200.0},
                total_savings=4200.0,
                income_volatility=0.15,
                spending_volatility=0.20,
                consistency_score=0.85,
                transaction_frequency=120
            ),
            behavioral_analysis=BehavioralAnalysis(
                spending_pattern_distribution={"groceries": 0.3, "utilities": 0.2, "entertainment": 0.1},
                income_and_spending_analysis={"2024-01": {"income": 7000.0, "spending": 5000.0, "savings_rate": 0.29}},
                spending_stability=SpendingStability.HIGH,
                behavioral_patterns=BehavioralPatterns(
                    essential_spending_ratio=0.65,
                    high_risk_spending_ratio=0.08,
                    weekend_spending_ratio=0.25
                )
            ),
            risk_assessment_details=RiskAssessmentDetails(
                risk_essential_spending=20.5,
                high_risk_spending=8.0,
                weekend_spending=12.5,
                loan_eligibility_factors=["Stable income", "Low risk spending"]
            ),
            created_at=datetime.utcnow()
        )
        
        return WebhookPayload(
            user_id=user_id,
            analysis_result=test_result,
            timestamp=datetime.utcnow()
        )
