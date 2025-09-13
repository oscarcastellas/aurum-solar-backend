"""
Data retention policies and compliance management
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class DataRetentionManager:
    """Manages data retention policies and GDPR compliance"""
    
    # Data retention periods (in days)
    RETENTION_PERIODS = {
        'leads': 2555,  # 7 years for business records
        'conversations': 1095,  # 3 years for conversation history
        'user_sessions': 365,  # 1 year for session data
        'ai_analyses': 1095,  # 3 years for AI analysis data
        'revenue_transactions': 2555,  # 7 years for financial records
        'platform_performance': 1095,  # 3 years for performance data
        'user_activity_logs': 365,  # 1 year for activity logs
        'error_logs': 90,  # 3 months for error logs
        'temporary_data': 30,  # 1 month for temporary data
    }
    
    # GDPR compliance settings
    GDPR_SETTINGS = {
        'enable_data_anonymization': True,
        'enable_data_pseudonymization': True,
        'enable_right_to_be_forgotten': True,
        'enable_data_portability': True,
        'enable_consent_tracking': True,
        'data_processing_basis': 'legitimate_interest',  # or 'consent'
    }
    
    @classmethod
    def get_retention_policy(cls, data_type: str) -> int:
        """Get retention period in days for a specific data type"""
        return cls.RETENTION_PERIODS.get(data_type, 365)  # Default 1 year
    
    @classmethod
    def calculate_retention_date(cls, data_type: str, created_date: datetime) -> datetime:
        """Calculate when data should be deleted based on retention policy"""
        retention_days = cls.get_retention_policy(data_type)
        return created_date + timedelta(days=retention_days)
    
    @classmethod
    def get_data_for_deletion(cls, db: Session, data_type: str, batch_size: int = 1000) -> List[Dict]:
        """Get data that should be deleted based on retention policy"""
        
        retention_days = cls.get_retention_policy(data_type)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        queries = {
            'leads': """
                SELECT id, email, created_at, data_retention_until
                FROM leads 
                WHERE is_active = false 
                AND (data_retention_until IS NULL OR data_retention_until < NOW())
                AND created_at < %s
                LIMIT %s
            """,
            'conversations': """
                SELECT id, lead_id, created_at
                FROM lead_conversations 
                WHERE created_at < %s
                LIMIT %s
            """,
            'user_sessions': """
                SELECT id, session_id, started_at
                FROM user_sessions 
                WHERE started_at < %s
                LIMIT %s
            """,
            'ai_analyses': """
                SELECT id, lead_id, analyzed_at
                FROM ai_analyses 
                WHERE analyzed_at < %s
                LIMIT %s
            """,
            'revenue_transactions': """
                SELECT id, lead_id, transaction_date
                FROM b2b_revenue_transactions 
                WHERE transaction_date < %s
                LIMIT %s
            """,
            'platform_performance': """
                SELECT id, platform_id, date
                FROM platform_performance 
                WHERE date < %s
                LIMIT %s
            """,
        }
        
        query = queries.get(data_type)
        if not query:
            logger.warning(f"No retention policy defined for data type: {data_type}")
            return []
        
        try:
            result = db.execute(text(query), (cutoff_date, batch_size))
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error getting data for deletion: {e}")
            return []
    
    @classmethod
    def anonymize_lead_data(cls, db: Session, lead_id: str) -> bool:
        """Anonymize lead data for GDPR compliance"""
        try:
            # Anonymize personal information
            anonymize_query = """
                UPDATE leads SET
                    email = 'anonymized_' || id::text || '@example.com',
                    phone = NULL,
                    first_name = 'Anonymized',
                    last_name = 'User',
                    property_address = 'Anonymized Address',
                    notes = 'Data anonymized for privacy compliance',
                    is_gdpr_compliant = true,
                    updated_at = NOW()
                WHERE id = %s
            """
            
            db.execute(text(anonymize_query), (lead_id,))
            db.commit()
            
            logger.info(f"Lead {lead_id} data anonymized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error anonymizing lead data: {e}")
            db.rollback()
            return False
    
    @classmethod
    def delete_expired_data(cls, db: Session, data_type: str, dry_run: bool = True) -> Dict:
        """Delete expired data based on retention policy"""
        
        results = {
            'data_type': data_type,
            'records_found': 0,
            'records_deleted': 0,
            'errors': [],
            'dry_run': dry_run
        }
        
        try:
            # Get data for deletion
            data_to_delete = cls.get_data_for_deletion(db, data_type)
            results['records_found'] = len(data_to_delete)
            
            if not data_to_delete:
                logger.info(f"No expired {data_type} data found for deletion")
                return results
            
            if dry_run:
                logger.info(f"DRY RUN: Would delete {len(data_to_delete)} {data_type} records")
                return results
            
            # Delete data based on type
            if data_type == 'leads':
                results = cls._delete_leads(db, data_to_delete, results)
            elif data_type == 'conversations':
                results = cls._delete_conversations(db, data_to_delete, results)
            elif data_type == 'user_sessions':
                results = cls._delete_user_sessions(db, data_to_delete, results)
            elif data_type == 'ai_analyses':
                results = cls._delete_ai_analyses(db, data_to_delete, results)
            elif data_type == 'revenue_transactions':
                results = cls._delete_revenue_transactions(db, data_to_delete, results)
            elif data_type == 'platform_performance':
                results = cls._delete_platform_performance(db, data_to_delete, results)
            
            db.commit()
            logger.info(f"Successfully deleted {results['records_deleted']} {data_type} records")
            
        except Exception as e:
            logger.error(f"Error deleting expired data: {e}")
            db.rollback()
            results['errors'].append(str(e))
        
        return results
    
    @classmethod
    def _delete_leads(cls, db: Session, data: List[Dict], results: Dict) -> Dict:
        """Delete lead records"""
        for record in data:
            try:
                # Soft delete first
                db.execute(text("UPDATE leads SET is_active = false WHERE id = %s"), (record['id'],))
                results['records_deleted'] += 1
            except Exception as e:
                results['errors'].append(f"Error deleting lead {record['id']}: {e}")
        return results
    
    @classmethod
    def _delete_conversations(cls, db: Session, data: List[Dict], results: Dict) -> Dict:
        """Delete conversation records"""
        for record in data:
            try:
                db.execute(text("DELETE FROM lead_conversations WHERE id = %s"), (record['id'],))
                results['records_deleted'] += 1
            except Exception as e:
                results['errors'].append(f"Error deleting conversation {record['id']}: {e}")
        return results
    
    @classmethod
    def _delete_user_sessions(cls, db: Session, data: List[Dict], results: Dict) -> Dict:
        """Delete user session records"""
        for record in data:
            try:
                db.execute(text("DELETE FROM user_sessions WHERE id = %s"), (record['id'],))
                results['records_deleted'] += 1
            except Exception as e:
                results['errors'].append(f"Error deleting session {record['id']}: {e}")
        return results
    
    @classmethod
    def _delete_ai_analyses(cls, db: Session, data: List[Dict], results: Dict) -> Dict:
        """Delete AI analysis records"""
        for record in data:
            try:
                db.execute(text("DELETE FROM ai_analyses WHERE id = %s"), (record['id'],))
                results['records_deleted'] += 1
            except Exception as e:
                results['errors'].append(f"Error deleting AI analysis {record['id']}: {e}")
        return results
    
    @classmethod
    def _delete_revenue_transactions(cls, db: Session, data: List[Dict], results: Dict) -> Dict:
        """Delete revenue transaction records"""
        for record in data:
            try:
                db.execute(text("DELETE FROM b2b_revenue_transactions WHERE id = %s"), (record['id'],))
                results['records_deleted'] += 1
            except Exception as e:
                results['errors'].append(f"Error deleting transaction {record['id']}: {e}")
        return results
    
    @classmethod
    def _delete_platform_performance(cls, db: Session, data: List[Dict], results: Dict) -> Dict:
        """Delete platform performance records"""
        for record in data:
            try:
                db.execute(text("DELETE FROM platform_performance WHERE id = %s"), (record['id'],))
                results['records_deleted'] += 1
            except Exception as e:
                results['errors'].append(f"Error deleting platform performance {record['id']}: {e}")
        return results
    
    @classmethod
    def cleanup_all_expired_data(cls, db: Session, dry_run: bool = True) -> Dict:
        """Clean up all expired data across all data types"""
        
        results = {
            'total_records_found': 0,
            'total_records_deleted': 0,
            'data_type_results': {},
            'errors': [],
            'dry_run': dry_run
        }
        
        for data_type in cls.RETENTION_PERIODS.keys():
            try:
                type_results = cls.delete_expired_data(db, data_type, dry_run)
                results['data_type_results'][data_type] = type_results
                results['total_records_found'] += type_results['records_found']
                results['total_records_deleted'] += type_results['records_deleted']
                results['errors'].extend(type_results['errors'])
            except Exception as e:
                error_msg = f"Error processing {data_type}: {e}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        return results
    
    @classmethod
    def get_data_retention_report(cls, db: Session) -> Dict:
        """Generate a data retention compliance report"""
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'retention_policies': cls.RETENTION_PERIODS,
            'data_counts': {},
            'compliance_status': 'compliant'
        }
        
        try:
            # Get counts for each data type
            queries = {
                'leads': "SELECT COUNT(*) as count FROM leads WHERE is_active = true",
                'conversations': "SELECT COUNT(*) as count FROM lead_conversations",
                'user_sessions': "SELECT COUNT(*) as count FROM user_sessions",
                'ai_analyses': "SELECT COUNT(*) as count FROM ai_analyses",
                'revenue_transactions': "SELECT COUNT(*) as count FROM b2b_revenue_transactions",
                'platform_performance': "SELECT COUNT(*) as count FROM platform_performance",
            }
            
            for data_type, query in queries.items():
                try:
                    result = db.execute(text(query))
                    count = result.scalar()
                    report['data_counts'][data_type] = count
                except Exception as e:
                    report['data_counts'][data_type] = f"Error: {e}"
            
            # Check for data that should be deleted
            for data_type in cls.RETENTION_PERIODS.keys():
                expired_data = cls.get_data_for_deletion(db, data_type, batch_size=1)
                if expired_data:
                    report['compliance_status'] = 'non_compliant'
                    break
            
        except Exception as e:
            report['error'] = str(e)
            report['compliance_status'] = 'error'
        
        return report
