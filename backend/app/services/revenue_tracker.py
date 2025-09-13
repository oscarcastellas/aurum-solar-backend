"""
Revenue Tracking and Reconciliation System
Comprehensive revenue management across all B2B platforms
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from app.core.database import get_db
from app.models.lead import Lead
from app.models.b2b_platforms import B2BPlatform, B2BRevenueTransaction, B2BLeadMapping
from app.core.redis import get_redis

logger = structlog.get_logger()

class TransactionStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    DISPUTED = "disputed"
    WRITTEN_OFF = "written_off"

@dataclass
class RevenueMetrics:
    total_revenue: float
    total_commission: float
    net_revenue: float
    platform_breakdown: Dict[str, float]
    quality_tier_breakdown: Dict[str, float]
    time_period: str
    transaction_count: int
    avg_revenue_per_lead: float

@dataclass
class ReconciliationResult:
    platform: str
    expected_revenue: float
    actual_revenue: float
    discrepancy: float
    status: str
    issues: List[str]
    recommendations: List[str]

class RevenueTracker:
    """Comprehensive revenue tracking and reconciliation system"""
    
    def __init__(self):
        self.redis = None
        self.revenue_cache = {}
        self.reconciliation_rules = {}
        self.payment_terms = {}
        
        # Performance metrics
        self.total_revenue_tracked = 0.0
        self.total_commission_earned = 0.0
        self.reconciliation_errors = 0
        self.start_time = datetime.utcnow()
    
    async def initialize(self):
        """Initialize the revenue tracker"""
        self.redis = await get_redis()
        await self._load_reconciliation_rules()
        await self._load_payment_terms()
        await self._start_revenue_monitoring()
    
    async def _load_reconciliation_rules(self):
        """Load reconciliation rules for each platform"""
        try:
            # Platform-specific reconciliation rules
            self.reconciliation_rules = {
                "solarreviews": {
                    "payment_terms_days": 30,
                    "commission_rate": 0.15,
                    "minimum_payment": 100.0,
                    "reconciliation_frequency": "daily",
                    "api_endpoint": "/api/revenue/reconciliation",
                    "webhook_url": "/webhooks/solarreviews/revenue"
                },
                "modernize": {
                    "payment_terms_days": 45,
                    "commission_rate": 0.20,
                    "minimum_payment": 50.0,
                    "reconciliation_frequency": "weekly",
                    "email_reports": True,
                    "csv_format": "standard"
                },
                "homeadvisor": {
                    "payment_terms_days": 30,
                    "commission_rate": 0.18,
                    "minimum_payment": 75.0,
                    "reconciliation_frequency": "daily",
                    "api_endpoint": "/api/leads/revenue",
                    "webhook_url": "/webhooks/homeadvisor/revenue"
                },
                "energysage": {
                    "payment_terms_days": 60,
                    "commission_rate": 0.12,
                    "minimum_payment": 25.0,
                    "reconciliation_frequency": "weekly",
                    "email_reports": True,
                    "csv_format": "custom"
                }
            }
            
            logger.info("Loaded reconciliation rules", count=len(self.reconciliation_rules))
            
        except Exception as e:
            logger.error("Error loading reconciliation rules", error=str(e))
    
    async def _load_payment_terms(self):
        """Load payment terms for each platform"""
        try:
            self.payment_terms = {
                "solarreviews": {
                    "net_30": True,
                    "auto_payment": True,
                    "payment_method": "ach",
                    "currency": "USD"
                },
                "modernize": {
                    "net_45": True,
                    "auto_payment": False,
                    "payment_method": "check",
                    "currency": "USD"
                },
                "homeadvisor": {
                    "net_30": True,
                    "auto_payment": True,
                    "payment_method": "ach",
                    "currency": "USD"
                },
                "energysage": {
                    "net_60": True,
                    "auto_payment": False,
                    "payment_method": "wire",
                    "currency": "USD"
                }
            }
            
        except Exception as e:
            logger.error("Error loading payment terms", error=str(e))
    
    async def _start_revenue_monitoring(self):
        """Start background revenue monitoring"""
        async def monitor():
            while True:
                try:
                    await self._update_revenue_metrics()
                    await self._check_payment_status()
                    await asyncio.sleep(3600)  # Run every hour
                except Exception as e:
                    logger.error("Error in revenue monitoring", error=str(e))
                    await asyncio.sleep(3600)
        
        asyncio.create_task(monitor())
    
    async def track_revenue(
        self, 
        lead_id: str, 
        platform_code: str, 
        revenue_amount: float,
        commission_rate: float,
        external_transaction_id: str = None
    ) -> str:
        """Track revenue from a lead delivery"""
        
        try:
            db = next(get_db())
            
            # Calculate commission
            commission_amount = revenue_amount * commission_rate
            net_amount = revenue_amount - commission_amount
            
            # Create revenue transaction
            transaction = B2BRevenueTransaction(
                lead_id=lead_id,
                platform_id=platform_code,
                transaction_date=datetime.utcnow(),
                gross_amount=revenue_amount,
                commission_rate=commission_rate,
                commission_amount=commission_amount,
                net_amount=net_amount,
                external_transaction_id=external_transaction_id,
                transaction_status=TransactionStatus.PENDING.value,
                payment_status=PaymentStatus.PENDING.value,
                payment_due_date=datetime.utcnow() + timedelta(days=30),  # Default 30 days
                created_at=datetime.utcnow()
            )
            
            db.add(transaction)
            db.commit()
            
            # Update metrics
            self.total_revenue_tracked += revenue_amount
            self.total_commission_earned += commission_amount
            
            # Cache revenue data
            await self._cache_revenue_data(platform_code, revenue_amount, net_amount)
            
            logger.info(
                "Revenue tracked successfully",
                lead_id=lead_id,
                platform=platform_code,
                revenue=revenue_amount,
                commission=commission_amount,
                net=net_amount
            )
            
            return str(transaction.id)
            
        except Exception as e:
            logger.error("Error tracking revenue", lead_id=lead_id, error=str(e))
            db.rollback()
            raise
    
    async def _cache_revenue_data(self, platform_code: str, revenue: float, net_revenue: float):
        """Cache revenue data for quick access"""
        try:
            if not self.redis:
                return
            
            # Update daily revenue cache
            today = datetime.utcnow().date().isoformat()
            daily_key = f"revenue:daily:{platform_code}:{today}"
            await self.redis.hincrbyfloat(daily_key, "gross_revenue", revenue)
            await self.redis.hincrbyfloat(daily_key, "net_revenue", net_revenue)
            await self.redis.expire(daily_key, 86400 * 30)  # 30 days TTL
            
            # Update platform totals
            platform_key = f"revenue:platform:{platform_code}"
            await self.redis.hincrbyfloat(platform_key, "total_gross", revenue)
            await self.redis.hincrbyfloat(platform_key, "total_net", net_revenue)
            await self.redis.hincrby(platform_key, "transaction_count", 1)
            
        except Exception as e:
            logger.error("Error caching revenue data", error=str(e))
    
    async def get_revenue_metrics(
        self, 
        time_period: str = "7d",
        platform_code: str = None
    ) -> RevenueMetrics:
        """Get comprehensive revenue metrics"""
        
        try:
            db = next(get_db())
            
            # Calculate date range
            end_date = datetime.utcnow()
            if time_period == "24h":
                start_date = end_date - timedelta(days=1)
            elif time_period == "7d":
                start_date = end_date - timedelta(days=7)
            elif time_period == "30d":
                start_date = end_date - timedelta(days=30)
            elif time_period == "90d":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=7)
            
            # Build query
            query = db.query(B2BRevenueTransaction).filter(
                B2BRevenueTransaction.transaction_date >= start_date,
                B2BRevenueTransaction.transaction_date <= end_date
            )
            
            if platform_code:
                query = query.filter(B2BRevenueTransaction.platform_id == platform_code)
            
            # Get revenue data
            transactions = query.all()
            
            # Calculate metrics
            total_revenue = sum(t.gross_amount for t in transactions)
            total_commission = sum(t.commission_amount for t in transactions)
            net_revenue = sum(t.net_amount for t in transactions)
            transaction_count = len(transactions)
            avg_revenue_per_lead = total_revenue / transaction_count if transaction_count > 0 else 0
            
            # Platform breakdown
            platform_breakdown = {}
            for transaction in transactions:
                platform = transaction.platform_id
                if platform not in platform_breakdown:
                    platform_breakdown[platform] = 0.0
                platform_breakdown[platform] += transaction.gross_amount
            
            # Quality tier breakdown (would need to join with leads table)
            quality_tier_breakdown = {
                "premium": 0.0,
                "standard": 0.0,
                "basic": 0.0,
                "unqualified": 0.0
            }
            
            # Get quality tier breakdown
            quality_query = db.query(
                Lead.lead_quality,
                func.sum(B2BRevenueTransaction.gross_amount).label('total_revenue')
            ).join(
                B2BRevenueTransaction, Lead.id == B2BRevenueTransaction.lead_id
            ).filter(
                B2BRevenueTransaction.transaction_date >= start_date,
                B2BRevenueTransaction.transaction_date <= end_date
            ).group_by(Lead.lead_quality)
            
            if platform_code:
                quality_query = quality_query.filter(B2BRevenueTransaction.platform_id == platform_code)
            
            quality_results = quality_query.all()
            for quality, revenue in quality_results:
                if quality in quality_tier_breakdown:
                    quality_tier_breakdown[quality] = float(revenue)
            
            return RevenueMetrics(
                total_revenue=total_revenue,
                total_commission=total_commission,
                net_revenue=net_revenue,
                platform_breakdown=platform_breakdown,
                quality_tier_breakdown=quality_tier_breakdown,
                time_period=time_period,
                transaction_count=transaction_count,
                avg_revenue_per_lead=avg_revenue_per_lead
            )
            
        except Exception as e:
            logger.error("Error getting revenue metrics", error=str(e))
            return RevenueMetrics(
                total_revenue=0.0,
                total_commission=0.0,
                net_revenue=0.0,
                platform_breakdown={},
                quality_tier_breakdown={},
                time_period=time_period,
                transaction_count=0,
                avg_revenue_per_lead=0.0
            )
    
    async def reconcile_platform_revenue(self, platform_code: str) -> ReconciliationResult:
        """Reconcile revenue with a specific platform"""
        
        try:
            db = next(get_db())
            
            # Get reconciliation rules
            rules = self.reconciliation_rules.get(platform_code, {})
            if not rules:
                raise ValueError(f"No reconciliation rules found for platform: {platform_code}")
            
            # Get our records
            our_transactions = db.query(B2BRevenueTransaction).filter(
                B2BRevenueTransaction.platform_id == platform_code,
                B2BRevenueTransaction.transaction_date >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            our_total = sum(t.gross_amount for t in our_transactions)
            our_count = len(our_transactions)
            
            # Get platform's records (this would call their API)
            platform_total, platform_count = await self._get_platform_revenue_data(platform_code)
            
            # Calculate discrepancy
            discrepancy = our_total - platform_total
            discrepancy_percentage = (discrepancy / our_total * 100) if our_total > 0 else 0
            
            # Identify issues
            issues = []
            recommendations = []
            
            if abs(discrepancy) > 100:  # $100 threshold
                issues.append(f"Revenue discrepancy: ${discrepancy:.2f}")
                recommendations.append("Review transaction records and contact platform")
            
            if our_count != platform_count:
                issues.append(f"Transaction count mismatch: {our_count} vs {platform_count}")
                recommendations.append("Verify all transactions were recorded")
            
            # Check for missing transactions
            missing_transactions = await self._find_missing_transactions(platform_code)
            if missing_transactions:
                issues.append(f"Missing transactions: {len(missing_transactions)}")
                recommendations.append("Investigate missing transaction records")
            
            # Determine status
            if abs(discrepancy) < 10 and our_count == platform_count:
                status = "reconciled"
            elif abs(discrepancy) < 100:
                status = "minor_discrepancy"
            else:
                status = "major_discrepancy"
            
            result = ReconciliationResult(
                platform=platform_code,
                expected_revenue=our_total,
                actual_revenue=platform_total,
                discrepancy=discrepancy,
                status=status,
                issues=issues,
                recommendations=recommendations
            )
            
            # Store reconciliation result
            await self._store_reconciliation_result(result)
            
            logger.info(
                "Platform revenue reconciled",
                platform=platform_code,
                our_total=our_total,
                platform_total=platform_total,
                discrepancy=discrepancy,
                status=status
            )
            
            return result
            
        except Exception as e:
            logger.error("Error reconciling platform revenue", platform=platform_code, error=str(e))
            raise
    
    async def _get_platform_revenue_data(self, platform_code: str) -> Tuple[float, int]:
        """Get revenue data from platform (simulated)"""
        try:
            # This would make actual API calls to platforms
            # For now, we'll simulate the data
            
            if platform_code == "solarreviews":
                return 15000.0, 45
            elif platform_code == "modernize":
                return 12000.0, 60
            elif platform_code == "homeadvisor":
                return 8000.0, 25
            elif platform_code == "energysage":
                return 5000.0, 30
            else:
                return 0.0, 0
                
        except Exception as e:
            logger.error("Error getting platform revenue data", platform=platform_code, error=str(e))
            return 0.0, 0
    
    async def _find_missing_transactions(self, platform_code: str) -> List[str]:
        """Find transactions that might be missing from our records"""
        try:
            # This would compare our records with platform records
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error("Error finding missing transactions", platform=platform_code, error=str(e))
            return []
    
    async def _store_reconciliation_result(self, result: ReconciliationResult):
        """Store reconciliation result for audit trail"""
        try:
            if not self.redis:
                return
            
            # Store in Redis for quick access
            reconciliation_key = f"reconciliation:{result.platform}:{datetime.utcnow().date().isoformat()}"
            await self.redis.hset(reconciliation_key, mapping={
                "platform": result.platform,
                "expected_revenue": result.expected_revenue,
                "actual_revenue": result.actual_revenue,
                "discrepancy": result.discrepancy,
                "status": result.status,
                "issues": json.dumps(result.issues),
                "recommendations": json.dumps(result.recommendations),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            await self.redis.expire(reconciliation_key, 86400 * 90)  # 90 days TTL
            
        except Exception as e:
            logger.error("Error storing reconciliation result", error=str(e))
    
    async def _update_revenue_metrics(self):
        """Update cached revenue metrics"""
        try:
            if not self.redis:
                return
            
            # Update daily metrics
            today = datetime.utcnow().date().isoformat()
            
            # Get today's revenue from database
            db = next(get_db())
            today_revenue = db.query(func.sum(B2BRevenueTransaction.gross_amount)).filter(
                func.date(B2BRevenueTransaction.transaction_date) == today
            ).scalar() or 0
            
            # Cache today's total
            await self.redis.set(f"revenue:daily_total:{today}", today_revenue, ex=86400 * 30)
            
            # Update platform metrics
            platform_revenues = db.query(
                B2BRevenueTransaction.platform_id,
                func.sum(B2BRevenueTransaction.gross_amount).label('total_revenue')
            ).filter(
                func.date(B2BRevenueTransaction.transaction_date) == today
            ).group_by(B2BRevenueTransaction.platform_id).all()
            
            for platform, revenue in platform_revenues:
                await self.redis.set(f"revenue:platform_daily:{platform}:{today}", revenue, ex=86400 * 30)
            
        except Exception as e:
            logger.error("Error updating revenue metrics", error=str(e))
    
    async def _check_payment_status(self):
        """Check payment status and identify overdue payments"""
        try:
            db = next(get_db())
            
            # Find overdue payments
            overdue_cutoff = datetime.utcnow() - timedelta(days=1)
            overdue_transactions = db.query(B2BRevenueTransaction).filter(
                B2BRevenueTransaction.payment_status == PaymentStatus.PENDING.value,
                B2BRevenueTransaction.payment_due_date < overdue_cutoff
            ).all()
            
            # Update status to overdue
            for transaction in overdue_transactions:
                transaction.payment_status = PaymentStatus.OVERDUE.value
                transaction.updated_at = datetime.utcnow()
            
            if overdue_transactions:
                db.commit()
                logger.warning(
                    "Found overdue payments",
                    count=len(overdue_transactions),
                    total_amount=sum(t.net_amount for t in overdue_transactions)
                )
            
        except Exception as e:
            logger.error("Error checking payment status", error=str(e))
            db.rollback()
    
    async def get_payment_summary(self) -> Dict[str, Any]:
        """Get payment summary across all platforms"""
        try:
            db = next(get_db())
            
            # Get payment status summary
            payment_summary = db.query(
                B2BRevenueTransaction.payment_status,
                func.count(B2BRevenueTransaction.id).label('count'),
                func.sum(B2BRevenueTransaction.net_amount).label('total_amount')
            ).group_by(B2BRevenueTransaction.payment_status).all()
            
            # Get platform payment summary
            platform_summary = db.query(
                B2BRevenueTransaction.platform_id,
                B2BRevenueTransaction.payment_status,
                func.count(B2BRevenueTransaction.id).label('count'),
                func.sum(B2BRevenueTransaction.net_amount).label('total_amount')
            ).group_by(
                B2BRevenueTransaction.platform_id,
                B2BRevenueTransaction.payment_status
            ).all()
            
            # Get overdue payments
            overdue_cutoff = datetime.utcnow() - timedelta(days=1)
            overdue_payments = db.query(B2BRevenueTransaction).filter(
                B2BRevenueTransaction.payment_status == PaymentStatus.OVERDUE.value
            ).all()
            
            return {
                "payment_status_summary": {
                    status: {"count": count, "total_amount": float(total_amount)}
                    for status, count, total_amount in payment_summary
                },
                "platform_payment_summary": {
                    f"{platform}_{status}": {"count": count, "total_amount": float(total_amount)}
                    for platform, status, count, total_amount in platform_summary
                },
                "overdue_payments": {
                    "count": len(overdue_payments),
                    "total_amount": sum(p.net_amount for p in overdue_payments),
                    "platforms": list(set(p.platform_id for p in overdue_payments))
                }
            }
            
        except Exception as e:
            logger.error("Error getting payment summary", error=str(e))
            return {}
    
    async def get_revenue_tracker_metrics(self) -> Dict[str, Any]:
        """Get revenue tracker performance metrics"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "total_revenue_tracked": self.total_revenue_tracked,
            "total_commission_earned": self.total_commission_earned,
            "reconciliation_errors": self.reconciliation_errors,
            "uptime_seconds": uptime,
            "active_platforms": len(self.reconciliation_rules),
            "payment_terms_configured": len(self.payment_terms)
        }
