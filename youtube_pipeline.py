from googleapiclient.discovery import build
import requests
import os
import re
import html
from dotenv import load_dotenv

# Force dotenv to override any system variables
load_dotenv(override=True)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# Preferred caption languages in priority order (English, Indian English, Hindi)
PREFERRED_LANGS = ["en", "en-IN", "en-US", "hi"]

# ======================================================================
# TRANSCRIPT STRATEGY:
#   Tier 1 (Free, No Key) : youtube-transcript-api  (direct, fastest)
#   Tier 2 (RapidAPI)     : youtube-transcriptor host (more reliable)
#   Tier 3 (RapidAPI)     : youtube-captions-... host (last resort)
# ======================================================================

def _get_transcript_tier1_free(video_id, preferred_langs=None):
    """
    Uses the open-source youtube-transcript-api package.
    Supports both v1.x instance API (.fetch/.list) and legacy v0.6 static API.
    """
    langs = preferred_langs or PREFERRED_LANGS
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        fetched = None

        # Support new youtube-transcript-api (v1.0+) instance methods
        if hasattr(YouTubeTranscriptApi, "fetch"):
            ytt_api = YouTubeTranscriptApi()
            try:
                fetched = ytt_api.fetch(video_id, languages=langs)
            except Exception:
                try:
                    transcript_list = ytt_api.list(video_id)
                    for t in transcript_list:
                        try:
                            fetched = t.fetch()
                            break
                        except Exception:
                            continue
                except Exception:
                    return None
        # Fallback if environment has youtube-transcript-api v0.6.x installed
        elif hasattr(YouTubeTranscriptApi, "get_transcript"):
            try:
                fetched = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)
            except Exception:
                return None

        if not fetched:
            return None

        texts = []
        for item in fetched:
            text = item.text if hasattr(item, "text") else item.get("text", "")
            if text:
                texts.append(text)

        full_text = " ".join(texts)
        full_text = re.sub(r"\s+", " ", full_text).strip()
        return full_text if len(full_text) > 100 else None

    except Exception:
        return None


def _get_transcript_tier2_rapidapi(video_id, rapid_key, lang="en"):
    """
    Uses the 'youtube-transcriptor' host on RapidAPI.
    Tries primary language first, then falls back to Hindi/English if needed.
    """
    if not rapid_key:
        return None

    url = "https://youtube-transcriptor.p.rapidapi.com/transcript"
    headers = {
        "x-rapidapi-key": rapid_key,
        "x-rapidapi-host": "youtube-transcriptor.p.rapidapi.com"
    }

    for try_lang in [lang, "en", "hi"]:
        try:
            params = {"video_id": video_id, "lang": try_lang}
            response = requests.get(url, headers=headers, params=params, timeout=20)

            if response.status_code != 200:
                continue

            data = response.json()
            if isinstance(data, list) and data:
                transcription_entries = data[0].get("transcription", [])
                texts = [e.get("subtitle", "") for e in transcription_entries if e.get("subtitle")]
                full_text = " ".join(texts)
                full_text = re.sub(r"\s+", " ", full_text).strip()
                if len(full_text) > 100:
                    return full_text
        except Exception:
            continue

    return None


def _get_transcript_tier3_rapidapi_original(video_id, rapid_key, lang="en"):
    """
    Original host as a last resort.
    """
    if not rapid_key:
        return None

    url = f"https://youtube-captions-transcript-subtitles-video-combiner.p.rapidapi.com/download-json/{video_id}"
    headers = {
        "x-rapidapi-key": rapid_key,
        "x-rapidapi-host": "youtube-captions-transcript-subtitles-video-combiner.p.rapidapi.com"
    }

    for try_lang in [lang, "en", "hi"]:
        try:
            response = requests.get(url, headers=headers, params={"language": try_lang}, timeout=25)

            if response.status_code != 200:
                continue

            data = response.json()
            if isinstance(data, list):
                texts = [e.get("text", "") for e in data if e.get("text")]
                full_text = " ".join(texts)
                full_text = re.sub(r"\s+", " ", full_text).strip()
                if len(full_text) > 100:
                    return full_text
        except Exception:
            continue

    return None


def fetch_transcript(video_id, rapid_key=None, prefer_hindi=False):
    """
    Attempts all 3 tiers in order. Returns (transcript_text, source) or (None, None).
    """
    langs = ["hi", "en-IN", "en", "en-US"] if prefer_hindi else PREFERRED_LANGS
    primary_lang = "hi" if prefer_hindi else "en"

    # Tier 1: Free library (fastest, no key needed)
    text = _get_transcript_tier1_free(video_id, preferred_langs=langs)
    if text:
        return text, "free-library"

    # Tier 2: RapidAPI youtube-transcriptor
    if rapid_key:
        text = _get_transcript_tier2_rapidapi(video_id, rapid_key, lang=primary_lang)
        if text:
            return text, "rapidapi-transcriptor"

    # Tier 3: Original RapidAPI host
    if rapid_key:
        text = _get_transcript_tier3_rapidapi_original(video_id, rapid_key, lang=primary_lang)
        if text:
            return text, "rapidapi-original"

    return None, None


def get_candidate_videos(topic, target_count=4):
    """
    Searches YouTube for focused (4-20 min) videos matching the micro-topic,
    then retrieves their transcripts using the 3-tier strategy.
    """
    youtube_key = os.getenv("YOUTUBE_API_KEY", YOUTUBE_API_KEY)
    rapid_key = os.getenv("RAPIDAPI_KEY", RAPIDAPI_KEY)

    if not youtube_key or youtube_key.strip() in ("", "your_youtube_api_key_here"):
        print("[YouTube Pipeline] YOUTUBE_API_KEY is not configured in .env. Skipping.")
        return []

    if not rapid_key or rapid_key.strip() in ("", "your_rapidapi_key_here"):
        print("[YouTube Pipeline] RAPIDAPI_KEY not set. Using free transcript library only.")
        rapid_key = None

    prefer_hindi = "hindi" in topic.lower()
    relevance_lang = "hi" if prefer_hindi else "en"

    print(f"\n[*] Searching YouTube (4-20 min micro-lectures) for: '{topic}'")

    try:
        youtube = build("youtube", "v3", developerKey=youtube_key)
        
        # videoDuration='medium' restricts results to 4-20 mins (ideal for 10-min micro-topics)
        # videoEmbeddable='true' ensures the video won't be blocked if embedded in a frontend UI
        search_response = youtube.search().list(
            q=topic,
            part="id,snippet",
            maxResults=12,
            type="video",
            videoDuration="medium",
            videoEmbeddable="true",
            relevanceLanguage=relevance_lang
        ).execute()
        items = search_response.get("items", [])

        # Fallback: if 'medium' duration returned very few videos on a niche topic, broaden duration
        if len(items) < target_count:
            fallback_response = youtube.search().list(
                q=topic,
                part="id,snippet",
                maxResults=10,
                type="video",
                videoEmbeddable="true",
                relevanceLanguage=relevance_lang
            ).execute()
            seen_ids = {item.get("id", {}).get("videoId") for item in items}
            for fb_item in fallback_response.get("items", []):
                fb_id = fb_item.get("id", {}).get("videoId")
                if fb_id and fb_id not in seen_ids:
                    items.append(fb_item)

    except Exception as e:
        print(f"    [!] YouTube Search API Error: {e}")
        return []

    candidates = []

    for item in items:
        video_id = item.get("id", {}).get("videoId")
        if not video_id:
            continue

        raw_title = item.get("snippet", {}).get("title", "Untitled Video")
        title = html.unescape(raw_title)
        safe_title = title.encode("ascii", errors="replace").decode("ascii")

        transcript, source = fetch_transcript(video_id, rapid_key, prefer_hindi=prefer_hindi)

        if transcript:
            candidates.append({
                "video_id": video_id,
                "title": title,
                "transcript": transcript
            })
            print(f"    [+] Got transcript via '{source}': {safe_title[:55]}...")
        else:
            print(f"    [-] No transcript available:  {safe_title[:55]}...")

        if len(candidates) >= target_count:
            break

    if not candidates:
        print(f"    [!] No candidates with transcripts found for: {topic}")

    return candidates