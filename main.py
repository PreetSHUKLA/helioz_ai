import json
from core import parse_syllabus
from youtube_pipeline import get_candidate_videos
from evaluator import find_best_video
from quiz_generator import generate_quiz

def generate_full_course(syllabus_text=None, syllabus_image=None, max_topics=5):
    # 1. Parse Syllabus and extract user preferences
    syllabus = parse_syllabus(text=syllabus_text, image_path=syllabus_image)
    
    course_title = syllabus.get("course_title", "Generated Course")
    all_topics = syllabus.get("topics", [])
    search_modifier = syllabus.get("search_modifier", "")
    evaluation_modifier = syllabus.get("evaluation_modifier", "")
    
    topics_to_process = all_topics[:max_topics]
    print(f"\n📚 Course: {course_title}")
    if search_modifier or evaluation_modifier:
        print(f"🎯 Custom Instructions Applied: {search_modifier} | {evaluation_modifier}")
    
    full_course = {
        "course_title": course_title,
        "modules": []
    }
    
    # Track context across the loop!
    previous_summary = ""
    
    # 2. Loop through topics
    for i, topic in enumerate(topics_to_process):
        print(f"\n{'='*50}\n🚀 BUILDING MODULE {i+1}: {topic}\n{'='*50}")
        
        # Append search modifier (e.g., "in Hindi") to the YouTube query
        search_query = f"{topic} {search_modifier}".strip()
        candidates = get_candidate_videos(search_query, target_count=4) 
        
        if not candidates:
            continue

        # Pass the previous summary and user instructions to the Evaluator
        best_video = find_best_video(topic, candidates, previous_summary, evaluation_modifier)
        
        if not best_video:
            continue
            
        # Update the context for the NEXT loop!
        previous_summary = best_video.get('ai_summary', '')
        
        print("\n[PHASE 3: GENERATING QUIZ]")
        quiz_data = generate_quiz(topic, best_video['transcript'], num_questions=3)

        full_course["modules"].append({
            "topic": topic,
            "video_url": f"https://www.youtube.com/watch?v={best_video['video_id']}",
            "video_title": best_video['title'],
            "quiz": quiz_data.get('quiz', []) if quiz_data else []
        })
            
    return full_course