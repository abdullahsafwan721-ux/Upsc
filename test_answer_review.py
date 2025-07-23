#!/usr/bin/env python3

import requests
import json

# Submit a test exam
submit_data = {
    "answers": {
        "1": "A", 
        "2": "B", 
        "3": "C"
    }, 
    "markedForReview": ["2"]
}

print("🧪 Testing Answer Review Issue")
print("=" * 50)

try:
    # Submit exam
    print("1. Submitting exam...")
    response = requests.post("http://127.0.0.1:5001/submit_exam", 
                           headers={"Content-Type": "application/json"}, 
                           json=submit_data)
    
    if response.status_code == 200:
        result = response.json()
        results_id = result.get('results_id')
        print(f"   ✅ Exam submitted successfully - ID: {results_id}")
        
        # Test results page
        print("2. Testing results page...")
        results_response = requests.get(f"http://127.0.0.1:5001/results?id={results_id}")
        if results_response.status_code == 200:
            print("   ✅ Results page loads successfully")
            
            # Check if answer review button exists
            if "answer_review" in results_response.text:
                print("   ✅ Answer review button found on results page")
            else:
                print("   ❌ Answer review button NOT found on results page")
        else:
            print(f"   ❌ Results page failed with status: {results_response.status_code}")
        
        # Test answer review page
        print("3. Testing answer review page...")
        review_response = requests.get(f"http://127.0.0.1:5001/answer_review?id={results_id}")
        if review_response.status_code == 200:
            review_html = review_response.text
            print("   ✅ Answer review page loads successfully")
            
            # Check if questions are displayed
            if "Question 1" in review_html and "Question 2" in review_html:
                print("   ✅ Questions are displayed in answer review")
            else:
                print("   ❌ Questions are NOT displayed in answer review")
                print("   📝 Page content preview:")
                # Show a snippet of the content
                lines = review_html.split('\n')
                for i, line in enumerate(lines):
                    if 'Question' in line or 'answer' in line.lower():
                        print(f"      Line {i}: {line.strip()}")
                        if i > 10:  # Limit output
                            break
        else:
            print(f"   ❌ Answer review page failed with status: {review_response.status_code}")
            if review_response.status_code == 500:
                print("   🔍 Server error - checking for template issues")
    else:
        print(f"   ❌ Exam submission failed with status: {response.status_code}")
        print(f"   Response: {response.text}")

except Exception as e:
    print(f"❌ Error during testing: {e}")

print("=" * 50)
print("🏁 Test completed")
