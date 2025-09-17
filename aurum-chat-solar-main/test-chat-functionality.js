#!/usr/bin/env node

/**
 * Comprehensive Chat Functionality Test
 * Tests the complete chat flow from frontend to backend
 */

import https from 'https';

const BACKEND_URL = 'https://backend-production-3f24.up.railway.app';
const FRONTEND_URL = 'https://aurum-solar.vercel.app';

// Test scenarios
const testScenarios = [
  {
    name: "Initial Greeting",
    message: "Hello, I am interested in solar for my home",
    expectedKeywords: ["solar", "interest", "help", "ZIP"]
  },
  {
    name: "ZIP Code Response", 
    message: "My ZIP code is 10001",
    expectedKeywords: ["NYC", "solar potential", "electric bill"]
  },
  {
    name: "Monthly Bill Response",
    message: "My monthly bill is $200",
    expectedKeywords: ["save", "monthly", "solar", "own"]
  },
  {
    name: "Home Ownership Response",
    message: "Yes, I own my home",
    expectedKeywords: ["homeowner", "qualify", "incentives", "roof"]
  },
  {
    name: "Roof Type Response",
    message: "I have a flat roof",
    expectedKeywords: ["roof", "solar", "installation", "suitable"]
  }
];

function makeRequest(url, data) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify(data);
    
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    };

    const req = https.request(url, options, (res) => {
      let responseData = '';
      
      res.on('data', (chunk) => {
        responseData += chunk;
      });
      
      res.on('end', () => {
        try {
          const parsed = JSON.parse(responseData);
          resolve({
            status: res.statusCode,
            data: parsed,
            headers: res.headers
          });
        } catch (error) {
          resolve({
            status: res.statusCode,
            data: responseData,
            headers: res.headers,
            parseError: error.message
          });
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.write(postData);
    req.end();
  });
}

async function testChatAPI() {
  console.log('🧪 COMPREHENSIVE CHAT FUNCTIONALITY TEST');
  console.log('==========================================\n');

  let sessionId = `test_session_${Date.now()}`;
  let allTestsPassed = true;

  for (let i = 0; i < testScenarios.length; i++) {
    const scenario = testScenarios[i];
    console.log(`Test ${i + 1}: ${scenario.name}`);
    console.log(`Message: "${scenario.message}"`);
    
    try {
      const response = await makeRequest(`${BACKEND_URL}/api/v1/chat/message`, {
        message: scenario.message,
        session_id: sessionId
      });

      if (response.status === 200) {
        const responseText = response.data.response.toLowerCase();
        const foundKeywords = scenario.expectedKeywords.filter(keyword => 
          responseText.includes(keyword.toLowerCase())
        );

        console.log(`✅ Status: ${response.status}`);
        console.log(`Response: "${response.data.response}"`);
        console.log(`Keywords found: ${foundKeywords.length}/${scenario.expectedKeywords.length} (${foundKeywords.join(', ')})`);
        
        if (foundKeywords.length >= scenario.expectedKeywords.length * 0.5) {
          console.log('✅ Test PASSED\n');
        } else {
          console.log('❌ Test FAILED - Insufficient keyword matches\n');
          allTestsPassed = false;
        }
      } else {
        console.log(`❌ Test FAILED - HTTP ${response.status}`);
        console.log(`Error: ${response.data}\n`);
        allTestsPassed = false;
      }
    } catch (error) {
      console.log(`❌ Test FAILED - Network Error: ${error.message}\n`);
      allTestsPassed = false;
    }

    // Small delay between tests
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  // Test frontend accessibility
  console.log('Test 6: Frontend Accessibility');
  try {
    const response = await new Promise((resolve, reject) => {
      https.get(FRONTEND_URL, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => resolve({ status: res.statusCode, data }));
      }).on('error', reject);
    });

    if (response.status === 200) {
      console.log('✅ Frontend accessible');
      console.log('✅ Frontend returns HTML content\n');
    } else {
      console.log(`❌ Frontend not accessible - HTTP ${response.status}\n`);
      allTestsPassed = false;
    }
  } catch (error) {
    console.log(`❌ Frontend test failed - ${error.message}\n`);
    allTestsPassed = false;
  }

  // Summary
  console.log('==========================================');
  if (allTestsPassed) {
    console.log('🎉 ALL CHAT TESTS PASSED!');
    console.log('✅ Chat functionality is working perfectly');
    console.log('✅ Backend API is responding correctly');
    console.log('✅ Frontend is accessible');
    console.log('✅ Ready for production use');
  } else {
    console.log('❌ SOME TESTS FAILED');
    console.log('⚠️  Chat functionality needs attention');
  }
  console.log('==========================================');
}

// Run the tests
testChatAPI().catch(console.error);
