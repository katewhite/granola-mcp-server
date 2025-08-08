import json
from pathlib import Path
from dateutil.parser import parse as parse_date
from datetime import datetime, timedelta, timezone

CACHE_PATH = Path("/Users/katewhite/Library/Application Support/Granola/cache-v3.json")

# Configuration - Add your identifying information here
MY_EMAIL = "kate@yourcompany.com"  # Replace with your actual email
MY_NAME = "Kate White"  # Replace with your actual name
MY_USER_ID = "19b41bfc-e113-44f4-8541-49a63b0aadcf"  # Your actual user ID (the one from meetings you were on)

def load_cache():
    if not CACHE_PATH.exists():
        raise FileNotFoundError("cache-v3.json not found in project directory")
    with open(CACHE_PATH, "r") as f:
        top = json.load(f)

        # Double-decode the embedded JSON string
        if isinstance(top.get("cache"), str):
            top["cache"] = json.loads(top["cache"])

        return top

def detect_my_user_id():
    """Try to automatically detect your user ID from the cache"""
    global MY_USER_ID
    if MY_USER_ID:
        return MY_USER_ID
    
    try:
        cache_data = load_cache()
        state = cache_data.get("cache", {}).get("state", {})
        
        # Look for user information in various places
        users = state.get("users", {})
        current_user = state.get("currentUser", {})
        
        # Try to find your user ID by email or name
        if current_user and isinstance(current_user, dict):
            user_id = current_user.get("id") or current_user.get("userId")
            if user_id:
                MY_USER_ID = str(user_id)
                print(f"🔍 Detected user ID from currentUser: {MY_USER_ID}")
                return MY_USER_ID
        
        # Search through users by email/name
        for user_id, user_data in users.items():
            if isinstance(user_data, dict):
                email = user_data.get("email", "").lower()
                name = user_data.get("name", "")
                display_name = user_data.get("displayName", "")
                
                if (MY_EMAIL and MY_EMAIL.lower() == email) or \
                   (MY_NAME and (MY_NAME.lower() in name.lower() or MY_NAME.lower() in display_name.lower())):
                    MY_USER_ID = str(user_id)
                    print(f"🔍 Detected user ID by matching email/name: {MY_USER_ID}")
                    return MY_USER_ID
        
        print("⚠️ Could not automatically detect user ID")
        return None
        
    except Exception as e:
        print(f"⚠️ Error detecting user ID: {e}")
        return None

def is_my_document(doc_id, doc, state):
    """
    Determine if a document belongs to the current user
    Updated with better logic based on Granola's actual data structure
    """
    if not isinstance(doc, dict):
        return False
    
    # Strategy 1: Check user_id field (most reliable)
    user_id = doc.get("user_id")
    if user_id:
        if MY_USER_ID and str(user_id) == MY_USER_ID:
            print(f"  ✅ Doc {doc_id}: Owned by me (user_id: {user_id})")
            return True
        else:
            print(f"  ❌ Doc {doc_id}: Owned by someone else (user_id: {user_id}, my_id: {MY_USER_ID})")
            return False
    
    # Strategy 2: Check if document is in workspace (usually team documents)
    workspace_id = doc.get("workspace_id")
    if workspace_id:
        print(f"  ❌ Doc {doc_id}: In workspace (workspace_id: {workspace_id})")
        return False
    
    # Strategy 3: Check visibility and public flags
    visibility = doc.get("visibility")
    is_public = doc.get("public", False)
    
    if is_public or visibility == "public":
        print(f"  ❌ Doc {doc_id}: Public document (public: {is_public}, visibility: {visibility})")
        return False
    
    # Strategy 4: Check number of participants - many participants usually means team meeting
    participants = doc.get("people", [])
    if isinstance(participants, list) and len(participants) > 4:
        print(f"  ❌ Doc {doc_id}: Too many participants ({len(participants)}) - likely team meeting")
        return False
    
    # Strategy 5: Check title patterns for team meetings
    title = doc.get("title", "").lower()
    team_patterns = [
        'daily standup', 'standup', 'sprint', 'retrospective', 'planning', 
        'all hands', 'team meeting', 'scrum', 'demo', 'review meeting'
    ]
    
    if any(pattern in title for pattern in team_patterns):
        print(f"  ❌ Doc {doc_id}: Team meeting pattern in title: '{doc.get('title', '')}'")
        return False
    
    # Strategy 6: Check for client/external meeting patterns
    client_patterns = [
        'intelligems &', '& intelligems', '<>', 'shopify split testing',
        'demo call', 'intro call', 'discovery call'
    ]
    
    if any(pattern in title for pattern in client_patterns):
        print(f"  ❌ Doc {doc_id}: Client/external meeting pattern: '{doc.get('title', '')}'")
        return False
    
    # Strategy 7: Look for personal meeting patterns
    personal_patterns = [
        '1:1', 'one-on-one', 'personal', 'career', 'feedback',
        'check-in', 'catch up', 'sync', '/ kate', 'kate /'
    ]
    
    if any(pattern in title for pattern in personal_patterns):
        print(f"  ✅ Doc {doc_id}: Personal meeting pattern: '{doc.get('title', '')}'")
        return True
    
    # Strategy 8: Default behavior - if we can't determine and no user_id, be more restrictive
    if not user_id:
        print(f"  ❌ Doc {doc_id}: No user_id and can't determine ownership - excluding for safety")
        return False
    
    # If we get here, include it (shouldn't happen often with user_id check)
    print(f"  🤷 Doc {doc_id}: Cannot determine ownership, defaulting to include")
    return True

def get_recent_meetings(limit=10):
    state = load_cache().get("cache", {}).get("state", {})
    documents = state.get("documents", {})

    print(f"DEBUG: Found {len(documents)} total documents")

    items = []

    for i, (doc_id, doc) in enumerate(documents.items()):
        # Filter out documents that aren't mine
        if not is_my_document(doc_id, doc, state):
            continue
            
        created = doc.get("created_at")
        title = doc.get("title", "")
        print(f"[{i}] ID: {doc_id}")
        print("  created_at:", created)
        print("  title:", title)

        if not created:
            print("  ⛔ Skipping: no timestamp")
            continue

        try:
            dt = parse_date(created)
            items.append({
                "id": doc_id,
                "title": title,
                "start_time": dt.isoformat()
            })
        except Exception as e:
            print(f"  ⚠️ Failed to parse timestamp: {e}")

    print(f"✅ Parsed {len(items)} personal documents with timestamps")
    sorted_items = sorted(items, key=lambda x: x["start_time"], reverse=True)
    return sorted_items[:limit]

def get_transcript_by_id(meeting_id):
    state = load_cache().get("cache", {}).get("state", {})
    transcripts = state.get("transcripts", {})
    entry = transcripts.get(meeting_id, {})
    return {"text": entry.get("text", "")}

def get_summary_by_id(meeting_id):
    state = load_cache().get("cache", {}).get("state", {})
    documents = state.get("documents", {})
    doc = documents.get(meeting_id, {})
    return {"text": doc.get("summary", {}).get("text", "")}

def extract_text_from_panel_content(content_dict):
    """Extract plain text from Granola's panel content structure"""
    if not isinstance(content_dict, dict):
        return ""
    
    text_parts = []
    
    def extract_recursive(obj):
        if isinstance(obj, dict):
            # Look for text content
            if 'text' in obj:
                text_parts.append(str(obj['text']))
            
            # Look for marks (formatting) with text
            if 'marks' in obj and isinstance(obj['marks'], list):
                for mark in obj['marks']:
                    if isinstance(mark, dict) and 'attrs' in mark:
                        attrs = mark['attrs']
                        if 'text' in attrs:
                            text_parts.append(str(attrs['text']))
            
            # Recursively process content arrays
            if 'content' in obj and isinstance(obj['content'], list):
                for item in obj['content']:
                    extract_recursive(item)
        elif isinstance(obj, list):
            for item in obj:
                extract_recursive(item)
    
    extract_recursive(content_dict)
    
    # Join with appropriate spacing
    result = ' '.join(text_parts).strip()
    
    # Clean up extra whitespace
    import re
    result = re.sub(r'\s+', ' ', result)
    
    return result

def extract_ai_content_from_panels(doc_id, document_panels):
    """Extract AI-generated content from document panels"""
    if doc_id not in document_panels:
        return ""
    
    panels = document_panels[doc_id]
    if not isinstance(panels, dict):
        return ""
    
    # Look for summary panels
    for panel_id, panel_data in panels.items():
        if not isinstance(panel_data, dict):
            continue
            
        # Check if this is a summary panel
        template_slug = panel_data.get('template_slug', '')
        title = panel_data.get('title', '')
        
        if 'summary' in template_slug.lower() or 'summary' in title.lower():
            content = panel_data.get('content', {})
            if isinstance(content, dict):
                extracted_text = extract_text_from_panel_content(content)
                if extracted_text.strip():
                    return extracted_text
    
    return ""

def extract_enhanced_notes(doc_id, doc, document_panels):
    """
    Extract enhanced notes combining manual notes AND AI-generated panel content
    """
    if not isinstance(doc, dict):
        print(f"  🔍 Doc {doc_id}: not a dict, type is {type(doc)}")
        return ""
    
    combined_content = []
    
    # Strategy 1: Get manual notes first
    manual_notes = ""
    if 'notes_markdown' in doc:
        value = doc['notes_markdown']
        if isinstance(value, str) and value.strip():
            manual_notes = value.strip()
            print(f"  ✅ Doc {doc_id}: Found manual notes_markdown (length: {len(manual_notes)})")
    
    if not manual_notes and 'notes_plain' in doc:
        value = doc['notes_plain']
        if isinstance(value, str) and value.strip():
            manual_notes = value.strip()
            print(f"  ✅ Doc {doc_id}: Found manual notes_plain (length: {len(manual_notes)})")
    
    # Strategy 2: Get AI-generated panel content
    ai_content = extract_ai_content_from_panels(doc_id, document_panels)
    
    # Strategy 3: Combine manual notes + AI content (like Granola UI does)
    if manual_notes and ai_content:
        # Both manual notes and AI content exist - combine them
        combined_content = f"""{manual_notes}

---

## AI-Generated Summary
{ai_content}"""
        print(f"  ✅ Doc {doc_id}: Combined manual notes + AI content (total length: {len(combined_content)})")
        return combined_content
    
    elif manual_notes:
        # Only manual notes exist
        print(f"  ✅ Doc {doc_id}: Using manual notes only (length: {len(manual_notes)})")
        return manual_notes
    
    elif ai_content:
        # Only AI content exists
        print(f"  ✅ Doc {doc_id}: Using AI-generated content only (length: {len(ai_content)})")
        return ai_content
    
    # Strategy 4: Try to extract from the 'notes' dict structure as last resort
    if 'notes' in doc:
        notes = doc['notes']
        if isinstance(notes, dict):
            extracted_text = extract_text_from_notes_structure(notes)
            if extracted_text.strip():
                print(f"  ✅ Doc {doc_id}: Extracted from notes structure (length: {len(extracted_text)})")
                return extracted_text
    
    # Strategy 5: Check summary as final fallback
    if 'summary' in doc:
        summary = doc['summary']
        if isinstance(summary, dict) and 'text' in summary:
            summary_text = summary['text']
            if isinstance(summary_text, str):
                cleaned_value = summary_text.strip()
                if cleaned_value:
                    print(f"  ✅ Doc {doc_id}: Using summary.text (length: {len(cleaned_value)})")
                    return cleaned_value
        elif isinstance(summary, str):
            cleaned_value = summary.strip()
            if cleaned_value:
                print(f"  ✅ Doc {doc_id}: Using summary as string (length: {len(cleaned_value)})")
                return cleaned_value
    
    print(f"  ⚠️ Doc {doc_id}: No enhanced notes or AI content found")
    return ""

def extract_text_from_notes_structure(notes_dict):
    """
    Extract plain text from Granola's rich text notes structure
    """
    if not isinstance(notes_dict, dict):
        return ""
    
    text_parts = []
    
    def extract_recursive(obj):
        if isinstance(obj, dict):
            # Look for text content
            if 'text' in obj:
                text_parts.append(str(obj['text']))
            
            # Recursively process content arrays
            if 'content' in obj and isinstance(obj['content'], list):
                for item in obj['content']:
                    extract_recursive(item)
        elif isinstance(obj, list):
            for item in obj:
                extract_recursive(item)
    
    extract_recursive(notes_dict)
    return ' '.join(text_parts)

def get_last_7_days_content(days_back=7):
    """
    Get all documents from the last N days with their full content (transcript + summary).
    Now includes AI-generated content from panels as fallback.
    Returns a structured format that's AI-friendly for summarization.
    UPDATED: Now filters to only include personal documents.
    """
    cache_data = load_cache()
    state = cache_data.get("cache", {}).get("state", {})
    documents = state.get("documents", {})
    transcripts = state.get("transcripts", {})
    document_panels = state.get("documentPanels", {})  # NEW: Get panels
    
    print(f"🔍 Total documents in cache: {len(documents)}")
    print(f"🔍 Total transcripts in cache: {len(transcripts)}")
    print(f"🔍 Total document panels in cache: {len(document_panels)}")
    
    # Calculate cutoff date - make it timezone-naive
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    
    recent_docs = []
    filtered_count = 0
    
    for doc_id, doc in documents.items():
        # FILTER: Only include documents that belong to me
        if not is_my_document(doc_id, doc, state):
            filtered_count += 1
            continue
            
        created = doc.get("created_at")
        if not created:
            continue
            
        try:
            created_dt = parse_date(created)
            
            # Convert both datetimes to timezone-naive for comparison
            if created_dt.tzinfo is not None:
                created_dt = created_dt.astimezone(timezone.utc).replace(tzinfo=None)
            if cutoff.tzinfo is not None:
                cutoff = cutoff.replace(tzinfo=None)
            
            if created_dt > cutoff:
                print(f"\n📄 Processing recent personal document: {doc_id}")
                
                # Get transcript text - transcripts are lists
                transcript_text = ""
                if doc_id in transcripts:
                    transcript_data = transcripts[doc_id]
                    print(f"  🔍 Transcript type: {type(transcript_data)}")
                    
                    if isinstance(transcript_data, list):
                        # Join transcript segments - each might be a dict or string
                        transcript_parts = []
                        for segment in transcript_data:
                            if isinstance(segment, dict):
                                # Look for common transcript fields
                                text = segment.get("text", "") or segment.get("content", "") or segment.get("transcript", "")
                                if text:
                                    transcript_parts.append(str(text))
                            elif isinstance(segment, str):
                                transcript_parts.append(segment)
                        transcript_text = " ".join(transcript_parts)
                    elif isinstance(transcript_data, str):
                        transcript_text = transcript_data
                    elif isinstance(transcript_data, dict):
                        # Sometimes transcript might be a dict with a text field
                        transcript_text = str(transcript_data.get("text", ""))
                    
                    print(f"  ✅ Transcript length: {len(transcript_text)}")
                else:
                    print(f"  ⚠️ No transcript found for {doc_id}")
                
                # Get enhanced notes OR AI-generated content (NEW LOGIC)
                enhanced_notes = extract_enhanced_notes(doc_id, doc, document_panels)
                
                # Ensure enhanced_notes is a string (defensive programming)
                if not isinstance(enhanced_notes, str):
                    enhanced_notes = str(enhanced_notes) if enhanced_notes is not None else ""
                
                # Safe field extraction with type checking
                title = doc.get("title", "Untitled") if isinstance(doc, dict) else "Untitled"
                duration = doc.get("duration", 0) if isinstance(doc, dict) else 0
                participants = doc.get("people", []) if isinstance(doc, dict) else []
                
                # Ensure participants is a list
                if not isinstance(participants, list):
                    participants = []
                
                # Ensure all string fields are properly converted to strings
                doc_content = {
                    "id": str(doc_id),
                    "title": str(title),
                    "created_at": created_dt.isoformat(),
                    "enhanced_notes": enhanced_notes,  # Now includes AI panel content as fallback
                    "transcript": str(transcript_text),
                    "duration": int(duration) if isinstance(duration, (int, float)) else 0,
                    "participants": [str(p) for p in participants if p]
                }
                
                print(f"  📋 Enhanced notes length: {len(enhanced_notes)}")
                print(f"  📋 Transcript length: {len(transcript_text)}")
                
                # Double-check that enhanced_notes is not empty before adding
                if enhanced_notes:
                    print(f"  ✅ Enhanced notes preview: {enhanced_notes[:100]}...")
                else:
                    print(f"  ⚠️ Enhanced notes is empty for {doc_id}")
                
                recent_docs.append(doc_content)
                
        except Exception as e:
            print(f"⚠️ Failed to process document {doc_id}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Sort by creation date (most recent first)
    recent_docs.sort(key=lambda x: x["created_at"], reverse=True)
    
    print(f"\n✅ Filtered out {filtered_count} non-personal documents")
    print(f"✅ Returning {len(recent_docs)} personal documents from last {days_back} days")
    
    # Final validation - check what we're actually returning
    for doc in recent_docs:
        print(f"Final check - {doc['id']}: enhanced_notes length = {len(doc['enhanced_notes'])}")
    
    return {
        "period": f"Last {days_back} days",
        "cutoff_date": cutoff.isoformat(),
        "total_documents": len(recent_docs),
        "filtered_documents": filtered_count,
        "documents": recent_docs
    }