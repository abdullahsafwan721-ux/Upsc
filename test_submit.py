#!/usr/bin/env python3
"""
Test script to simulate exam submission
"""
import requests
import json

# Test data
test_answers = {
    "1": "A",
    "2": "B", 
    "3": "C",
    "4": "A",
    "5": "B"
}

test_data = {
    "answers": test_answers,
    "markedForReview": [2, 4],
    "timeLeft": 1800,
    "submissionTime": "2025-07-23T11:10:00.000Z"
}

try:
    # Test submit endpoint
    response = requests.post(
        'http://127.0.0.1:5001/submit_exam',
        headers={'Content-Type': 'application/json'},
        json=test_data
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Submit successful!")
            # Test results page
            results_response = requests.get('http://127.0.0.1:5001/results')
            print(f"Results Status: {results_response.status_code}")
            if results_response.status_code != 200:
                print(f"❌ Results page error: {results_response.text}")
        else:
            print(f"❌ Submit failed: {data}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to server. Make sure Flask app is running.")
except Exception as e:
    print(f"❌ Error: {e}")
