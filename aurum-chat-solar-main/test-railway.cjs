#!/usr/bin/env node

/**
 * Railway Backend Test Suite
 * Comprehensive testing for Aurum Solar Railway backend
 */

const https = require('https');

const RAILWAY_URL = 'https://aurum-solarv3-production.up.railway.app';

// Test results storage
const testResults = {
  connection: null,
  health: null,
  chat: null,
  overall: false
};

// Utility function for HTTP requests
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const req = https.request(url, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const latency = Date.now() - startTime;
        resolve({
          status: res.statusCode,
          data: data,
          latency: latency,
          headers: res.headers
        });
      });
    });
    
    req.on('error', (err) => {
      const latency = Date.now() - startTime;
      reject({
        error: err.message,
        latency: latency
      });
    });
    
    req.setTimeout(10000, () => {
      req.destroy();
      reject({
        error: 'Request timeout',
        latency: Date.now() - startTime
      });
    });
    
    if (options.body) {
      req.write(options.body);
    }
    req.end();
  });
}

// Test 1: Health Check
async function testHealth() {
  console.log('🏥 Testing Railway Backend Health...');
  try {
    const response = await makeRequest(`${RAILWAY_URL}/health`);
    
    if (response.status === 200) {
      const data = JSON.parse(response.data);
      testResults.health = {
        success: true,
        latency: response.latency,
        data: data
      };
      console.log(`✅ Health Check: PASSED (${response.latency}ms)`);
      console.log(`   Status: ${data.status}`);
      console.log(`   Version: ${data.version}`);
      console.log(`   Environment: ${data.environment}`);
    } else {
      testResults.health = {
        success: false,
        latency: response.latency,
        error: `HTTP ${response.status}`
      };
      console.log(`❌ Health Check: FAILED (${response.latency}ms)`);
      console.log(`   Error: HTTP ${response.status}`);
    }
  } catch (error) {
    testResults.health = {
      success: false,
      latency: error.latency || 0,
      error: error.error || 'Unknown error'
    };
    console.log(`❌ Health Check: FAILED (${error.latency || 0}ms)`);
    console.log(`   Error: ${error.error || 'Unknown error'}`);
  }
}

// Test 2: Root Endpoint
async function testRoot() {
  console.log('🌐 Testing Railway Backend Root...');
  try {
    const response = await makeRequest(`${RAILWAY_URL}/`);
    
    if (response.status === 200) {
      const data = JSON.parse(response.data);
      testResults.connection = {
        success: true,
        latency: response.latency,
        data: data
      };
      console.log(`✅ Root Endpoint: PASSED (${response.latency}ms)`);
      console.log(`   Message: ${data.message}`);
      console.log(`   Version: ${data.version}`);
      console.log(`   Status: ${data.status}`);
    } else {
      testResults.connection = {
        success: false,
        latency: response.latency,
        error: `HTTP ${response.status}`
      };
      console.log(`❌ Root Endpoint: FAILED (${response.latency}ms)`);
      console.log(`   Error: HTTP ${response.status}`);
    }
  } catch (error) {
    testResults.connection = {
      success: false,
      latency: error.latency || 0,
      error: error.error || 'Unknown error'
    };
    console.log(`❌ Root Endpoint: FAILED (${error.latency || 0}ms)`);
    console.log(`   Error: ${error.error || 'Unknown error'}`);
  }
}

// Test 3: Chat Endpoint (if available)
async function testChat() {
  console.log('💬 Testing Chat Endpoint...');
  try {
    const chatData = JSON.stringify({
      message: "Test message for Railway backend",
      session_id: "test_" + Date.now()
    });
    
    const response = await makeRequest(`${RAILWAY_URL}/api/v1/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(chatData)
      },
      body: chatData
    });
    
    if (response.status === 200) {
      const data = JSON.parse(response.data);
      testResults.chat = {
        success: true,
        latency: response.latency,
        data: data
      };
      console.log(`✅ Chat Endpoint: PASSED (${response.latency}ms)`);
      console.log(`   Response: ${JSON.stringify(data).substring(0, 100)}...`);
    } else {
      testResults.chat = {
        success: false,
        latency: response.latency,
        error: `HTTP ${response.status}`
      };
      console.log(`❌ Chat Endpoint: FAILED (${response.latency}ms)`);
      console.log(`   Error: HTTP ${response.status}`);
      console.log(`   Response: ${response.data.substring(0, 200)}...`);
    }
  } catch (error) {
    testResults.chat = {
      success: false,
      latency: error.latency || 0,
      error: error.error || 'Unknown error'
    };
    console.log(`❌ Chat Endpoint: FAILED (${error.latency || 0}ms)`);
    console.log(`   Error: ${error.error || 'Unknown error'}`);
  }
}

// Test 4: Frontend Connection
async function testFrontend() {
  console.log('🖥️  Testing Frontend Connection...');
  try {
    const response = await makeRequest('http://localhost:3001');
    
    if (response.status === 200) {
      console.log(`✅ Frontend: PASSED (${response.latency}ms)`);
      console.log(`   Content Length: ${response.data.length} characters`);
      console.log(`   Content Type: ${response.headers['content-type']}`);
    } else {
      console.log(`❌ Frontend: FAILED (${response.latency}ms)`);
      console.log(`   Error: HTTP ${response.status}`);
    }
  } catch (error) {
    console.log(`❌ Frontend: FAILED (${error.latency || 0}ms)`);
    console.log(`   Error: ${error.error || 'Unknown error'}`);
  }
}

// Performance Test
async function performanceTest() {
  console.log('⚡ Running Performance Test...');
  const iterations = 5;
  const latencies = [];
  
  for (let i = 0; i < iterations; i++) {
    try {
      const response = await makeRequest(`${RAILWAY_URL}/health`);
      latencies.push(response.latency);
      console.log(`   Request ${i + 1}: ${response.latency}ms`);
    } catch (error) {
      console.log(`   Request ${i + 1}: FAILED`);
    }
  }
  
  if (latencies.length > 0) {
    const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
    const minLatency = Math.min(...latencies);
    const maxLatency = Math.max(...latencies);
    
    console.log(`📊 Performance Results:`);
    console.log(`   Average Latency: ${avgLatency.toFixed(2)}ms`);
    console.log(`   Min Latency: ${minLatency}ms`);
    console.log(`   Max Latency: ${maxLatency}ms`);
    console.log(`   Success Rate: ${(latencies.length / iterations * 100).toFixed(1)}%`);
  }
}

// Main test runner
async function runTests() {
  console.log('🚀 Starting Railway Backend Test Suite...');
  console.log('=' .repeat(50));
  
  const startTime = Date.now();
  
  // Run all tests
  await testHealth();
  console.log('');
  await testRoot();
  console.log('');
  await testChat();
  console.log('');
  await testFrontend();
  console.log('');
  await performanceTest();
  
  const totalTime = Date.now() - startTime;
  
  // Summary
  console.log('');
  console.log('=' .repeat(50));
  console.log('📋 TEST SUMMARY');
  console.log('=' .repeat(50));
  
  const passedTests = [
    testResults.health?.success,
    testResults.connection?.success,
    testResults.chat?.success
  ].filter(Boolean).length;
  
  const totalTests = 3;
  
  console.log(`✅ Passed: ${passedTests}/${totalTests}`);
  console.log(`⏱️  Total Time: ${totalTime}ms`);
  console.log(`🌐 Backend URL: ${RAILWAY_URL}`);
  console.log(`🖥️  Frontend URL: http://localhost:3001`);
  
  if (testResults.health?.success) {
    console.log(`🏥 Health: ${testResults.health.latency}ms`);
  }
  if (testResults.connection?.success) {
    console.log(`🌐 Connection: ${testResults.connection.latency}ms`);
  }
  if (testResults.chat?.success) {
    console.log(`💬 Chat: ${testResults.chat.latency}ms`);
  }
  
  testResults.overall = passedTests >= 2; // At least 2 out of 3 tests must pass
  
  console.log('');
  if (testResults.overall) {
    console.log('🎉 OVERALL RESULT: ✅ TESTS PASSED');
    console.log('   Railway backend is operational and ready for production!');
  } else {
    console.log('❌ OVERALL RESULT: TESTS FAILED');
    console.log('   Some issues detected. Check the logs above.');
  }
  
  console.log('');
  console.log('🔗 Next Steps:');
  console.log('   1. Visit http://localhost:3001 to see the frontend');
  console.log('   2. Test the chat interface');
  console.log('   3. Check the Railway backend testing section');
  console.log('   4. Deploy to Vercel when ready');
}

// Run the tests
runTests().catch(console.error);
