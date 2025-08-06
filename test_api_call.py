#!/usr/bin/env python3

import requests
import json

def test_api_call():
    """Test the API exactly like Zapier would call it"""
    
    # Test the health endpoint first
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get("http://127.0.0.1:11434/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return

    # Test the simple test endpoint
    print("\n🧪 Testing simple test endpoint...")
    try:
        response = requests.get("http://127.0.0.1:11434/test")
        result = response.json()
        print(f"Test endpoint: {response.status_code}")
        print(f"Documents found: {result.get('documents_found', 0)}")
        if result.get('status') == 'success' and result.get('sample_data', {}).get('documents'):
            for i, doc in enumerate(result['sample_data']['documents']):
                print(f"  Doc {i+1}: enhanced_notes length = {len(doc.get('enhanced_notes', ''))}")
    except Exception as e:
        print(f"❌ Test endpoint failed: {e}")

    # Test the JSON-RPC endpoint (like Zapier would)
    print("\n📡 Testing JSON-RPC endpoint (like Zapier)...")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "get_last_7_days_content",
        "params": {"days_back": 7},
        "id": 1
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:11434/jsonrpc",
            data=json.dumps(payload),
            headers=headers
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if "result" in result:
                data = result["result"]
                print(f"✅ Success! Found {data.get('total_documents', 0)} documents")
                
                # Check each document's enhanced_notes
                for i, doc in enumerate(data.get('documents', [])):
                    enhanced_notes = doc.get('enhanced_notes', '')
                    transcript = doc.get('transcript', '')
                    print(f"\nDocument {i+1} ({doc.get('id', 'unknown')}):")
                    print(f"  Title: {doc.get('title', 'N/A')}")
                    print(f"  Enhanced notes length: {len(enhanced_notes)}")
                    print(f"  Transcript length: {len(transcript)}")
                    
                    if enhanced_notes:
                        print(f"  Enhanced notes preview: {enhanced_notes[:100]}...")
                    else:
                        print(f"  ⚠️ Enhanced notes is EMPTY!")
                        
                    if transcript:
                        print(f"  Transcript preview: {transcript[:100]}...")
                    else:
                        print(f"  ⚠️ Transcript is empty!")
                
            elif "error" in result:
                print(f"❌ JSON-RPC Error: {result['error']}")
            else:
                print(f"❌ Unexpected response format: {result}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing Granola API like Zapier would...")
    test_api_call()