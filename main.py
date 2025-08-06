from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import json
import traceback
from granola_loader import load_cache, get_recent_meetings, get_transcript_by_id, get_summary_by_id, get_last_7_days_content

app = FastAPI()

class JSONRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: dict
    id: int

@app.post("/jsonrpc")
async def jsonrpc_handler(req: Request):
    try:
        body = await req.json()
        request_data = JSONRPCRequest(**body)
        method = request_data.method
        params = request_data.params

        print(f"🔍 Received JSON-RPC request: {method} with params: {params}")

        if method == "get_recent_meetings":
            result = get_recent_meetings(params.get("limit", 10))
        elif method == "get_transcript":
            result = get_transcript_by_id(params["meeting_id"])
        elif method == "get_summary":
            result = get_summary_by_id(params["meeting_id"])
        elif method == "get_last_7_days_content":
            days_back = params.get("days_back", 7)
            result = get_last_7_days_content(days_back)
            
            # Debug: Check what we're about to return
            print(f"🔍 About to return {len(result.get('documents', []))} documents")
            for i, doc in enumerate(result.get('documents', [])):
                enhanced_notes_len = len(doc.get('enhanced_notes', ''))
                print(f"  Doc {i+1} ({doc.get('id', 'unknown')}): enhanced_notes length = {enhanced_notes_len}")
                if enhanced_notes_len > 0:
                    print(f"    Preview: {doc.get('enhanced_notes', '')[:100]}...")
        else:
            error_response = {"jsonrpc": "2.0", "id": request_data.id, "error": {"code": -32601, "message": "Method not found"}}
            print(f"❌ Unknown method: {method}")
            return JSONResponse(content=error_response)

        # Ensure the result is JSON serializable
        try:
            # Test serialization
            json.dumps(result)
            response = {"jsonrpc": "2.0", "id": request_data.id, "result": result}
            print(f"✅ Successfully processed {method}")
            return JSONResponse(content=response)
        except Exception as serialize_error:
            print(f"❌ JSON serialization error: {serialize_error}")
            error_response = {"jsonrpc": "2.0", "id": request_data.id, "error": {"code": -32603, "message": f"Serialization error: {str(serialize_error)}"}}
            return JSONResponse(content=error_response)

    except Exception as e:
        print(f"❌ Error processing request: {e}")
        traceback.print_exc()
        error_response = {"jsonrpc": "2.0", "id": getattr(request_data, 'id', 0), "error": {"code": -32603, "message": str(e)}}
        return JSONResponse(content=error_response)

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "message": "Granola MCP Server is running"}

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify data extraction"""
    try:
        result = get_last_7_days_content(7)
        return {
            "status": "success", 
            "documents_found": len(result.get('documents', [])),
            "sample_data": result
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/zapier-simple")
async def zapier_simple_endpoint():
    """Simple Zapier endpoint that returns formatted text blocks"""
    try:
        result = get_last_7_days_content(7)
        documents = result.get('documents', [])
        
        print(f"🔍 Processing {len(documents)} documents (no filtering)")
        
        # Create simple formatted text blocks for ALL documents
        formatted_calls = []
        for doc in documents:
            # Format the date nicely
            created_at = doc.get('created_at', '')
            try:
                from dateutil.parser import parse as parse_date
                dt = parse_date(created_at)
                formatted_date = dt.strftime('%B %d, %Y at %I:%M %p')
            except:
                formatted_date = created_at
            
            # Create the formatted text block
            formatted_text = f"""Title: {doc.get('title', 'Untitled')}
Call date: {formatted_date}
Enhanced Notes: {doc.get('enhanced_notes', '')}"""
            
            formatted_calls.append(formatted_text)
        
        return {
            "total_calls": len(formatted_calls),
            "calls": formatted_calls
        }
        
    except Exception as e:
        print(f"❌ Error in zapier-simple: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/zapier-simple")
async def zapier_simple_post():
    """POST version of the simple Zapier endpoint"""
    return await zapier_simple_endpoint()

if __name__ == "__main__":
    print("🚀 Starting Granola MCP Server...")
    print("📡 Health check available at: http://127.0.0.1:11434/health")
    print("🧪 Test endpoint available at: http://127.0.0.1:11434/test")
    print("🎯 Simple Zapier endpoint available at: http://127.0.0.1:11434/zapier-simple")
    uvicorn.run("main:app", host="127.0.0.1", port=11434, reload=True)