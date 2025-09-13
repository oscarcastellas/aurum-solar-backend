"""
Test Runner for Phases 1 & 2 Validation
Integration Validation and Performance & Load Testing
"""

import pytest
import asyncio
import time
from datetime import datetime
from pathlib import Path

class PhaseValidationRunner:
    """Test runner for phases 1 & 2 validation"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_integration_validation(self):
        """Run Phase 1: Integration Validation"""
        print("\n" + "="*80)
        print("🔄 PHASE 1: INTEGRATION VALIDATION")
        print("="*80)
        
        start_time = time.time()
        
        try:
            # Run integration validation tests
            result = pytest.main([
                "tests/test_integration_validation.py",
                "-v",
                "--tb=short",
                "--disable-warnings"
            ])
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.test_results["integration_validation"] = {
                "status": "PASSED" if result == 0 else "FAILED",
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            print(f"\n✅ Integration validation completed in {duration:.2f}s")
            
        except Exception as e:
            print(f"\n❌ Integration validation failed: {str(e)}")
            self.test_results["integration_validation"] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def run_performance_validation(self):
        """Run Phase 2: Performance & Load Testing"""
        print("\n" + "="*80)
        print("⚡ PHASE 2: PERFORMANCE & LOAD TESTING")
        print("="*80)
        
        start_time = time.time()
        
        try:
            # Run performance validation tests
            result = pytest.main([
                "tests/test_performance_validation.py",
                "-v",
                "--tb=short",
                "--disable-warnings"
            ])
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.test_results["performance_validation"] = {
                "status": "PASSED" if result == 0 else "FAILED",
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            print(f"\n✅ Performance validation completed in {duration:.2f}s")
            
        except Exception as e:
            print(f"\n❌ Performance validation failed: {str(e)}")
            self.test_results["performance_validation"] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def run_phases_1_and_2(self):
        """Run both Phase 1 and Phase 2 validation"""
        print("\n" + "="*80)
        print("🚀 AURUM SOLAR - PHASES 1 & 2 VALIDATION")
        print("="*80)
        print(f"Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.start_time = time.time()
        
        # Phase 1: Integration Validation
        self.run_integration_validation()
        
        # Phase 2: Performance & Load Testing
        self.run_performance_validation()
        
        # Generate summary
        self.generate_validation_summary()
    
    def generate_validation_summary(self):
        """Generate validation summary report"""
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        print("\n" + "="*80)
        print("📊 PHASES 1 & 2 VALIDATION SUMMARY REPORT")
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
            ("End-to-End Integration", self.test_results.get("integration_validation", {}).get("status") == "PASSED"),
            ("Cross-System Communication", self.test_results.get("integration_validation", {}).get("status") == "PASSED"),
            ("Data Flow Validation", self.test_results.get("integration_validation", {}).get("status") == "PASSED"),
            ("API Performance", self.test_results.get("performance_validation", {}).get("status") == "PASSED"),
            ("Load Testing", self.test_results.get("performance_validation", {}).get("status") == "PASSED"),
            ("Scalability", self.test_results.get("performance_validation", {}).get("status") == "PASSED")
        ]
        
        for criterion, passed in criteria:
            status_icon = "✅" if passed else "❌"
            print(f"{status_icon} {criterion}")
        
        # Next steps
        print("\n🚀 Next Steps:")
        print("-" * 50)
        
        if all_passed:
            print("✅ Phases 1 & 2 validation completed successfully!")
            print("✅ System is ready for production deployment")
            print("✅ All integration and performance requirements met")
        else:
            print("❌ Some validation tests failed")
            print("❌ Review failed tests and fix issues")
            print("❌ Re-run validation before proceeding")
        
        print("\n" + "="*80)

def main():
    """Main entry point for phases 1 & 2 validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Aurum Solar Phases 1 & 2 Validation")
    parser.add_argument(
        "--phase", 
        choices=["integration", "performance", "both"],
        default="both",
        help="Validation phase to run"
    )
    
    args = parser.parse_args()
    
    runner = PhaseValidationRunner()
    
    if args.phase == "both":
        runner.run_phases_1_and_2()
    elif args.phase == "integration":
        runner.run_integration_validation()
    elif args.phase == "performance":
        runner.run_performance_validation()

if __name__ == "__main__":
    main()
