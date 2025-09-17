#!/usr/bin/env python3

import asyncio
import websockets
import json
import ssl

async def test_websocket():
    uri = "wss://aurum-solarv3-production.up.railway.app/ws/chat"
    
    # Create SSL context that doesn't verify certificates (for testing)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        print("Testing WebSocket connection...")
        print(f"Connecting to: {uri}")
        
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send a test message
            test_message = {
                "message": "Hello WebSocket!",
                "session_id": "test123"
            }
            
            print(f"Sending test message: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            print(f"✅ Received response: {response}")
            
            # Send another message
            test_message2 = {
                "message": "How are you?",
                "session_id": "test123"
            }
            
            print(f"Sending second message: {test_message2}")
            await websocket.send(json.dumps(test_message2))
            
            # Wait for response
            response2 = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            print(f"✅ Received second response: {response2}")
            
            print("✅ WebSocket test completed successfully!")
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket connection failed with status code: {e.status_code}")
        print(f"Response headers: {e.response_headers}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket connection closed: {e}")
    except asyncio.TimeoutError:
        print("❌ WebSocket response timeout")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
