import os
from typing import List, Optional, Dict, Any
from supabase import create_client, Client
from datetime import datetime, timedelta
from uuid import UUID
import json

from models.schemas import User, Transaction, MLResult, MLAnalysisResult


class SupabaseService:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        if not self.url or not self.key:
            print("⚠️  Warning: SUPABASE_URL and SUPABASE_KEY not found in environment")
            self.client = None
            return
        
        try:
            self.client: Client = create_client(self.url, self.key)
            print("✅ Supabase client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Supabase client: {e}")
            self.client = None

    async def get_user_by_account(self, account_no: str, ifsc_code: str) -> Optional[User]:
        """Get user by account number and IFSC code"""
        if not self.client:
            print("❌ Supabase client not initialized")
            return None
            
        try:
            response = self.client.table("users").select("*").eq("account_no", account_no).eq("ifsc_code", ifsc_code).execute()
            
            if response.data:
                return User(**response.data[0])
            return None
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None

    async def get_user_transactions(self, user_id: UUID, days: int = 180) -> List[Transaction]:
        """Get user transactions for the last N days"""
        if not self.client:
            print("❌ Supabase client not initialized")
            return []
            
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            response = self.client.table("transactions").select("*").eq("user_id", str(user_id)).gte("date", cutoff_date.isoformat()).execute()
            
            transactions = []
            for transaction_data in response.data:
                # Convert string date to datetime if needed
                if isinstance(transaction_data['date'], str):
                    transaction_data['date'] = datetime.fromisoformat(transaction_data['date'].replace('Z', '+00:00'))
                
                transactions.append(Transaction(**transaction_data))
            
            return transactions
        except Exception as e:
            print(f"Error fetching transactions: {e}")
            return []

    async def save_ml_result(self, user_id: UUID, analysis_result: MLAnalysisResult) -> Optional[MLResult]:
        """Save ML analysis result to database"""
        if not self.client:
            print("❌ Supabase client not initialized")
            return None
            
        try:
            ml_result_data = {
                "user_id": str(user_id),
                "risk_score": analysis_result.overall_risk_score,
                "risk_category": analysis_result.risk_category.value,
                "eligible": analysis_result.loan_eligibility,
                "eligibility_reason": analysis_result.eligibility_reason,
                "metrics": analysis_result.dict(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("ml_results").insert(ml_result_data).execute()
            
            if response.data:
                return MLResult(**response.data[0])
            return None
        except Exception as e:
            print(f"Error saving ML result: {e}")
            return None

    async def get_latest_ml_result(self, user_id: UUID) -> Optional[MLResult]:
        """Get the latest ML result for a user"""
        if not self.client:
            print("❌ Supabase client not initialized")
            return None
            
        try:
            response = self.client.table("ml_results").select("*").eq("user_id", str(user_id)).order("created_at", desc=True).limit(1).execute()
            
            if response.data:
                result_data = response.data[0]
                # Convert string dates to datetime if needed
                if isinstance(result_data['created_at'], str):
                    result_data['created_at'] = datetime.fromisoformat(result_data['created_at'].replace('Z', '+00:00'))
                
                return MLResult(**result_data)
            return None
        except Exception as e:
            print(f"Error fetching latest ML result: {e}")
            return None

    async def create_user(self, name: str, account_no: str, ifsc_code: str) -> Optional[User]:
        """Create a new user"""
        if not self.client:
            print("❌ Supabase client not initialized")
            return None
            
        try:
            user_data = {
                "name": name,
                "account_no": account_no,
                "ifsc_code": ifsc_code
            }
            
            response = self.client.table("users").insert(user_data).execute()
            
            if response.data:
                return User(**response.data[0])
            return None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if Supabase connection is healthy"""
        if not self.client:
            print("❌ Supabase client not initialized")
            return False
            
        try:
            # Simple test query that doesn't require specific tables
            response = self.client.rpc('version').execute()
            print("✅ Supabase connection healthy")
            return True
        except Exception as e:
            print(f"❌ Supabase health check failed: {e}")
            return False
