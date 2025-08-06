#!/usr/bin/env python3

import requests
import json

def test_zapier_endpoint():
    """Test the new Zapier-friendly endpoint"""
    
    print("🧪 Testing Zapier-friendly endpoint...")
    
    try:
        # Test GET version
        response = requests.get("http://127.0.0.1:11434/zapier")
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Success! Found {result.get('total_documents', 0)} documents")
            print(f"Period: {result.get('period', 'N/A')}")
            
            # Check the flattened document fields
            for i in range(1, 11):  # Check up to 10 documents
                title_key = f"document_{i}_title"
                notes_key = f"document_{i}_enhanced_notes"
                
                if title_key in result:
                    title = result[title_key]
                    notes = result[notes_key]
                    
                    print(f"\nDocument {i}:")
                    print(f"  Title: {title}")
                    print(f"  Enhanced notes length: {len(notes)}")
                    
                    if notes:
                        preview = notes[:100] + "..." if len(notes) > 100 else notes
                        print(f"  Enhanced notes preview: {preview}")
                    else:
                        print(f"  ⚠️ Enhanced notes is EMPTY!")
                else:
                    print(f"\nNo more documents after document {i-1}")
                    break
            
            # Test POST version too
            print(f"\n📡 Testing POST version...")
            post_response = requests.post("http://127.0.0.1:11434/zapier")
            
            if post_response.status_code == 200:
                print("✅ POST version works too!")
            else:
                print(f"❌ POST version failed: {post_response.status_code}")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_zapier_endpoint()