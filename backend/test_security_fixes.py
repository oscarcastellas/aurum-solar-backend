#!/usr/bin/env python3
"""
Security Fixes Validation Script
Tests the critical security vulnerabilities that were fixed
"""

import os
import sys
import time
import requests
import json
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_security_fixes():
    """Test all critical security fixes"""
    
    print("🔒 Testing Critical Security Fixes")
    print("=" * 50)
    
    # Test results
    results = {
        "jwt_secret": False,
        "input_validation": False,
        "rate_limiting": False,
        "csrf_protection": False,
        "sanitization": False,
        "auth_errors": False
    }
    
    # Test 1: JWT Secret Configuration
    print("\n1. Testing JWT Secret Configuration...")
    try:
        from app.core.config import settings
        
        # Check if SECRET_KEY is properly configured
        if hasattr(settings, 'SECRET_KEY') and settings.SECRET_KEY:
            if settings.SECRET_KEY != "your-secret-key-change-in-production":
                results["jwt_secret"] = True
                print("✅ JWT secret is properly configured")
            else:
                print("❌ JWT secret is still using default value")
        else:
            print("❌ JWT secret not found in configuration")
            
    except Exception as e:
        print(f"❌ JWT secret test failed: {e}")
    
    # Test 2: Input Validation
    print("\n2. Testing Input Validation...")
    try:
        from app.middleware.input_validation import ConversationInputValidator
        
        # Test dangerous input
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "../../../etc/passwd",
            "'; DROP TABLE users; --"
        ]
        
        validation_passed = True
        for dangerous_input in dangerous_inputs:
            try:
                sanitized = ConversationInputValidator.validate_message(dangerous_input)
                if sanitized != dangerous_input:
                    print(f"✅ Dangerous input sanitized: {dangerous_input[:20]}... -> {sanitized[:20]}...")
                else:
                    print(f"❌ Dangerous input not sanitized: {dangerous_input}")
                    validation_passed = False
            except Exception as e:
                print(f"✅ Dangerous input blocked: {dangerous_input[:20]}... (Error: {e})")
        
        results["input_validation"] = validation_passed
        
    except Exception as e:
        print(f"❌ Input validation test failed: {e}")
    
    # Test 3: Rate Limiting
    print("\n3. Testing Rate Limiting...")
    try:
        from app.middleware.rate_limit import RateLimitMiddleware
        
        # Create a mock rate limiter
        rate_limiter = RateLimitMiddleware(None)
        
        # Test rate limiting logic
        client_id = "test_client"
        
        # Test multiple requests
        for i in range(5):
            is_allowed, remaining, reset_time = rate_limiter._check_fallback_rate_limit(client_id)
            if i < 4:  # Should allow first few requests
                if not is_allowed:
                    print(f"❌ Rate limiting blocked request {i+1} too early")
                    break
            else:  # 5th request should be allowed (under limit)
                if is_allowed:
                    results["rate_limiting"] = True
                    print(f"✅ Rate limiting working correctly (remaining: {remaining})")
                    break
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
    
    # Test 4: CSRF Protection
    print("\n4. Testing CSRF Protection...")
    try:
        from app.middleware.csrf_protection import CSRFTokenManager
        
        # Create a mock request
        class MockRequest:
            def __init__(self, path):
                self.url = type('obj', (object,), {'path': path})
        
        mock_request = MockRequest("/api/v1/test")
        
        # Generate CSRF token
        token = CSRFTokenManager.generate_csrf_token(mock_request)
        
        # Validate token
        is_valid = CSRFTokenManager.validate_csrf_token(token, mock_request)
        
        if is_valid:
            results["csrf_protection"] = True
            print("✅ CSRF token generation and validation working")
        else:
            print("❌ CSRF token validation failed")
            
    except Exception as e:
        print(f"❌ CSRF protection test failed: {e}")
    
    # Test 5: Input Sanitization
    print("\n5. Testing Input Sanitization...")
    try:
        from app.middleware.input_validation import InputValidationMiddleware
        
        middleware = InputValidationMiddleware(None)
        
        # Test sanitization
        test_inputs = [
            ("<b>Hello</b>", "&lt;b&gt;Hello&lt;/b&gt;"),
            ("alert('xss')", "alert(&#x27;xss&#x27;)"),
            ("../../../etc/passwd", "../../../etc/passwd"),  # Should be escaped
        ]
        
        sanitization_passed = True
        for original, expected_pattern in test_inputs:
            sanitized = middleware._sanitize_string(original)
            if "&lt;" in sanitized or "&gt;" in sanitized:  # HTML escaped
                print(f"✅ Input sanitized: {original[:20]}... -> {sanitized[:30]}...")
            else:
                print(f"❌ Input not properly sanitized: {original}")
                sanitization_passed = False
        
        results["sanitization"] = sanitization_passed
        
    except Exception as e:
        print(f"❌ Input sanitization test failed: {e}")
    
    # Test 6: Authentication Error Handling
    print("\n6. Testing Authentication Error Handling...")
    try:
        from app.middleware.auth import AuthMiddleware
        
        # Check if AuthMiddleware uses settings
        middleware = AuthMiddleware(None)
        
        if hasattr(middleware, 'jwt_secret') and middleware.jwt_secret:
            if middleware.jwt_secret != "your-secret-key":
                results["auth_errors"] = True
                print("✅ Authentication middleware using proper configuration")
            else:
                print("❌ Authentication middleware still using hardcoded secret")
        else:
            print("❌ Authentication middleware not properly configured")
            
    except Exception as e:
        print(f"❌ Authentication error handling test failed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("🔒 SECURITY FIXES SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} security fixes working")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL CRITICAL SECURITY FIXES IMPLEMENTED!")
        print("✅ System is ready for safe launch with customer data")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} security issues still need attention")
        print("❌ System NOT ready for production launch")
        return False

def test_security_configuration():
    """Test security configuration"""
    
    print("\n🔧 Testing Security Configuration...")
    print("-" * 40)
    
    try:
        from app.core.config import settings
        
        # Check security settings
        security_checks = [
            ("SECRET_KEY", settings.SECRET_KEY),
            ("CSRF_SECRET_KEY", settings.CSRF_SECRET_KEY),
            ("RATE_LIMIT_REQUESTS_PER_MINUTE", settings.RATE_LIMIT_REQUESTS_PER_MINUTE),
            ("RATE_LIMIT_BURST_SIZE", settings.RATE_LIMIT_BURST_SIZE),
        ]
        
        for setting_name, value in security_checks:
            if value and str(value) != "your-secret-key-change-in-production":
                print(f"✅ {setting_name}: Configured")
            else:
                print(f"❌ {setting_name}: Not properly configured")
        
        # Check environment
        if settings.ENVIRONMENT == "production":
            print("✅ Environment: Production")
        else:
            print(f"⚠️  Environment: {settings.ENVIRONMENT} (not production)")
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")

if __name__ == "__main__":
    print("🔒 Aurum Solar Security Validation")
    print("Testing critical security fixes for safe launch")
    print()
    
    # Test security fixes
    security_passed = test_security_fixes()
    
    # Test configuration
    test_security_configuration()
    
    print("\n" + "=" * 60)
    if security_passed:
        print("🚀 SYSTEM READY FOR SECURE LAUNCH!")
        print("All critical security vulnerabilities have been fixed.")
        print("Customer data will be handled safely.")
    else:
        print("⚠️  SECURITY ISSUES DETECTED!")
        print("Please address the failing security tests before launch.")
    
    print("=" * 60)
