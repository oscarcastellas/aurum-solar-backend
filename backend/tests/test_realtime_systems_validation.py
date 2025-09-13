"""
Real-Time Systems Testing
Tests for WebSocket functionality, real-time data streaming, and Redis integration
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.redis import get_redis

client = TestClient(app)

class TestWebSocketValidation:
    """WebSocket functionality validation tests"""
    
    def test_websocket_connection_establishment(self):
        """Test WebSocket connection establishment and authentication"""
        with client.websocket_connect("/ws/chat") as websocket:
            # Test connection is established
            assert websocket is not None
            
            # Test initial handshake
            websocket.send_json({
                "type": "handshake",
                "user_id": "test_user_123"
            })
            
            response = websocket.receive_json()
            assert "type" in response
            assert response["type"] == "handshake_ack"
            
            print("✅ WebSocket connection establishment test passed")
    
    def test_websocket_message_delivery(self):
        """Test WebSocket message sending and receiving"""
        with client.websocket_connect("/ws/chat") as websocket:
            # Test message sending
            test_message = {
                "type": "message",
                "content": "Hello, I'm interested in solar",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            websocket.send_json(test_message)
            
            # Test message receiving
            response = websocket.receive_json()
            assert "type" in response
            assert "content" in response
            assert "timestamp" in response
            
            print("✅ WebSocket message delivery test passed")
    
    def test_websocket_message_ordering(self):
        """Test WebSocket message ordering and sequence"""
        with client.websocket_connect("/ws/chat") as websocket:
            messages = [
                "First message",
                "Second message",
                "Third message"
            ]
            
            sent_messages = []
            received_messages = []
            
            # Send messages
            for i, message in enumerate(messages):
                websocket.send_json({
                    "type": "message",
                    "content": message,
                    "sequence": i
                })
                sent_messages.append(message)
            
            # Receive messages
            for i in range(len(messages)):
                response = websocket.receive_json()
                received_messages.append(response["content"])
            
            # Verify message ordering
            assert sent_messages == received_messages
            
            print("✅ WebSocket message ordering test passed")
    
    def test_websocket_connection_persistence(self):
        """Test WebSocket connection persistence and stability"""
        with client.websocket_connect("/ws/chat") as websocket:
            # Test connection over time
            start_time = time.time()
            
            for i in range(10):
                websocket.send_json({
                    "type": "ping",
                    "sequence": i
                })
                
                response = websocket.receive_json()
                assert response["type"] == "pong"
                
                time.sleep(0.1)  # Small delay between messages
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert duration > 1.0  # Connection persisted for at least 1 second
            
            print("✅ WebSocket connection persistence test passed")
    
    def test_websocket_error_handling(self):
        """Test WebSocket error handling and recovery"""
        with client.websocket_connect("/ws/chat") as websocket:
            # Test invalid message format
            websocket.send_text("invalid json message")
            
            # Should handle error gracefully
            try:
                response = websocket.receive_json()
                # If we get a response, it should be an error message
                assert "error" in response or "type" in response
            except Exception:
                # Connection should remain stable even with invalid input
                pass
            
            # Test valid message after error
            websocket.send_json({
                "type": "message",
                "content": "Valid message after error"
            })
            
            response = websocket.receive_json()
            assert "content" in response
            
            print("✅ WebSocket error handling test passed")
    
    def test_websocket_concurrent_connections(self):
        """Test WebSocket concurrent connections handling"""
        connections = []
        
        try:
            # Create multiple concurrent connections
            for i in range(5):
                websocket = client.websocket_connect("/ws/chat")
                connections.append(websocket)
            
            # Test all connections work
            for i, websocket in enumerate(connections):
                with websocket as ws:
                    ws.send_json({
                        "type": "message",
                        "content": f"Message from connection {i}",
                        "connection_id": i
                    })
                    
                    response = ws.receive_json()
                    assert "content" in response
                    
            print("✅ WebSocket concurrent connections test passed")
            
        finally:
            # Clean up connections
            for connection in connections:
                try:
                    connection.close()
                except:
                    pass

class TestRealTimeDataStreaming:
    """Real-time data streaming validation tests"""
    
    def test_analytics_data_streaming(self):
        """Test real-time analytics data streaming"""
        with client.websocket_connect("/ws/analytics") as websocket:
            # Subscribe to analytics updates
            websocket.send_json({
                "type": "subscribe",
                "channel": "analytics",
                "metrics": ["revenue", "leads", "quality"]
            })
            
            # Receive subscription confirmation
            response = websocket.receive_json()
            assert response["type"] == "subscription_confirmed"
            
            # Simulate analytics update
            websocket.send_json({
                "type": "analytics_update",
                "data": {
                    "revenue": 15000.0,
                    "leads": 45,
                    "quality_score": 78.5,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
            
            # Receive analytics update
            response = websocket.receive_json()
            assert response["type"] == "analytics_update"
            assert "revenue" in response["data"]
            assert "leads" in response["data"]
            
            print("✅ Analytics data streaming test passed")
    
    def test_chat_data_streaming(self):
        """Test real-time chat data streaming"""
        with client.websocket_connect("/ws/chat") as websocket:
            # Test typing indicator
            websocket.send_json({
                "type": "typing_start",
                "user_id": "test_user"
            })
            
            response = websocket.receive_json()
            assert response["type"] == "typing_indicator"
            assert response["user_id"] == "test_user"
            assert response["is_typing"] == True
            
            # Test typing stop
            websocket.send_json({
                "type": "typing_stop",
                "user_id": "test_user"
            })
            
            response = websocket.receive_json()
            assert response["type"] == "typing_indicator"
            assert response["is_typing"] == False
            
            print("✅ Chat data streaming test passed")
    
    def test_system_status_streaming(self):
        """Test real-time system status streaming"""
        with client.websocket_connect("/ws/analytics") as websocket:
            # Subscribe to system status
            websocket.send_json({
                "type": "subscribe",
                "channel": "system_status"
            })
            
            # Receive subscription confirmation
            response = websocket.receive_json()
            assert response["type"] == "subscription_confirmed"
            
            # Simulate system status update
            websocket.send_json({
                "type": "system_status_update",
                "data": {
                    "status": "healthy",
                    "uptime": 3600,
                    "active_connections": 25,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
            
            # Receive system status update
            response = websocket.receive_json()
            assert response["type"] == "system_status_update"
            assert "status" in response["data"]
            assert "uptime" in response["data"]
            
            print("✅ System status streaming test passed")
    
    def test_data_accuracy_and_consistency(self):
        """Test real-time data accuracy and consistency"""
        with client.websocket_connect("/ws/analytics") as websocket:
            # Subscribe to multiple metrics
            websocket.send_json({
                "type": "subscribe",
                "channel": "analytics",
                "metrics": ["revenue", "leads", "conversion_rate"]
            })
            
            # Send test data
            test_data = {
                "revenue": 25000.0,
                "leads": 75,
                "conversion_rate": 0.85
            }
            
            websocket.send_json({
                "type": "analytics_update",
                "data": test_data
            })
            
            # Receive and verify data
            response = websocket.receive_json()
            assert response["type"] == "analytics_update"
            
            received_data = response["data"]
            assert received_data["revenue"] == test_data["revenue"]
            assert received_data["leads"] == test_data["leads"]
            assert received_data["conversion_rate"] == test_data["conversion_rate"]
            
            print("✅ Data accuracy and consistency test passed")

class TestRedisIntegration:
    """Redis integration validation tests"""
    
    @pytest.mark.asyncio
    async def test_redis_connection(self):
        """Test Redis connection and basic operations"""
        redis = await get_redis()
        
        # Test basic operations
        await redis.set("test_key", "test_value")
        value = await redis.get("test_key")
        assert value == "test_value"
        
        # Test expiration
        await redis.setex("test_expire", 1, "expire_value")
        value = await redis.get("test_expire")
        assert value == "expire_value"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        value = await redis.get("test_expire")
        assert value is None
        
        print("✅ Redis connection test passed")
    
    @pytest.mark.asyncio
    async def test_redis_caching_functionality(self):
        """Test Redis caching functionality"""
        redis = await get_redis()
        
        # Test cache set and get
        cache_data = {
            "revenue": 15000.0,
            "leads": 45,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await redis.set("analytics:revenue:daily", json.dumps(cache_data))
        retrieved_data = await redis.get("analytics:revenue:daily")
        
        assert retrieved_data is not None
        parsed_data = json.loads(retrieved_data)
        assert parsed_data["revenue"] == cache_data["revenue"]
        assert parsed_data["leads"] == cache_data["leads"]
        
        print("✅ Redis caching functionality test passed")
    
    @pytest.mark.asyncio
    async def test_redis_session_management(self):
        """Test Redis session management"""
        redis = await get_redis()
        
        # Test session storage
        session_data = {
            "user_id": "test_user_123",
            "conversation_id": "conv_123",
            "last_activity": datetime.utcnow().isoformat()
        }
        
        session_key = f"session:{session_data['user_id']}"
        await redis.set(session_key, json.dumps(session_data), ex=3600)
        
        # Test session retrieval
        retrieved_session = await redis.get(session_key)
        assert retrieved_session is not None
        
        parsed_session = json.loads(retrieved_session)
        assert parsed_session["user_id"] == session_data["user_id"]
        assert parsed_session["conversation_id"] == session_data["conversation_id"]
        
        # Test session cleanup
        await redis.delete(session_key)
        deleted_session = await redis.get(session_key)
        assert deleted_session is None
        
        print("✅ Redis session management test passed")
    
    @pytest.mark.asyncio
    async def test_redis_queue_management(self):
        """Test Redis queue management for delivery processing"""
        redis = await get_redis()
        
        # Test queue operations
        queue_name = "delivery_queue:test_platform"
        
        # Add items to queue
        delivery_items = [
            {"lead_id": "lead_1", "platform": "test_platform"},
            {"lead_id": "lead_2", "platform": "test_platform"},
            {"lead_id": "lead_3", "platform": "test_platform"}
        ]
        
        for item in delivery_items:
            await redis.lpush(queue_name, json.dumps(item))
        
        # Test queue length
        queue_length = await redis.llen(queue_name)
        assert queue_length == len(delivery_items)
        
        # Test queue processing
        processed_items = []
        while await redis.llen(queue_name) > 0:
            item = await redis.rpop(queue_name)
            if item:
                processed_items.append(json.loads(item))
        
        assert len(processed_items) == len(delivery_items)
        
        print("✅ Redis queue management test passed")
    
    @pytest.mark.asyncio
    async def test_redis_performance(self):
        """Test Redis performance under load"""
        redis = await get_redis()
        
        # Test bulk operations
        start_time = time.time()
        
        # Set multiple keys
        for i in range(100):
            await redis.set(f"perf_test_key_{i}", f"perf_test_value_{i}")
        
        # Get multiple keys
        for i in range(100):
            value = await redis.get(f"perf_test_key_{i}")
            assert value == f"perf_test_value_{i}"
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Performance should be under 1 second for 200 operations
        assert duration < 1.0
        
        # Cleanup
        for i in range(100):
            await redis.delete(f"perf_test_key_{i}")
        
        print(f"✅ Redis performance test passed - Duration: {duration:.2f}s")

class TestRealTimeSystemPerformance:
    """Real-time system performance validation tests"""
    
    def test_concurrent_websocket_connections(self):
        """Test system performance with concurrent WebSocket connections"""
        connections = []
        start_time = time.time()
        
        try:
            # Create 50 concurrent connections
            for i in range(50):
                websocket = client.websocket_connect("/ws/chat")
                connections.append(websocket)
            
            # Test all connections simultaneously
            for i, websocket in enumerate(connections):
                with websocket as ws:
                    ws.send_json({
                        "type": "message",
                        "content": f"Concurrent message {i}",
                        "connection_id": i
                    })
                    
                    response = ws.receive_json()
                    assert "content" in response
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should handle 50 connections in under 5 seconds
            assert duration < 5.0
            
            print(f"✅ Concurrent WebSocket connections test passed - Duration: {duration:.2f}s")
            
        finally:
            # Clean up connections
            for connection in connections:
                try:
                    connection.close()
                except:
                    pass
    
    def test_message_throughput(self):
        """Test message throughput and processing speed"""
        with client.websocket_connect("/ws/chat") as websocket:
            start_time = time.time()
            message_count = 100
            
            # Send multiple messages rapidly
            for i in range(message_count):
                websocket.send_json({
                    "type": "message",
                    "content": f"Throughput test message {i}",
                    "sequence": i
                })
            
            # Receive all responses
            for i in range(message_count):
                response = websocket.receive_json()
                assert "content" in response
            
            end_time = time.time()
            duration = end_time - start_time
            throughput = message_count / duration
            
            # Should process at least 50 messages per second
            assert throughput >= 50.0
            
            print(f"✅ Message throughput test passed - Throughput: {throughput:.2f} msg/s")
    
    @pytest.mark.asyncio
    async def test_redis_performance_under_load(self):
        """Test Redis performance under high load"""
        redis = await get_redis()
        
        start_time = time.time()
        operation_count = 1000
        
        # Perform bulk operations
        for i in range(operation_count):
            await redis.set(f"load_test_key_{i}", f"load_test_value_{i}")
        
        # Verify all operations
        for i in range(operation_count):
            value = await redis.get(f"load_test_key_{i}")
            assert value == f"load_test_value_{i}"
        
        end_time = time.time()
        duration = end_time - start_time
        operations_per_second = operation_count / duration
        
        # Should handle at least 500 operations per second
        assert operations_per_second >= 500.0
        
        # Cleanup
        for i in range(operation_count):
            await redis.delete(f"load_test_key_{i}")
        
        print(f"✅ Redis performance under load test passed - OPS: {operations_per_second:.2f}/s")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
