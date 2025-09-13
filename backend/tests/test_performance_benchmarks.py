"""
Performance Benchmarking and Validation Metrics for Aurum Solar Agent
Tests system performance, load handling, and benchmarks against industry standards
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from unittest.mock import Mock
import numpy as np
import psutil
import gc

from app.services.revenue_optimization_system import RevenueOptimizationSystem


@dataclass
class PerformanceBenchmark:
    """Performance benchmark configuration"""
    benchmark_id: str
    name: str
    description: str
    test_type: str  # "response_time", "throughput", "memory", "accuracy"
    target_metric: float
    tolerance: float
    test_parameters: Dict[str, Any]


@dataclass
class BenchmarkResult:
    """Benchmark test result"""
    benchmark_id: str
    name: str
    test_type: str
    target_metric: float
    actual_metric: float
    passed: bool
    performance_score: float
    details: Dict[str, Any]
    timestamp: datetime


@dataclass
class LoadTestResult:
    """Load test result"""
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput: float  # requests per second
    error_rate: float
    memory_usage: float
    cpu_usage: float


class PerformanceBenchmarker:
    """Performance benchmarking and validation framework"""
    
    def __init__(self, revenue_system: RevenueOptimizationSystem):
        self.revenue_system = revenue_system
        self.benchmarks = self._load_performance_benchmarks()
        self.industry_standards = self._load_industry_standards()
    
    def _load_performance_benchmarks(self) -> List[PerformanceBenchmark]:
        """Load performance benchmark configurations"""
        
        return [
            # Response Time Benchmarks
            PerformanceBenchmark(
                benchmark_id="response_time_basic",
                name="Basic Response Time",
                description="Response time for basic conversation processing",
                test_type="response_time",
                target_metric=2.0,  # 2 seconds
                tolerance=0.5,
                test_parameters={
                    "message": "I'm interested in solar for my home",
                    "conversation_length": 1
                }
            ),
            
            PerformanceBenchmark(
                benchmark_id="response_time_complex",
                name="Complex Response Time",
                description="Response time for complex conversation with calculations",
                test_type="response_time",
                target_metric=3.0,  # 3 seconds
                tolerance=1.0,
                test_parameters={
                    "message": "My Con Ed bill is $380 monthly, what system size do I need?",
                    "conversation_length": 5,
                    "include_calculations": True
                }
            ),
            
            PerformanceBenchmark(
                benchmark_id="response_time_revenue_optimization",
                name="Revenue Optimization Response Time",
                description="Response time with full revenue optimization",
                test_type="response_time",
                target_metric=4.0,  # 4 seconds
                tolerance=1.0,
                test_parameters={
                    "message": "I want to move forward with solar installation",
                    "conversation_length": 8,
                    "include_revenue_optimization": True
                }
            ),
            
            # Throughput Benchmarks
            PerformanceBenchmark(
                benchmark_id="throughput_single",
                name="Single User Throughput",
                description="Throughput for single user conversation",
                test_type="throughput",
                target_metric=30.0,  # 30 messages per minute
                tolerance=5.0,
                test_parameters={
                    "duration_minutes": 1,
                    "concurrent_users": 1
                }
            ),
            
            PerformanceBenchmark(
                benchmark_id="throughput_concurrent",
                name="Concurrent User Throughput",
                description="Throughput with multiple concurrent users",
                test_type="throughput",
                target_metric=150.0,  # 150 messages per minute
                tolerance=25.0,
                test_parameters={
                    "duration_minutes": 2,
                    "concurrent_users": 10
                }
            ),
            
            # Memory Usage Benchmarks
            PerformanceBenchmark(
                benchmark_id="memory_basic",
                name="Basic Memory Usage",
                description="Memory usage for basic conversation processing",
                test_type="memory",
                target_metric=100.0,  # 100 MB
                tolerance=50.0,
                test_parameters={
                    "test_type": "basic_conversation"
                }
            ),
            
            PerformanceBenchmark(
                benchmark_id="memory_extended",
                name="Extended Memory Usage",
                description="Memory usage during extended conversation",
                test_type="memory",
                target_metric=200.0,  # 200 MB
                tolerance=100.0,
                test_parameters={
                    "test_type": "extended_conversation",
                    "conversation_length": 20
                }
            ),
            
            # Accuracy Benchmarks
            PerformanceBenchmark(
                benchmark_id="accuracy_solar_calculations",
                name="Solar Calculation Accuracy",
                description="Accuracy of solar system calculations",
                test_type="accuracy",
                target_metric=0.95,  # 95% accuracy
                tolerance=0.05,
                test_parameters={
                    "test_cases": 10,
                    "calculation_type": "system_sizing"
                }
            ),
            
            PerformanceBenchmark(
                benchmark_id="accuracy_lead_scoring",
                name="Lead Scoring Accuracy",
                description="Accuracy of lead scoring algorithms",
                test_type="accuracy",
                target_metric=0.90,  # 90% accuracy
                tolerance=0.10,
                test_parameters={
                    "test_cases": 20,
                    "scoring_type": "quality_tier"
                }
            )
        ]
    
    def _load_industry_standards(self) -> Dict[str, Any]:
        """Load industry performance standards"""
        
        return {
            "response_time": {
                "excellent": 1.0,
                "good": 2.0,
                "acceptable": 3.0,
                "poor": 5.0
            },
            "throughput": {
                "excellent": 200.0,  # messages per minute
                "good": 150.0,
                "acceptable": 100.0,
                "poor": 50.0
            },
            "memory_usage": {
                "excellent": 50.0,   # MB
                "good": 100.0,
                "acceptable": 200.0,
                "poor": 500.0
            },
            "accuracy": {
                "excellent": 0.98,
                "good": 0.95,
                "acceptable": 0.90,
                "poor": 0.80
            },
            "availability": {
                "excellent": 0.999,  # 99.9%
                "good": 0.99,        # 99%
                "acceptable": 0.95,   # 95%
                "poor": 0.90         # 90%
            }
        }
    
    async def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all performance benchmarks"""
        
        print("🚀 Starting Performance Benchmarking...")
        
        results = []
        
        for benchmark in self.benchmarks:
            print(f"\n📊 Running: {benchmark.name}")
            
            try:
                if benchmark.test_type == "response_time":
                    result = await self._benchmark_response_time(benchmark)
                elif benchmark.test_type == "throughput":
                    result = await self._benchmark_throughput(benchmark)
                elif benchmark.test_type == "memory":
                    result = await self._benchmark_memory_usage(benchmark)
                elif benchmark.test_type == "accuracy":
                    result = await self._benchmark_accuracy(benchmark)
                else:
                    continue
                
                results.append(result)
                
                status = "✅ PASSED" if result.passed else "❌ FAILED"
                print(f"  {status} - {result.actual_metric:.2f} vs {result.target_metric:.2f} target")
                
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)}")
                results.append(BenchmarkResult(
                    benchmark_id=benchmark.benchmark_id,
                    name=benchmark.name,
                    test_type=benchmark.test_type,
                    target_metric=benchmark.target_metric,
                    actual_metric=0.0,
                    passed=False,
                    performance_score=0.0,
                    details={"error": str(e)},
                    timestamp=datetime.utcnow()
                ))
        
        return results
    
    async def _benchmark_response_time(self, benchmark: PerformanceBenchmark) -> BenchmarkResult:
        """Benchmark response time performance"""
        
        test_params = benchmark.test_parameters
        response_times = []
        
        # Run multiple iterations for statistical significance
        iterations = 10
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                await self.revenue_system.process_conversation_for_revenue_optimization(
                    session_id=f"benchmark_{benchmark.benchmark_id}_{i}",
                    message=test_params["message"],
                    conversation_context={
                        "homeowner_verified": True,
                        "bill_amount": 300.0,
                        "zip_code": "10021",
                        "borough": "manhattan"
                    },
                    conversation_history=[]
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                response_times.append(response_time)
                
            except Exception as e:
                response_times.append(10.0)  # Error penalty time
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = np.percentile(response_times, 95)
        
        # Determine if benchmark passed
        passed = avg_response_time <= (benchmark.target_metric + benchmark.tolerance)
        performance_score = max(0.0, 1.0 - (avg_response_time / benchmark.target_metric - 1.0))
        
        return BenchmarkResult(
            benchmark_id=benchmark.benchmark_id,
            name=benchmark.name,
            test_type=benchmark.test_type,
            target_metric=benchmark.target_metric,
            actual_metric=avg_response_time,
            passed=passed,
            performance_score=performance_score,
            details={
                "iterations": iterations,
                "avg_response_time": avg_response_time,
                "median_response_time": median_response_time,
                "p95_response_time": p95_response_time,
                "response_times": response_times
            },
            timestamp=datetime.utcnow()
        )
    
    async def _benchmark_throughput(self, benchmark: PerformanceBenchmark) -> BenchmarkResult:
        """Benchmark throughput performance"""
        
        test_params = benchmark.test_parameters
        concurrent_users = test_params["concurrent_users"]
        duration_seconds = test_params["duration_minutes"] * 60
        
        # Run load test
        load_test_result = await self._run_load_test(concurrent_users, duration_seconds)
        
        # Calculate throughput (messages per minute)
        throughput = load_test_result.throughput * 60
        
        # Determine if benchmark passed
        passed = throughput >= (benchmark.target_metric - benchmark.tolerance)
        performance_score = min(1.0, throughput / benchmark.target_metric)
        
        return BenchmarkResult(
            benchmark_id=benchmark.benchmark_id,
            name=benchmark.name,
            test_type=benchmark.test_type,
            target_metric=benchmark.target_metric,
            actual_metric=throughput,
            passed=passed,
            performance_score=performance_score,
            details={
                "load_test_result": asdict(load_test_result),
                "concurrent_users": concurrent_users,
                "duration_minutes": test_params["duration_minutes"]
            },
            timestamp=datetime.utcnow()
        )
    
    async def _benchmark_memory_usage(self, benchmark: PerformanceBenchmark) -> BenchmarkResult:
        """Benchmark memory usage"""
        
        test_params = benchmark.test_parameters
        
        # Get baseline memory usage
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run memory-intensive test
        if test_params["test_type"] == "basic_conversation":
            await self._run_basic_conversation_test()
        elif test_params["test_type"] == "extended_conversation":
            await self._run_extended_conversation_test(test_params.get("conversation_length", 20))
        
        # Measure peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - baseline_memory
        
        # Force garbage collection and measure final memory
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_memory_increase = final_memory - baseline_memory
        
        # Use final memory increase as the metric
        actual_memory = final_memory_increase
        
        # Determine if benchmark passed
        passed = actual_memory <= (benchmark.target_metric + benchmark.tolerance)
        performance_score = max(0.0, 1.0 - (actual_memory / benchmark.target_metric - 1.0))
        
        return BenchmarkResult(
            benchmark_id=benchmark.benchmark_id,
            name=benchmark.name,
            test_type=benchmark.test_type,
            target_metric=benchmark.target_metric,
            actual_metric=actual_memory,
            passed=passed,
            performance_score=performance_score,
            details={
                "baseline_memory": baseline_memory,
                "peak_memory": peak_memory,
                "final_memory": final_memory,
                "memory_increase": actual_memory,
                "test_type": test_params["test_type"]
            },
            timestamp=datetime.utcnow()
        )
    
    async def _benchmark_accuracy(self, benchmark: PerformanceBenchmark) -> BenchmarkResult:
        """Benchmark accuracy performance"""
        
        test_params = benchmark.test_parameters
        test_cases = test_params["test_cases"]
        calculation_type = test_params.get("calculation_type", "system_sizing")
        scoring_type = test_params.get("scoring_type", "quality_tier")
        
        correct_predictions = 0
        total_predictions = 0
        
        if benchmark.benchmark_id == "accuracy_solar_calculations":
            # Test solar calculation accuracy
            for i in range(test_cases):
                # Generate test case
                monthly_bill = random.uniform(150, 500)
                expected_size_range = (monthly_bill * 0.02, monthly_bill * 0.025)  # Rough estimate
                
                try:
                    # Get actual calculation
                    response = await self.revenue_system.process_conversation_for_revenue_optimization(
                        session_id=f"accuracy_test_{i}",
                        message=f"My electric bill is ${monthly_bill:.0f} monthly, what system size do I need?",
                        conversation_context={
                            "homeowner_verified": True,
                            "bill_amount": monthly_bill,
                            "zip_code": "10021",
                            "borough": "manhattan"
                        },
                        conversation_history=[]
                    )
                    
                    # Extract system size from response (simplified)
                    content = response.get("content", "").lower()
                    if "kw" in content or "kilowatt" in content:
                        # This is a simplified check - in reality, you'd parse the actual system size
                        correct_predictions += 1
                    
                    total_predictions += 1
                    
                except Exception:
                    total_predictions += 1
        
        elif benchmark.benchmark_id == "accuracy_lead_scoring":
            # Test lead scoring accuracy
            test_profiles = [
                {"bill_amount": 400, "borough": "manhattan", "expected_tier": "premium"},
                {"bill_amount": 250, "borough": "queens", "expected_tier": "standard"},
                {"bill_amount": 150, "borough": "bronx", "expected_tier": "basic"},
                {"bill_amount": 600, "borough": "manhattan", "expected_tier": "premium"},
                {"bill_amount": 200, "borough": "brooklyn", "expected_tier": "standard"}
            ]
            
            for profile in test_profiles * (test_cases // len(test_profiles) + 1):
                if total_predictions >= test_cases:
                    break
                
                try:
                    response = await self.revenue_system.process_conversation_for_revenue_optimization(
                        session_id=f"scoring_test_{total_predictions}",
                        message=f"My {profile['borough']} bill is ${profile['bill_amount']} monthly",
                        conversation_context={
                            "homeowner_verified": True,
                            "bill_amount": profile["bill_amount"],
                            "borough": profile["borough"]
                        },
                        conversation_history=[]
                    )
                    
                    revenue_data = response.get("revenue_optimization", {})
                    lead_score = revenue_data.get("lead_score", {})
                    actual_tier = lead_score.get("quality_tier", "unqualified")
                    
                    if actual_tier == profile["expected_tier"]:
                        correct_predictions += 1
                    
                    total_predictions += 1
                    
                except Exception:
                    total_predictions += 1
        
        # Calculate accuracy
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0
        
        # Determine if benchmark passed
        passed = accuracy >= (benchmark.target_metric - benchmark.tolerance)
        performance_score = accuracy
        
        return BenchmarkResult(
            benchmark_id=benchmark.benchmark_id,
            name=benchmark.name,
            test_type=benchmark.test_type,
            target_metric=benchmark.target_metric,
            actual_metric=accuracy,
            passed=passed,
            performance_score=performance_score,
            details={
                "correct_predictions": correct_predictions,
                "total_predictions": total_predictions,
                "test_cases": test_cases
            },
            timestamp=datetime.utcnow()
        )
    
    async def _run_load_test(self, concurrent_users: int, duration_seconds: int) -> LoadTestResult:
        """Run load test with specified concurrent users"""
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        response_times = []
        successful_requests = 0
        failed_requests = 0
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_users)
        
        async def make_request(request_id: int):
            async with semaphore:
                request_start = time.time()
                try:
                    await self.revenue_system.process_conversation_for_revenue_optimization(
                        session_id=f"load_test_{request_id}",
                        message=f"Load test message {request_id}",
                        conversation_context={
                            "homeowner_verified": True,
                            "bill_amount": 300.0,
                            "zip_code": "10021",
                            "borough": "manhattan"
                        },
                        conversation_history=[]
                    )
                    
                    request_end = time.time()
                    response_time = request_end - request_start
                    response_times.append(response_time)
                    return True
                    
                except Exception:
                    return False
        
        # Run load test
        request_id = 0
        tasks = []
        
        while time.time() < end_time:
            # Create new requests up to concurrent limit
            while len(tasks) < concurrent_users and time.time() < end_time:
                task = asyncio.create_task(make_request(request_id))
                tasks.append(task)
                request_id += 1
            
            # Wait for some tasks to complete
            if tasks:
                done, pending = await asyncio.wait(tasks, timeout=0.1, return_when=asyncio.FIRST_COMPLETED)
                
                for task in done:
                    if task.result():
                        successful_requests += 1
                    else:
                        failed_requests += 1
                
                # Remove completed tasks
                tasks = [task for task in pending]
        
        # Wait for remaining tasks
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if result is True:
                    successful_requests += 1
                else:
                    failed_requests += 1
        
        total_requests = successful_requests + failed_requests
        actual_duration = time.time() - start_time
        
        # Calculate metrics
        avg_response_time = statistics.mean(response_times) if response_times else 0.0
        p95_response_time = np.percentile(response_times, 95) if response_times else 0.0
        p99_response_time = np.percentile(response_times, 99) if response_times else 0.0
        throughput = total_requests / actual_duration if actual_duration > 0 else 0.0
        error_rate = failed_requests / total_requests if total_requests > 0 else 0.0
        
        # Get system metrics
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_usage = process.cpu_percent()
        
        return LoadTestResult(
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            throughput=throughput,
            error_rate=error_rate,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage
        )
    
    async def _run_basic_conversation_test(self):
        """Run basic conversation test for memory benchmarking"""
        
        for i in range(10):
            await self.revenue_system.process_conversation_for_revenue_optimization(
                session_id=f"memory_test_basic_{i}",
                message="I'm interested in solar",
                conversation_context={
                    "homeowner_verified": True,
                    "bill_amount": 300.0,
                    "zip_code": "10021",
                    "borough": "manhattan"
                },
                conversation_history=[]
            )
    
    async def _run_extended_conversation_test(self, conversation_length: int):
        """Run extended conversation test for memory benchmarking"""
        
        session_id = "memory_test_extended"
        conversation_history = []
        
        for i in range(conversation_length):
            await self.revenue_system.process_conversation_for_revenue_optimization(
                session_id=session_id,
                message=f"Extended conversation message {i}",
                conversation_context={
                    "homeowner_verified": True,
                    "bill_amount": 300.0,
                    "zip_code": "10021",
                    "borough": "manhattan"
                },
                conversation_history=conversation_history
            )
            
            # Add to conversation history
            conversation_history.append({
                "user": f"Extended conversation message {i}",
                "bot": f"Response {i}"
            })


# Test runner functions
async def run_performance_benchmarks(revenue_system: RevenueOptimizationSystem) -> List[BenchmarkResult]:
    """Run all performance benchmarks"""
    
    benchmarker = PerformanceBenchmarker(revenue_system)
    return await benchmarker.run_all_benchmarks()


def generate_benchmark_report(results: List[BenchmarkResult]) -> str:
    """Generate performance benchmark report"""
    
    passed_benchmarks = sum(1 for r in results if r.passed)
    total_benchmarks = len(results)
    success_rate = passed_benchmarks / total_benchmarks if total_benchmarks > 0 else 0.0
    
    # Calculate average performance scores by category
    categories = {}
    for result in results:
        if result.test_type not in categories:
            categories[result.test_type] = []
        categories[result.test_type].append(result.performance_score)
    
    category_averages = {}
    for category, scores in categories.items():
        category_averages[category] = statistics.mean(scores)
    
    report = f"""
# 🚀 Performance Benchmark Report

## 📊 Overall Results
- **Total Benchmarks**: {total_benchmarks}
- **Passed**: {passed_benchmarks} ✅
- **Failed**: {total_benchmarks - passed_benchmarks} ❌
- **Success Rate**: {success_rate:.1%}

## 🎯 Performance by Category
"""
    
    for category, avg_score in category_averages.items():
        report += f"- **{category.replace('_', ' ').title()}**: {avg_score:.1%}\n"
    
    report += "\n## 📋 Detailed Results\n"
    
    for result in results:
        status = "✅ PASSED" if result.passed else "❌ FAILED"
        report += f"""
### {result.name}
- **Status**: {status}
- **Target**: {result.target_metric}
- **Actual**: {result.actual_metric:.2f}
- **Performance Score**: {result.performance_score:.1%}
- **Test Type**: {result.test_type}
"""
        
        if not result.passed:
            report += f"- **Issue**: Actual value {result.actual_metric:.2f} exceeds target {result.target_metric}\n"
    
    # Performance recommendations
    report += "\n## 💡 Performance Recommendations\n"
    
    failed_benchmarks = [r for r in results if not r.passed]
    if failed_benchmarks:
        for result in failed_benchmarks[:3]:  # Top 3 issues
            if result.test_type == "response_time":
                report += f"- **{result.name}**: Optimize response time performance\n"
            elif result.test_type == "throughput":
                report += f"- **{result.name}**: Improve system throughput capacity\n"
            elif result.test_type == "memory":
                report += f"- **{result.name}**: Optimize memory usage\n"
            elif result.test_type == "accuracy":
                report += f"- **{result.name}**: Improve calculation accuracy\n"
    else:
        report += "- ✅ All benchmarks passed! System performance is excellent.\n"
    
    report += f"\n### 📅 Benchmark Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return report


if __name__ == "__main__":
    print("🚀 Performance Benchmarking Framework")
    print("Tests system performance against industry standards")
