#!/usr/bin/env python3
"""
Fix existing seminars that have speaker_id=0 by linking them to proper speakers.
"""

import urllib.request
import urllib.error
import json

BASE_URL = "https://seminars-app.fly.dev"

# Test JWT token (valid token for the inacio user)
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImluYWNpbyIsIm5hbWUiOiJJbmFjaW8iLCJyb2xlIjoib3duZXIiLCJleHAiOjE3NzE1MDYxNTZ9.dzUTeFOQPE3-UbLN_yPsSw6mxr7YSDgQB27llPORNOc"

def make_request(method, url, data=None):
    """Make HTTP request using urllib."""
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    
    if data:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode('utf-8')
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

def main():
    print("=" * 60)
    print("Fixing seminars with speaker_id=0")
    print("=" * 60)
    
    # Get all seminars
    status, seminars = make_request("GET", f"{BASE_URL}/api/seminars")
    if status != 200:
        print(f"Failed to fetch seminars: {status}")
        return
    
    # Get all speakers
    status, speakers = make_request("GET", f"{BASE_URL}/api/speakers")
    if status != 200:
        print(f"Failed to fetch speakers: {status}")
        return
    
    # Get all suggestions
    status, suggestions = make_request("GET", f"{BASE_URL}/api/v1/seminars/speaker-suggestions")
    if status != 200:
        print(f"Failed to fetch suggestions: {status}")
        return
    
    # Create speaker name -> speaker_id mapping
    speaker_by_name = {s['name'].strip().lower(): s['id'] for s in speakers}
    
    # Create suggestion -> speaker_name mapping
    suggestion_speakers = {s['id']: s['speaker_name'] for s in suggestions}
    
    fixed_count = 0
    for seminar in seminars:
        if seminar.get('speaker_id') == 0 or seminar.get('speaker_id') is None:
            # Try to find the speaker from the title or suggestion
            title = seminar.get('title', '')
            
            # Try to match "Seminar by {speaker_name}" pattern
            speaker_name = None
            if title.startswith("Seminar by "):
                speaker_name = title.replace("Seminar by ", "").strip()
            
            # If we found a speaker name, look up the speaker_id
            if speaker_name:
                speaker_id = speaker_by_name.get(speaker_name.lower())
                if speaker_id:
                    # Update the seminar
                    print(f"Fixing seminar {seminar['id']}: '{title}' -> speaker '{speaker_name}' (id={speaker_id})")
                    status, result = make_request("PUT", f"{BASE_URL}/api/seminars/{seminar['id']}", {
                        "speaker_id": speaker_id
                    })
                    if status == 200:
                        fixed_count += 1
                        print(f"  ✓ Fixed!")
                    else:
                        print(f"  ✗ Failed: {status} {result}")
                else:
                    print(f"Seminar {seminar['id']}: Speaker '{speaker_name}' not found in speakers list")
            else:
                print(f"Seminar {seminar['id']}: Could not extract speaker name from title '{title}'")
    
    print("\n" + "=" * 60)
    print(f"Fixed {fixed_count} seminars")
    print("=" * 60)

if __name__ == "__main__":
    main()
