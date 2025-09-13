"""
Basic Validation Script for Aurum Solar Conversational Agent
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing module imports...")
    
    results = {}
    
    try:
        from app.services.solar_calculation_engine import SolarCalculationEngine
        results["solar_calculation"] = True
        print("✅ SolarCalculationEngine import successful")
    except Exception as e:
        results["solar_calculation"] = False
        print(f"❌ SolarCalculationEngine import failed: {e}")
    
    try:
        from app.services.nyc_expertise_database import NYCExpertiseDatabase
        results["nyc_expertise"] = True
        print("✅ NYCExpertiseDatabase import successful")
    except Exception as e:
        results["nyc_expertise"] = False
        print(f"❌ NYCExpertiseDatabase import failed: {e}")
    
    try:
        from app.services.revenue_optimization_engine import RealTimeLeadScoringEngine
        results["revenue_optimization"] = True
        print("✅ RealTimeLeadScoringEngine import successful")
    except Exception as e:
        results["revenue_optimization"] = False
        print(f"❌ RealTimeLeadScoringEngine import failed: {e}")
    
    return results

def run_basic_validation():
    """Run basic validation"""
    
    print("🚀 Aurum Solar Conversational Agent - Basic Validation")
    print("=" * 60)
    
    start_time = datetime.utcnow()
    
    # Test imports
    results = test_imports()
    
    # Calculate results
    end_time = datetime.utcnow()
    execution_time = (end_time - start_time).total_seconds()
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    success_rate = passed_tests / total_tests
    
    # Generate report
    print("\n" + "=" * 60)
    print("📊 VALIDATION RESULTS")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Success Rate: {success_rate:.1%} ({passed_tests}/{total_tests})")
    print(f"Execution Time: {execution_time:.2f} seconds")
    
    # Launch readiness assessment
    launch_ready = success_rate >= 0.8
    
    print(f"\nLaunch Readiness: {'✅ READY' if launch_ready else '❌ NOT READY'}")
    
    if launch_ready:
        print("\n🎉 BASIC VALIDATION SUCCESSFUL!")
        print("Core modules are importing correctly!")
    else:
        print("\n⚠️ BASIC VALIDATION FAILED")
        print("Some modules have import issues.")
    
    print("\n" + "=" * 60)
    
    return {
        "success_rate": success_rate,
        "passed_tests": passed_tests,
        "total_tests": total_tests,
        "execution_time": execution_time,
        "launch_ready": launch_ready,
        "results": results
    }

if __name__ == "__main__":
    run_basic_validation()
