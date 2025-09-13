"""
Test Runner for Core Systems Validation
Executes all validation tests in the correct order
"""

import pytest
import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

class ValidationTestRunner:
    """Test runner for core systems validation"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_database_validation(self):
        """Run database and API validation tests"""
        print("\n" + "="*60)
        print("🔍 PHASE 1: DATABASE & APIs VALIDATION")
        print("="*60)
        
        start_time = time.time()
        
        try:
            # Run database validation tests
            result = pytest.main([
                "tests/test_database_validation.py",
                "-v",
                "--tb=short",
                "--disable-warnings"
            ])
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.test_results["database_validation"] = {
                "status": "PASSED" if result == 0 else "FAILED",
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            print(f"\n✅ Database validation completed in {duration:.2f}s")
            
        except Exception as e:
            print(f"\n❌ Database validation failed: {str(e)}")
            self.test_results["database_validation"] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def run_ai_conversation_validation(self):
        """Run AI conversation agent validation tests"""
        print("\n" + "="*60)
        print("🤖 PHASE 2: AI CONVERSATION AGENT VALIDATION")
        print("="*60)
        
        start_time = time.time()
        
        try:
            # Run AI conversation validation tests
            result = pytest.main([
                "tests/test_ai_conversation_validation.py",
                "-v",
                "--tb=short",
                "--disable-warnings"
            ])
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.test_results["ai_conversation_validation"] = {
                "status": "PASSED" if result == 0 else "FAILED",
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            print(f"\n✅ AI conversation validation completed in {duration:.2f}s")
            
        except Exception as e:
            print(f"\n❌ AI conversation validation failed: {str(e)}")
            self.test_results["ai_conversation_validation"] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def run_realtime_systems_validation(self):
        """Run real-time systems validation tests"""
        print("\n" + "="*60)
        print("⚡ PHASE 3: REAL-TIME SYSTEMS VALIDATION")
        print("="*60)
        
        start_time = time.time()
        
        try:
            # Run real-time systems validation tests
            result = pytest.main([
                "tests/test_realtime_systems_validation.py",
                "-v",
                "--tb=short",
                "--disable-warnings"
            ])
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.test_results["realtime_systems_validation"] = {
                "status": "PASSED" if result == 0 else "FAILED",
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            print(f"\n✅ Real-time systems validation completed in {duration:.2f}s")
            
        except Exception as e:
            print(f"\n❌ Real-time systems validation failed: {str(e)}")
            self.test_results["realtime_systems_validation"] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def run_all_core_validation(self):
        """Run all core systems validation tests"""
        print("\n" + "="*80)
        print("🚀 AURUM SOLAR - CORE SYSTEMS VALIDATION")
        print("="*80)
        print(f"Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.start_time = time.time()
        
        # Phase 1: Database & APIs
        self.run_database_validation()
        
        # Phase 2: AI Conversation Agent
        self.run_ai_conversation_validation()
        
        # Phase 3: Real-Time Systems
        self.run_realtime_systems_validation()
        
        # Generate summary
        self.generate_validation_summary()
    
    def generate_validation_summary(self):
        """Generate validation summary report"""
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        print("\n" + "="*80)
        print("📊 VALIDATION SUMMARY REPORT")
        print("="*80)
        
        # Overall status
        all_passed = all(
            result["status"] == "PASSED" 
            for result in self.test_results.values()
        )
        
        overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
        print(f"Overall Status: {overall_status}")
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"Completed at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n📋 Test Results:")
        print("-" * 50)
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            duration = result.get("duration", 0)
            print(f"{status_icon} {test_name.replace('_', ' ').title()}: {result['status']} ({duration:.2f}s)")
            
            if "error" in result:
                print(f"   Error: {result['error']}")
        
        print("\n🎯 Success Criteria:")
        print("-" * 50)
        
        criteria = [
            ("Database Schema", self.test_results.get("database_validation", {}).get("status") == "PASSED"),
            ("API Endpoints", self.test_results.get("database_validation", {}).get("status") == "PASSED"),
            ("AI Conversations", self.test_results.get("ai_conversation_validation", {}).get("status") == "PASSED"),
            ("Real-Time Systems", self.test_results.get("realtime_systems_validation", {}).get("status") == "PASSED"),
            ("WebSocket Connections", self.test_results.get("realtime_systems_validation", {}).get("status") == "PASSED"),
            ("Redis Integration", self.test_results.get("realtime_systems_validation", {}).get("status") == "PASSED")
        ]
        
        for criterion, passed in criteria:
            status_icon = "✅" if passed else "❌"
            print(f"{status_icon} {criterion}")
        
        # Next steps
        print("\n🚀 Next Steps:")
        print("-" * 50)
        
        if all_passed:
            print("✅ Core systems validation completed successfully!")
            print("✅ Ready to proceed with integration validation")
            print("✅ System is ready for production deployment")
        else:
            print("❌ Some core systems validation failed")
            print("❌ Review failed tests and fix issues")
            print("❌ Re-run validation before proceeding")
        
        print("\n" + "="*80)
    
    def run_specific_phase(self, phase):
        """Run a specific validation phase"""
        if phase == "database":
            self.run_database_validation()
        elif phase == "ai":
            self.run_ai_conversation_validation()
        elif phase == "realtime":
            self.run_realtime_systems_validation()
        else:
            print(f"Unknown phase: {phase}")
            print("Available phases: database, ai, realtime")

def main():
    """Main entry point for test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Aurum Solar Core Systems Validation")
    parser.add_argument(
        "--phase", 
        choices=["database", "ai", "realtime", "all"],
        default="all",
        help="Validation phase to run"
    )
    
    args = parser.parse_args()
    
    runner = ValidationTestRunner()
    
    if args.phase == "all":
        runner.run_all_core_validation()
    else:
        runner.run_specific_phase(args.phase)

if __name__ == "__main__":
    main()
