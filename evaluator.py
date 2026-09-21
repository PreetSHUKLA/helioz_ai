import json
from core import call_ai

def evaluate_transcript(topic, transcript, previous_summary="", evaluation_modifier=""):
    
    # Handle the first video case
    context_text = f"The student JUST watched a video covering: {previous_summary}\nHEAVILY PENALIZE this new video if it just repeats those concepts. It must build upon them and introduce the next logical step." if previous_summary else "This is the first video in the course. Look for a solid foundational overview."

    system_instruction = f"""
    You are an expert curriculum curator. 
    Score this video transcript (0-100) on how well it teaches '{topic}'.

    CUSTOM USER INSTRUCTIONS: 
    {evaluation_modifier if evaluation_modifier else 'None'}
    
    SEQUENTIAL LEARNING CONTEXT: 
    {context_text}

    Return ONLY a valid JSON object matching this schema:
    {{
        "score": 85,
        "reason": "1-2 sentences explaining why it scored this way.",
        "summary": "1 sentence summarizing exactly what concepts this specific video taught. (We will use this to prevent overlaps in the next video)."
    }}
    """
    
    user_prompt = f"TOPIC: {topic}\n\nTRANSCRIPT:\n{transcript}"
    
    try:
        result = call_ai(system_instruction, user_prompt, require_json=True)
        return result
    except Exception as e:
        print(f"    [AI Error]: {e}")
        return {"score": 0, "reason": "Failed to parse API.", "summary": ""}

def find_best_video(topic, candidate_videos, previous_summary="", evaluation_modifier=""):
    print(f"\n--- AI Evaluating {len(candidate_videos)} videos for: '{topic}' ---")
    
    best_video = None
    highest_score = -1
    
    for i, video in enumerate(candidate_videos):
        print(f"Evaluating: '{video['title'][:40]}...'")
        
        evaluation = evaluate_transcript(topic, video['transcript'], previous_summary, evaluation_modifier)
        
        score = int(evaluation.get('score', 0))
        reason = evaluation.get('reason', 'No reasoning provided.')
        summary = evaluation.get('summary', '')
        
        video['ai_score'] = score
        video['ai_reason'] = reason
        video['ai_summary'] = summary
        
        print(f"  -> Score: {score}/100 | Reason: {reason}")
        
        if score > highest_score:
            highest_score = score
            best_video = video
            
    if best_video:
        print(f"\n🏆 WINNER: '{best_video['title']}' (Score: {highest_score})")
        return best_video
    return None