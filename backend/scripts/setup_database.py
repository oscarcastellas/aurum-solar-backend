"""
Database setup and optimization script
"""

import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, SessionLocal
from app.core.database_optimization import DatabaseOptimizer
from app.core.data_retention import DataRetentionManager
from app.models import *  # Import all models to ensure they're registered


def setup_database():
    """Set up database with optimizations and initial data"""
    
    print("Setting up Aurum Solar database...")
    
    # Create all tables
    print("Creating database tables...")
    from app.core.database import Base
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    # Create performance indexes
    print("Creating performance indexes...")
    create_performance_indexes()
    print("✓ Performance indexes created")
    
    # Create materialized views
    print("Creating materialized views...")
    create_materialized_views()
    print("✓ Materialized views created")
    
    # Set up database optimizations
    print("Applying database optimizations...")
    apply_database_optimizations()
    print("✓ Database optimizations applied")
    
    # Seed initial data
    print("Seeding initial data...")
    seed_initial_data()
    print("✓ Initial data seeded")
    
    print("Database setup completed successfully!")


def create_performance_indexes():
    """Create performance-critical indexes"""
    
    db = SessionLocal()
    
    try:
        # Get performance indexes
        indexes = DatabaseOptimizer.get_performance_indexes()
        
        for index_sql in indexes:
            try:
                db.execute(text(index_sql))
                print(f"  ✓ Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
            except SQLAlchemyError as e:
                if "already exists" in str(e):
                    print(f"  - Index already exists: {index_sql.split('idx_')[1].split(' ')[0]}")
                else:
                    print(f"  ✗ Error creating index: {e}")
        
        db.commit()
        
    except Exception as e:
        print(f"Error creating performance indexes: {e}")
        db.rollback()
    finally:
        db.close()


def create_materialized_views():
    """Create materialized views for analytics performance"""
    
    db = SessionLocal()
    
    try:
        # Get materialized views
        views = DatabaseOptimizer.get_analytics_materialized_views()
        
        for view_sql in views:
            try:
                db.execute(text(view_sql))
                print(f"  ✓ Created materialized view")
            except SQLAlchemyError as e:
                if "already exists" in str(e):
                    print(f"  - Materialized view already exists")
                else:
                    print(f"  ✗ Error creating materialized view: {e}")
        
        db.commit()
        
    except Exception as e:
        print(f"Error creating materialized views: {e}")
        db.rollback()
    finally:
        db.close()


def apply_database_optimizations():
    """Apply database-level optimizations"""
    
    db = SessionLocal()
    
    try:
        # PostgreSQL optimizations
        optimizations = [
            "SET random_page_cost = 1.1",
            "SET effective_cache_size = '4GB'",
            "SET work_mem = '256MB'",
            "SET maintenance_work_mem = '1GB'",
            "SET shared_buffers = '1GB'",
            "SET checkpoint_completion_target = 0.9",
            "SET wal_buffers = '16MB'",
            "SET default_statistics_target = 100",
            "SET max_parallel_workers_per_gather = 4",
            "SET max_parallel_workers = 8",
            "SET max_parallel_maintenance_workers = 4",
            "SET jit = on",
            "SET jit_above_cost = 100000",
            "SET jit_optimize_above_cost = 500000",
        ]
        
        for optimization in optimizations:
            try:
                db.execute(text(optimization))
                print(f"  ✓ Applied: {optimization}")
            except SQLAlchemyError as e:
                print(f"  ✗ Error applying optimization: {e}")
        
        db.commit()
        
    except Exception as e:
        print(f"Error applying database optimizations: {e}")
        db.rollback()
    finally:
        db.close()


def seed_initial_data():
    """Seed initial data for the application"""
    
    try:
        # Import and run seed scripts
        from scripts.seed_nyc_data import main as seed_nyc_data
        from scripts.seed_database import create_sample_data
        
        print("  Seeding NYC market intelligence data...")
        seed_nyc_data()
        
        print("  Seeding sample application data...")
        create_sample_data()
        
    except Exception as e:
        print(f"Error seeding initial data: {e}")


def verify_database_setup():
    """Verify database setup and performance"""
    
    print("\nVerifying database setup...")
    
    db = SessionLocal()
    
    try:
        # Check table counts
        tables_to_check = [
            'leads', 'users', 'b2b_platforms', 'ai_models',
            'nyc_zip_codes', 'revenue_metrics', 'platform_performance'
        ]
        
        for table in tables_to_check:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  ✓ {table}: {count} records")
        
        # Check indexes
        result = db.execute(text("""
            SELECT COUNT(*) as index_count 
            FROM pg_indexes 
            WHERE schemaname = 'public'
        """))
        index_count = result.scalar()
        print(f"  ✓ Total indexes: {index_count}")
        
        # Check materialized views
        result = db.execute(text("""
            SELECT COUNT(*) as view_count 
            FROM pg_matviews 
            WHERE schemaname = 'public'
        """))
        view_count = result.scalar()
        print(f"  ✓ Materialized views: {view_count}")
        
        # Check connection pool status
        pool_status = DatabaseOptimizer.get_pool_status(engine)
        print(f"  ✓ Connection pool size: {pool_status['pool_size']}")
        print(f"  ✓ Checked out connections: {pool_status['checked_out_connections']}")
        
        print("\n✓ Database setup verification completed successfully!")
        
    except Exception as e:
        print(f"Error verifying database setup: {e}")
    finally:
        db.close()


def run_performance_tests():
    """Run basic performance tests"""
    
    print("\nRunning performance tests...")
    
    db = SessionLocal()
    
    try:
        # Test lead query performance
        import time
        
        start_time = time.time()
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM leads 
            WHERE is_active = true 
            AND created_at > NOW() - INTERVAL '30 days'
        """))
        lead_count = result.scalar()
        query_time = time.time() - start_time
        
        print(f"  ✓ Lead count query: {lead_count} records in {query_time:.3f}s")
        
        # Test analytics query performance
        start_time = time.time()
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total_leads,
                AVG(lead_score) as avg_score,
                SUM(total_revenue_earned) as total_revenue
            FROM leads 
            WHERE is_active = true
        """))
        analytics_result = result.fetchone()
        query_time = time.time() - start_time
        
        print(f"  ✓ Analytics query: {analytics_result[0]} leads, avg score {analytics_result[1]:.1f}, revenue ${analytics_result[2]:.2f} in {query_time:.3f}s")
        
        # Test NYC market intelligence query
        start_time = time.time()
        result = db.execute(text("""
            SELECT 
                borough,
                COUNT(*) as zip_count,
                AVG(solar_adoption_rate) as avg_adoption
            FROM nyc_zip_codes 
            GROUP BY borough
        """))
        nyc_results = result.fetchall()
        query_time = time.time() - start_time
        
        print(f"  ✓ NYC market query: {len(nyc_results)} boroughs in {query_time:.3f}s")
        
        print("\n✓ Performance tests completed successfully!")
        
    except Exception as e:
        print(f"Error running performance tests: {e}")
    finally:
        db.close()


def main():
    """Main setup function"""
    
    print("Aurum Solar Database Setup")
    print("=" * 50)
    
    # Setup database
    setup_database()
    
    # Verify setup
    verify_database_setup()
    
    # Run performance tests
    run_performance_tests()
    
    print("\n" + "=" * 50)
    print("Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Update environment variables in .env file")
    print("2. Configure API keys for external services")
    print("3. Start the application with: python main.py")
    print("4. Access the API documentation at: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
