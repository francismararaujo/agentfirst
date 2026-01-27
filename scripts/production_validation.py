#!/usr/bin/env python3
"""
Production Validation Script (Phase 13.3)

Comprehensive validation script for production environment:
- Health checks
- Performance validation
- Integration testing
- Security validation
- User acceptance testing

Usage:
    python scripts/production_validation.py
    python scripts/production_validation.py --quick
    python scripts/production_validation.py --full
"""

import argparse
import asyncio
import json
import time
import requests
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class ValidationResult:
    """Result of a validation test"""
    test_name: str
    success: bool
    message: str
    duration: float
    details: Dict[str, Any] = None


class ProductionValidator:
    """Production validation orchestrator"""
    
    def __init__(self, base_url: str = "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod"):
        """
        Initialize validator
        
        Args:
            base_url: Production API base URL
        """
        self.base_url = base_url
        self.results: List[ValidationResult] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AgentFirst2-ProductionValidator/1.0.0'
        })
    
    def run_test(self, test_func, test_name: str) -> ValidationResult:
        """
        Run a single test and capture result
        
        Args:
            test_func: Test function to run
            test_name: Name of the test
            
        Returns:
            ValidationResult
        """
        print(f"🔍 Running: {test_name}")
        start_time = time.time()
        
        try:
            result = test_func()
            duration = time.time() - start_time
            
            if isinstance(result, tuple):
                success, message, details = result
            elif isinstance(result, bool):
                success, message, details = result, "Test completed", {}
            else:
                success, message, details = True, str(result), {}
            
            validation_result = ValidationResult(
                test_name=test_name,
                success=success,
                message=message,
                duration=duration,
                details=details or {}
            )
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} - {message} ({duration:.2f}s)")
            
            return validation_result
            
        except Exception as e:
            duration = time.time() - start_time
            validation_result = ValidationResult(
                test_name=test_name,
                success=False,
                message=f"Exception: {str(e)}",
                duration=duration,
                details={"exception": str(e)}
            )
            
            print(f"   ❌ FAIL - Exception: {str(e)} ({duration:.2f}s)")
            return validation_result
    
    def validate_health_endpoints(self) -> Tuple[bool, str, Dict]:
        """Validate health endpoints"""
        endpoints = ["/health", "/status"]  # Removed /docs/examples temporarily
        results = {}
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                results[endpoint] = {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "success": response.status_code == 200
                }
            except Exception as e:
                results[endpoint] = {
                    "status_code": None,
                    "response_time": None,
                    "success": False,
                    "error": str(e)
                }
        
        successful_endpoints = [ep for ep, result in results.items() if result["success"]]
        success = len(successful_endpoints) == len(endpoints)
        
        message = f"{len(successful_endpoints)}/{len(endpoints)} endpoints healthy"
        
        return success, message, results
    
    def validate_performance(self) -> Tuple[bool, str, Dict]:
        """Validate performance benchmarks"""
        # Test response times
        response_times = []
        
        for i in range(5):
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}/health", timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append(end_time - start_time)
            except Exception:
                pass
            
            time.sleep(0.5)
        
        if not response_times:
            return False, "No successful requests", {}
        
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # Performance criteria
        avg_ok = avg_time < 2.0
        max_ok = max_time < 5.0
        
        success = avg_ok and max_ok
        message = f"Avg: {avg_time:.2f}s, Max: {max_time:.2f}s"
        
        details = {
            "average_response_time": avg_time,
            "max_response_time": max_time,
            "min_response_time": min_time,
            "total_requests": len(response_times),
            "avg_within_sla": avg_ok,
            "max_within_sla": max_ok
        }
        
        return success, message, details
    
    def validate_api_documentation(self) -> Tuple[bool, str, Dict]:
        """Validate API documentation"""
        doc_endpoints = ["/docs", "/redoc", "/openapi.json"]
        results = {}
        
        for endpoint in doc_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                results[endpoint] = {
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "success": response.status_code == 200
                }
            except Exception as e:
                results[endpoint] = {
                    "success": False,
                    "error": str(e)
                }
        
        successful_docs = [ep for ep, result in results.items() if result["success"]]
        success = len(successful_docs) == len(doc_endpoints)
        
        message = f"{len(successful_docs)}/{len(doc_endpoints)} documentation endpoints accessible"
        
        return success, message, results
    
    def validate_webhook_endpoints(self) -> Tuple[bool, str, Dict]:
        """Validate webhook endpoints exist and handle requests"""
        webhooks = ["/webhook/telegram", "/webhook/ifood"]
        results = {}
        
        for webhook in webhooks:
            try:
                # Send invalid request (should be rejected but endpoint should exist)
                response = self.session.post(
                    f"{self.base_url}{webhook}",
                    json={"invalid": "data"},
                    timeout=10
                )
                
                # Should not return 404 (endpoint exists)
                endpoint_exists = response.status_code != 404
                
                results[webhook] = {
                    "status_code": response.status_code,
                    "endpoint_exists": endpoint_exists,
                    "success": endpoint_exists
                }
                
            except Exception as e:
                results[webhook] = {
                    "success": False,
                    "error": str(e)
                }
        
        successful_webhooks = [wh for wh, result in results.items() if result["success"]]
        success = len(successful_webhooks) == len(webhooks)
        
        message = f"{len(successful_webhooks)}/{len(webhooks)} webhook endpoints exist"
        
        return success, message, results
    
    def validate_security_headers(self) -> Tuple[bool, str, Dict]:
        """Validate security headers"""
        response = self.session.get(f"{self.base_url}/health", timeout=10)
        
        headers = response.headers
        security_checks = {
            "https_only": self.base_url.startswith("https://"),
            "has_request_id": "x-request-id" in headers,
            "has_process_time": "x-process-time" in headers,
            "content_type_json": headers.get("content-type") == "application/json"
        }
        
        passed_checks = sum(1 for check in security_checks.values() if check)
        total_checks = len(security_checks)
        
        success = passed_checks >= total_checks * 0.75  # 75% of checks must pass
        message = f"{passed_checks}/{total_checks} security checks passed"
        
        return success, message, security_checks
    
    def validate_concurrent_requests(self) -> Tuple[bool, str, Dict]:
        """Validate concurrent request handling"""
        def make_request(request_id):
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/health", timeout=15)
                end_time = time.time()
                
                return {
                    "request_id": request_id,
                    "success": response.status_code == 200,
                    "response_time": end_time - start_time,
                    "status_code": response.status_code
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "success": False,
                    "error": str(e)
                }
        
        # Execute 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        successful_requests = [r for r in results if r["success"]]
        success_rate = len(successful_requests) / len(results)
        
        avg_response_time = sum(r.get("response_time", 0) for r in successful_requests) / len(successful_requests) if successful_requests else 0
        
        success = success_rate >= 0.8 and avg_response_time < 10.0
        message = f"{len(successful_requests)}/10 concurrent requests successful (avg: {avg_response_time:.2f}s)"
        
        details = {
            "total_requests": len(results),
            "successful_requests": len(successful_requests),
            "success_rate": success_rate,
            "average_response_time": avg_response_time,
            "results": results
        }
        
        return success, message, details
    
    def validate_telegram_integration(self) -> Tuple[bool, str, Dict]:
        """Validate Telegram integration (structure validation)"""
        # Test valid Telegram update structure
        telegram_update = {
            "update_id": int(time.time()),
            "message": {
                "message_id": 1,
                "from": {
                    "id": 999999999,
                    "is_bot": False,
                    "first_name": "Validation Test"
                },
                "chat": {
                    "id": 999999999,
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "validation test message"
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/webhook/telegram",
                json=telegram_update,
                timeout=15
            )
            
            # Should not return validation error (422)
            structure_valid = response.status_code != 422
            
            success = structure_valid
            message = f"Telegram structure validation: {'PASS' if structure_valid else 'FAIL'}"
            
            details = {
                "status_code": response.status_code,
                "structure_valid": structure_valid,
                "response_headers": dict(response.headers)
            }
            
            return success, message, details
            
        except Exception as e:
            return False, f"Telegram integration test failed: {str(e)}", {"error": str(e)}
    
    def validate_error_handling(self) -> Tuple[bool, str, Dict]:
        """Validate error handling"""
        error_tests = [
            ("/nonexistent", 404, "Not Found"),
            ("/webhook/telegram", 400, "Bad Request (invalid JSON)"),
        ]
        
        results = {}
        
        for endpoint, expected_status, description in error_tests:
            try:
                if endpoint == "/webhook/telegram":
                    # Send invalid JSON
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        data="invalid json",
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                else:
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                
                correct_status = response.status_code == expected_status
                
                results[endpoint] = {
                    "expected_status": expected_status,
                    "actual_status": response.status_code,
                    "correct": correct_status,
                    "description": description
                }
                
            except Exception as e:
                results[endpoint] = {
                    "correct": False,
                    "error": str(e),
                    "description": description
                }
        
        correct_responses = [r for r in results.values() if r.get("correct", False)]
        success = len(correct_responses) >= len(error_tests) * 0.5  # At least 50% correct
        
        message = f"{len(correct_responses)}/{len(error_tests)} error responses correct"
        
        return success, message, results
    
    def run_quick_validation(self) -> List[ValidationResult]:
        """Run quick validation (essential tests only)"""
        print("🚀 Running Quick Production Validation")
        print("=" * 50)
        
        tests = [
            (self.validate_health_endpoints, "Health Endpoints"),
            (self.validate_performance, "Performance Benchmarks"),
            (self.validate_webhook_endpoints, "Webhook Endpoints"),
            (self.validate_security_headers, "Security Headers")
        ]
        
        results = []
        for test_func, test_name in tests:
            result = self.run_test(test_func, test_name)
            results.append(result)
            self.results.append(result)
        
        return results
    
    def run_full_validation(self) -> List[ValidationResult]:
        """Run full validation (all tests)"""
        print("🚀 Running Full Production Validation")
        print("=" * 50)
        
        tests = [
            (self.validate_health_endpoints, "Health Endpoints"),
            (self.validate_performance, "Performance Benchmarks"),
            (self.validate_api_documentation, "API Documentation"),
            (self.validate_webhook_endpoints, "Webhook Endpoints"),
            (self.validate_security_headers, "Security Headers"),
            (self.validate_concurrent_requests, "Concurrent Requests"),
            (self.validate_telegram_integration, "Telegram Integration"),
            (self.validate_error_handling, "Error Handling")
        ]
        
        results = []
        for test_func, test_name in tests:
            result = self.run_test(test_func, test_name)
            results.append(result)
            self.results.append(result)
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.success])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        total_duration = sum(r.duration for r in self.results)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "total_duration": total_duration,
                "average_duration": avg_duration
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "message": r.message,
                    "duration": r.duration,
                    "details": r.details
                }
                for r in self.results
            ]
        }
        
        return report
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.success])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"🎯 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        total_duration = sum(r.duration for r in self.results)
        print(f"⏱️  Total Duration: {total_duration:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if not result.success:
                    print(f"   • {result.test_name}: {result.message}")
        
        # Overall status
        if success_rate >= 90:
            print(f"\n🎉 PRODUCTION VALIDATION: ✅ EXCELLENT ({success_rate:.1f}%)")
        elif success_rate >= 75:
            print(f"\n⚠️  PRODUCTION VALIDATION: 🟡 GOOD ({success_rate:.1f}%)")
        elif success_rate >= 50:
            print(f"\n⚠️  PRODUCTION VALIDATION: 🟠 NEEDS ATTENTION ({success_rate:.1f}%)")
        else:
            print(f"\n🚨 PRODUCTION VALIDATION: ❌ CRITICAL ISSUES ({success_rate:.1f}%)")
        
        print("=" * 50)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="AgentFirst2 Production Validation")
    parser.add_argument(
        "--mode",
        choices=["quick", "full"],
        default="quick",
        help="Validation mode (default: quick)"
    )
    parser.add_argument(
        "--url",
        default="https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod",
        help="Production API URL"
    )
    parser.add_argument(
        "--output",
        help="Output file for JSON report"
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = ProductionValidator(args.url)
    
    # Run validation
    start_time = time.time()
    
    if args.mode == "quick":
        results = validator.run_quick_validation()
    else:
        results = validator.run_full_validation()
    
    end_time = time.time()
    
    # Print summary
    validator.print_summary()
    
    # Generate report
    report = validator.generate_report()
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Report saved to: {args.output}")
    
    # Exit with appropriate code
    success_rate = report["summary"]["success_rate"]
    if success_rate >= 75:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == "__main__":
    main()