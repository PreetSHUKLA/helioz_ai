from googleapiclient.discovery import build
import requests
import os
import re
from dotenv import load_dotenv

# Force dotenv to override any system variables
load_dotenv(override=True)

# ==========================================
# SECURE API CONFIG
# ==========================================
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

def get_candidate_videos(topic, target_count=4):
    print(f"\n🔍 Searching YouTube for: '{topic}'")
    
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    try:
        # Fetch up to 10 videos
        search_response = youtube.search().list(
            q=topic,
            part='id,snippet',
            maxResults=10, 
            type='video'
        ).execute()
    except Exception as e:
        print(f"❌ YouTube Search API Error: {e}")
        return []

    candidates = []

    for item in search_response.get('items', []):
        video_id = item['id']['videoId']
        title = item['snippet']['title']
        
        try:
            # Using the new RapidAPI JSON Endpoint!
            url = f"https://youtube-captions-transcript-subtitles-video-combiner.p.rapidapi.com/download-json/{video_id}"
            
            # language=en gets English transcripts. response_mode=default forces it to return data directly.
            querystring = {"language": "en", "response_mode": "default"}
            
            headers = {
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": "youtube-captions-transcript-subtitles-video-combiner.p.rapidapi.com"
            }

            response = requests.get(url, headers=headers, params=querystring)
            
            if response.status_code != 200:
                print(f"❌ Skipped (API Error {response.status_code}): '{title[:40]}...'")
                continue
                
            data = response.json()
            
            # The API returns a list of dictionaries: [{"start": "...", "dur": "...", "text": "words"}, ...]
            if isinstance(data, list):
                # Extract JUST the text from every timestamp
                transcript_pieces = [entry.get("text", "") for entry in data if "text" in entry]
                full_transcript = " ".join(transcript_pieces)
                
                # Clean up weird spacing and newlines
                full_transcript = re.sub(r'\s+', ' ', full_transcript).strip()
                
                if len(full_transcript) < 100:
                    print(f"❌ Skipped (Transcript too short): '{title[:40]}...'")
                    continue
                    
                candidates.append({
                    "video_id": video_id,
                    "title": title,
                    "transcript": full_transcript
                })
                
                print(f"✅ Found Transcript: '{title[:40]}...'")
                
                # Stop when we hit our target limit
                if len(candidates) >= target_count:
                    break
            else:
                print(f"❌ Skipped (No English Transcript Available): '{title[:40]}...'")

        except Exception as e:
            print(f"❌ Skipped (Failed to fetch transcript): '{title[:40]}...'")
            continue
            
    return candidates