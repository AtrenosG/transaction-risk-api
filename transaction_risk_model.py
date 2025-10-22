import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

from models.schemas import Transaction, MLAnalysisResult, FinancialSummary, BehavioralAnalysis, BehavioralPatterns, RiskAssessmentDetails, RiskCategory, SpendingStability


class TransactionRiskModel:
    def __init__(self):
        # Risk categories for spending
        self.high_risk_categories = {
            'gambling', 'casino', 'betting', 'alcohol', 'tobacco', 'luxury', 
            'entertainment', 'gaming', 'nightlife', 'party'
        }
        
        self.essential_categories = {
            'groceries', 'utilities', 'rent', 'mortgage', 'insurance', 'healthcare', 
            'medicine', 'fuel', 'transport', 'education', 'bills'
        }
        
        # Weekend days
        self.weekend_days = [5, 6]  # Saturday, Sunday

    def analyze_transactions(self, transactions: List[Transaction]) -> MLAnalysisResult:
        """Main method to analyze transactions and generate risk assessment"""
        if not transactions:
            return self._generate_empty_result()
        
        # Convert to DataFrame for easier analysis
        df = self._transactions_to_dataframe(transactions)
        
        # Calculate all metrics
        financial_summary = self._calculate_financial_summary(df)
        behavioral_analysis = self._calculate_behavioral_analysis(df)
        risk_assessment = self._calculate_risk_assessment(df, behavioral_analysis)
        
        # Calculate overall risk score
        overall_risk_score = self._calculate_overall_risk_score(
            financial_summary, behavioral_analysis, risk_assessment
        )
        
        # Determine risk category
        risk_category = self._determine_risk_category(overall_risk_score)
        
        # Determine loan eligibility
        loan_eligibility, eligibility_reason = self._determine_loan_eligibility(
            overall_risk_score, financial_summary, behavioral_analysis
        )
        
        return MLAnalysisResult(
            overall_risk_score=round(overall_risk_score, 1),
            risk_category=risk_category,
            loan_eligibility=loan_eligibility,
            eligibility_reason=eligibility_reason,
            financial_summary=financial_summary,
            behavioral_analysis=behavioral_analysis,
            risk_assessment_details=risk_assessment,
            created_at=datetime.utcnow()
        )

    def _transactions_to_dataframe(self, transactions: List[Transaction]) -> pd.DataFrame:
        """Convert transactions to pandas DataFrame"""
        data = []
        for transaction in transactions:
            data.append({
                'date': transaction.date,
                'amount': transaction.amount,
                'type': transaction.type.value,
                'category': transaction.category.lower(),
                'description': transaction.description,
                'upi_app': transaction.upi_app,
                'weekday': transaction.date.weekday(),
                'month': transaction.date.strftime('%Y-%m'),
                'is_weekend': transaction.date.weekday() in self.weekend_days
            })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values('date')

    def _calculate_financial_summary(self, df: pd.DataFrame) -> FinancialSummary:
        """Calculate financial summary metrics"""
        # Monthly spending and income
        monthly_data = df.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)
        
        monthly_spendings = {}
        monthly_savings = {}
        
        for month in monthly_data.index:
            spending = monthly_data.loc[month, 'debit'] if 'debit' in monthly_data.columns else 0
            income = monthly_data.loc[month, 'credit'] if 'credit' in monthly_data.columns else 0
            
            monthly_spendings[month] = float(spending)
            monthly_savings[month] = float(max(0, income - spending))
        
        # Calculate volatilities
        spending_values = list(monthly_spendings.values())
        income_values = [monthly_data.loc[month, 'credit'] if 'credit' in monthly_data.columns else 0 
                        for month in monthly_data.index]
        
        income_volatility = np.std(income_values) / (np.mean(income_values) + 1e-6)
        spending_volatility = np.std(spending_values) / (np.mean(spending_values) + 1e-6)
        
        # Consistency score (inverse of combined volatility)
        consistency_score = max(0, 1 - (income_volatility + spending_volatility) / 2)
        
        return FinancialSummary(
            monthly_spendings=monthly_spendings,
            monthly_savings=monthly_savings,
            total_savings=sum(monthly_savings.values()),
            income_volatility=round(income_volatility, 3),
            spending_volatility=round(spending_volatility, 3),
            consistency_score=round(consistency_score, 3),
            transaction_frequency=len(df)
        )

    def _calculate_behavioral_analysis(self, df: pd.DataFrame) -> BehavioralAnalysis:
        """Calculate behavioral analysis metrics"""
        # Spending pattern distribution by category
        spending_by_category = df[df['type'] == 'debit'].groupby('category')['amount'].sum()
        total_spending = spending_by_category.sum()
        
        spending_pattern_distribution = {}
        if total_spending > 0:
            spending_pattern_distribution = {
                category: round(float(amount / total_spending), 3)
                for category, amount in spending_by_category.items()
            }
        
        # Income and spending analysis by month
        monthly_analysis = df.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)
        income_spending_analysis = {}
        
        for month in monthly_analysis.index:
            income = monthly_analysis.loc[month, 'credit'] if 'credit' in monthly_analysis.columns else 0
            spending = monthly_analysis.loc[month, 'debit'] if 'debit' in monthly_analysis.columns else 0
            
            income_spending_analysis[month] = {
                'income': float(income),
                'spending': float(spending),
                'savings_rate': float((income - spending) / (income + 1e-6))
            }
        
        # Calculate behavioral patterns
        debit_transactions = df[df['type'] == 'debit']
        total_debit_amount = debit_transactions['amount'].sum()
        
        if total_debit_amount > 0:
            # Essential spending ratio
            essential_spending = debit_transactions[
                debit_transactions['category'].isin(self.essential_categories)
            ]['amount'].sum()
            essential_ratio = essential_spending / total_debit_amount
            
            # High-risk spending ratio
            high_risk_spending = debit_transactions[
                debit_transactions['category'].isin(self.high_risk_categories)
            ]['amount'].sum()
            high_risk_ratio = high_risk_spending / total_debit_amount
            
            # Weekend spending ratio
            weekend_spending = debit_transactions[debit_transactions['is_weekend']]['amount'].sum()
            weekend_ratio = weekend_spending / total_debit_amount
        else:
            essential_ratio = high_risk_ratio = weekend_ratio = 0
        
        behavioral_patterns = BehavioralPatterns(
            essential_spending_ratio=round(essential_ratio, 3),
            high_risk_spending_ratio=round(high_risk_ratio, 3),
            weekend_spending_ratio=round(weekend_ratio, 3)
        )
        
        # Determine spending stability
        spending_stability = self._determine_spending_stability(df)
        
        return BehavioralAnalysis(
            spending_pattern_distribution=spending_pattern_distribution,
            income_and_spending_analysis=income_spending_analysis,
            spending_stability=spending_stability,
            behavioral_patterns=behavioral_patterns
        )

    def _calculate_risk_assessment(self, df: pd.DataFrame, behavioral_analysis: BehavioralAnalysis) -> RiskAssessmentDetails:
        """Calculate detailed risk assessment"""
        patterns = behavioral_analysis.behavioral_patterns
        
        # Risk scores for different spending types (0-100 scale)
        risk_essential_spending = max(0, 50 - patterns.essential_spending_ratio * 50)
        high_risk_spending = patterns.high_risk_spending_ratio * 100
        weekend_spending = min(patterns.weekend_spending_ratio * 100, 50)  # Cap at 50
        
        # Determine loan eligibility factors
        eligibility_factors = []
        
        if patterns.essential_spending_ratio > 0.5:
            eligibility_factors.append("High essential spending ratio")
        
        if patterns.high_risk_spending_ratio < 0.15:
            eligibility_factors.append("Low discretionary spending")
        
        if behavioral_analysis.spending_stability in [SpendingStability.HIGH, SpendingStability.MEDIUM]:
            eligibility_factors.append("Stable spending pattern")
        
        # Check income consistency from financial summary
        monthly_incomes = [
            analysis['income'] for analysis in behavioral_analysis.income_and_spending_analysis.values()
        ]
        if len(monthly_incomes) > 1 and np.std(monthly_incomes) / (np.mean(monthly_incomes) + 1e-6) < 0.3:
            eligibility_factors.append("Stable income")
        
        if not eligibility_factors:
            eligibility_factors.append("Standard risk profile")
        
        return RiskAssessmentDetails(
            risk_essential_spending=round(risk_essential_spending, 1),
            high_risk_spending=round(high_risk_spending, 1),
            weekend_spending=round(weekend_spending, 1),
            loan_eligibility_factors=eligibility_factors
        )

    def _determine_spending_stability(self, df: pd.DataFrame) -> SpendingStability:
        """Determine spending stability based on transaction patterns"""
        monthly_spending = df[df['type'] == 'debit'].groupby('month')['amount'].sum()
        
        if len(monthly_spending) < 2:
            return SpendingStability.MEDIUM
        
        cv = np.std(monthly_spending) / (np.mean(monthly_spending) + 1e-6)
        
        if cv < 0.2:
            return SpendingStability.HIGH
        elif cv < 0.4:
            return SpendingStability.MEDIUM
        else:
            return SpendingStability.LOW

    def _calculate_overall_risk_score(self, financial_summary: FinancialSummary, 
                                    behavioral_analysis: BehavioralAnalysis,
                                    risk_assessment: RiskAssessmentDetails) -> float:
        """Calculate overall risk score (0-100, higher = more risky)"""
        
        # Base score from volatilities
        volatility_score = (financial_summary.income_volatility + financial_summary.spending_volatility) * 50
        
        # Consistency bonus (lower risk for consistent behavior)
        consistency_bonus = (1 - financial_summary.consistency_score) * 20
        
        # Behavioral risk factors
        behavioral_risk = (
            behavioral_analysis.behavioral_patterns.high_risk_spending_ratio * 30 +
            max(0, behavioral_analysis.behavioral_patterns.weekend_spending_ratio - 0.2) * 20
        )
        
        # Essential spending bonus (lower risk for essential spending)
        essential_bonus = max(0, (0.6 - behavioral_analysis.behavioral_patterns.essential_spending_ratio) * 15)
        
        # Savings rate factor
        avg_savings_rate = np.mean([
            analysis.get('savings_rate', 0) 
            for analysis in behavioral_analysis.income_and_spending_analysis.values()
        ])
        savings_risk = max(0, (0.1 - avg_savings_rate) * 25)  # Risk if savings rate < 10%
        
        # Transaction frequency factor (very low or very high frequency can be risky)
        freq_risk = 0
        if financial_summary.transaction_frequency < 20:  # Too few transactions
            freq_risk = 10
        elif financial_summary.transaction_frequency > 300:  # Too many transactions
            freq_risk = 5
        
        total_risk = (
            volatility_score + consistency_bonus + behavioral_risk + 
            essential_bonus + savings_risk + freq_risk
        )
        
        return min(100, max(0, total_risk))

    def _determine_risk_category(self, risk_score: float) -> RiskCategory:
        """Determine risk category based on overall risk score"""
        if risk_score < 40:
            return RiskCategory.LOW
        elif risk_score < 70:
            return RiskCategory.MEDIUM
        else:
            return RiskCategory.HIGH

    def _determine_loan_eligibility(self, risk_score: float, financial_summary: FinancialSummary,
                                  behavioral_analysis: BehavioralAnalysis) -> Tuple[bool, str]:
        """Determine loan eligibility and provide reasoning"""
        
        # Base eligibility on risk score
        if risk_score > 75:
            return False, "High risk profile with significant financial volatility"
        
        # Check essential criteria
        patterns = behavioral_analysis.behavioral_patterns
        
        # Must have reasonable essential spending
        if patterns.essential_spending_ratio < 0.3:
            return False, "Insufficient essential spending pattern indicating unstable lifestyle"
        
        # High-risk spending should be controlled
        if patterns.high_risk_spending_ratio > 0.25:
            return False, "Excessive high-risk spending indicating poor financial discipline"
        
        # Check savings capability
        avg_savings_rate = np.mean([
            analysis.get('savings_rate', 0) 
            for analysis in behavioral_analysis.income_and_spending_analysis.values()
        ])
        
        if avg_savings_rate < -0.1:  # Consistently spending more than earning
            return False, "Negative savings rate indicating financial stress"
        
        # Check consistency
        if financial_summary.consistency_score < 0.3:
            return False, "Highly inconsistent financial behavior"
        
        # Determine eligibility reason based on strengths
        reasons = []
        if patterns.essential_spending_ratio > 0.5:
            reasons.append("stable essential spending")
        if patterns.high_risk_spending_ratio < 0.15:
            reasons.append("controlled discretionary spending")
        if financial_summary.consistency_score > 0.7:
            reasons.append("consistent financial behavior")
        if avg_savings_rate > 0.05:
            reasons.append("positive savings rate")
        
        if not reasons:
            reasons.append("acceptable risk profile")
        
        eligibility_reason = f"Eligible based on {', '.join(reasons)}"
        
        return True, eligibility_reason

    def _generate_empty_result(self) -> MLAnalysisResult:
        """Generate empty result for cases with no transactions"""
        return MLAnalysisResult(
            overall_risk_score=50.0,
            risk_category=RiskCategory.MEDIUM,
            loan_eligibility=False,
            eligibility_reason="Insufficient transaction history for assessment",
            financial_summary=FinancialSummary(
                monthly_spendings={},
                monthly_savings={},
                total_savings=0.0,
                income_volatility=0.0,
                spending_volatility=0.0,
                consistency_score=0.0,
                transaction_frequency=0
            ),
            behavioral_analysis=BehavioralAnalysis(
                spending_pattern_distribution={},
                income_and_spending_analysis={},
                spending_stability=SpendingStability.MEDIUM,
                behavioral_patterns=BehavioralPatterns(
                    essential_spending_ratio=0.0,
                    high_risk_spending_ratio=0.0,
                    weekend_spending_ratio=0.0
                )
            ),
            risk_assessment_details=RiskAssessmentDetails(
                risk_essential_spending=50.0,
                high_risk_spending=0.0,
                weekend_spending=0.0,
                loan_eligibility_factors=["Insufficient data"]
            ),
            created_at=datetime.utcnow()
        )
