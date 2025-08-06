import requests
import json

def test_7_days_content():
    """Test the new get_last_7_days_content endpoint"""
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "get_last_7_days_content",
        "params": {"days_back": 7}  # Optional, defaults to 7
    }
    
    try:
        response = requests.post("http://localhost:11434/jsonrpc", json=payload)
        data = response.json()
        
        if "error" in data:
            print(f"❌ Error: {data['error']}")
            return
            
        result = data["result"]
        
        print(f"✅ Success! Retrieved content for the last 7 days:")
        print(f"📅 Period: {result['period']}")
        print(f"📊 Total documents: {result['total_documents']}")
        print(f"⏰ Cutoff date: {result['cutoff_date']}")
        print("\n📋 Documents found:")
        
        for i, doc in enumerate(result["documents"], 1):
            print(f"\n[{i}] {doc['title']}")
            print(f"    📅 Created: {doc['created_at']}")
            
            # Safe length checking with new field names
            transcript_len = len(doc['transcript']) if doc['transcript'] else 0
            enhanced_notes_len = len(doc['enhanced_notes']) if doc['enhanced_notes'] else 0
            
            print(f"    📝 Transcript length: {transcript_len} chars")
            print(f"    📄 Enhanced notes length: {enhanced_notes_len} chars")
            print(f"    ⏱️ Duration: {doc.get('duration', 0)} seconds")
            
            # Show debug info
            if 'debug_notes' in doc:
                debug = doc['debug_notes']
                print(f"    🔍 Debug - Markdown: {debug['has_notes_markdown']} ({debug['markdown_length']} chars)")
                print(f"    🔍 Debug - Plain: {debug['has_notes_plain']} ({debug['plain_length']} chars)")
            
            # Show a preview of the content
            if doc['transcript']:
                preview = doc['transcript'][:100] + "..." if len(doc['transcript']) > 100 else doc['transcript']
                print(f"    🎤 Transcript preview: {preview}")
            
            if doc['enhanced_notes']:
                notes_preview = doc['enhanced_notes'][:100] + "..." if len(doc['enhanced_notes']) > 100 else doc['enhanced_notes']
                print(f"    📋 Enhanced notes preview: {notes_preview}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure your MCP server is running on localhost:11434")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_7_days_content()