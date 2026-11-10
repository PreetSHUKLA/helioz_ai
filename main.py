import json
from core import parse_syllabus
from youtube_pipeline import get_candidate_videos
from evaluator import find_best_video
from quiz_generator import generate_quiz
import os
from dotenv import load_dotenv

def generate_full_course(syllabus_text=None, syllabus_image=None, max_topics=3):
    # 1. Parse Syllabus and extract user preferences
    syllabus = parse_syllabus(text=syllabus_text, image_path=syllabus_image)
    
    course_title = syllabus.get("course_title", "Generated Course")
    all_topics = syllabus.get("topics", [])
    search_modifier = syllabus.get("search_modifier", "")
    evaluation_modifier = syllabus.get("evaluation_modifier", "")
    
    # Route only the top 3 serial micro-topics (controlled by max_topics=3)
    topics_to_process = all_topics[:max_topics]
    print(f"\n[Course]: {course_title}")
    if search_modifier or evaluation_modifier:
        print(f"[Instructions]: Search Mod='{search_modifier}' | Eval Mod='{evaluation_modifier}'")
    
    full_course = {
        "course_title": course_title,
        "modules": []
    }

    
    # Track context across sequential modules
    previous_summary = ""
    
    # 2. Loop through the top 3 structured micro-topics
    for i, topic_item in enumerate(topics_to_process):
        # Safely unpack structured object (with fallback if a plain string is ever returned)
        if isinstance(topic_item, dict):
            topic_title = topic_item.get("title", f"Micro-Topic {i+1}")
            core_concept = topic_item.get("core_concept", "")
            base_query = topic_item.get("search_query") or topic_title
        else:
            topic_title = str(topic_item)
            core_concept = ""
            base_query = topic_title

        print(f"\n{'='*50}\n[*] BUILDING MODULE {i+1}: {topic_title}\n{'='*50}")
        if core_concept:
            print(f"[*] 10-Min Goal: {core_concept}")
        
        # Append search modifier (e.g., "in Hindi") to the targeted YouTube search query
        search_query = f"{base_query} {search_modifier}".strip()
        candidates = get_candidate_videos(search_query, target_count=4) 
        
        if not candidates:
            print(f"[-] No candidate videos found for: {topic_title}")
            continue

        # Give the evaluator both the title and the 10-min core concept for better video selection
        eval_topic_context = f"{topic_title} ({core_concept})" if core_concept else topic_title
        best_video = find_best_video(eval_topic_context, candidates, previous_summary, evaluation_modifier)
        
        if not best_video:
            print(f"[-] No suitable video evaluated for: {topic_title}")
            continue
            
        # Update context for the next loop
        previous_summary = best_video.get('ai_summary', '')
        
        print("\n[PHASE 3: GENERATING ACTIVE RECALL QUIZ]")
        quiz_data = generate_quiz(topic_title, best_video['transcript'], num_questions=3)

        full_course["modules"].append({
            "topic": topic_title,
            "core_concept": core_concept,
            "video_url": f"https://www.youtube.com/watch?v={best_video['video_id']}",
            "video_title": best_video['title'],
            "quiz": quiz_data.get('quiz', []) if quiz_data else []
        })
            
    return full_course

def save_course_to_firedb(course_data, user_id="local-developer"):
    """Stores generated course data directly into FireDB Firestore."""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
        if not firebase_admin._apps:
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)

        db = firestore.client()
        doc_ref = db.collection("notebooks").document()
        course_data["id"] = doc_ref.id
        course_data["user_id"] = user_id
        doc_ref.set(course_data)
        print(f"\n[+] Course successfully saved to FireDB with ID: {doc_ref.id}")
        return doc_ref.id
    except Exception as e:
        print(f"\n[-] Failed to store course in FireDB: {e}")
        return None