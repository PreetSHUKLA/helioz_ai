import json
from core import call_ai

# Maximum transcript characters sent to the LLM to prevent token overflow and slow API calls
MAX_TRANSCRIPT_CHARS = 12000
MIN_PASSING_SCORE = 40

def evaluate_transcript(topic, video_title, transcript, previous_summary="", evaluation_modifier=""):
    # Handle sequential context without asking for a broad "overview" on Video 1
    context_text = (
        f"The student JUST watched a video covering: {previous_summary}\n"
        "HEAVILY PENALIZE this candidate if it mostly repeats those exact concepts. "
        "Reward it if it briefly bridges from them and focuses directly on the current micro-topic."
        if previous_summary else
        "This is the first micro-topic in the sequence. Reward a clear, beginner-friendly entry directly into this specific micro-topic (avoid broad syllabus-wide overviews)."
    )

    system_instruction = f"""
    You are an expert technical curriculum curator.
    Evaluate how well this YouTube video teaches the specific 10-minute micro-topic: '{topic}'.

    SCORING RUBRIC (0-100):
    - 85-100: Laser-focused on the exact micro-topic with clear explanations/examples and minimal fluff.
    - 60-84: Teaches the micro-topic well, but includes some tangential material or minor repetition.
    - 30-59: Too broad (e.g., a giant crash course covering the whole subject superficially) or only briefly mentions the topic.
    - 0-29: Irrelevant, clickbait, wrong language, or mostly repeats the previous video.

    CUSTOM USER INSTRUCTIONS:
    {evaluation_modifier if evaluation_modifier else 'None'}

    SEQUENTIAL LEARNING CONTEXT:
    {context_text}

    Return ONLY a valid JSON object matching this exact schema:
    {{
        "score": <integer from 0 to 100>,
        "reason": "1-2 concise sentences explaining the score based on focus, depth, and sequential fit.",
        "summary": "1 specific sentence listing the exact sub-concepts and examples taught in this video (used to prevent overlap in the next module)."
    }}
    """

    trimmed_transcript = (transcript or "")[:MAX_TRANSCRIPT_CHARS]
    user_prompt = (
        f"TARGET MICRO-TOPIC: {topic}\n"
        f"VIDEO TITLE: {video_title}\n\n"
        f"TRANSCRIPT:\n{trimmed_transcript}"
    )

    try:
        result = call_ai(system_instruction, user_prompt, require_json=True)
        if not isinstance(result, dict):
            return {"score": 0, "reason": "Invalid JSON format returned.", "summary": ""}
        return result
    except Exception as e:
        print(f"    [AI Error]: {e}")
        return {"score": 0, "reason": "Failed to parse API.", "summary": ""}


def _parse_score(raw_score):
    """Safely converts LLM score output into a bounded integer (0-100)."""
    try:
        if isinstance(raw_score, str):
            raw_score = raw_score.split("/")[0].strip()
        return max(0, min(100, int(float(raw_score))))
    except (ValueError, TypeError):
        return 0


def find_best_video(topic, candidate_videos, previous_summary="", evaluation_modifier=""):
    print(f"\n--- AI Evaluating {len(candidate_videos)} videos for: '{topic}' ---")

    best_video = None
    highest_score = -1

    for video in candidate_videos:
        title = video.get("title", "Untitled Video")
        transcript = video.get("transcript", "")
        print(f"Evaluating: '{title[:50]}...'")

        if not transcript or not transcript.strip():
            print("  -> Skipped: Empty transcript.")
            continue

        evaluation = evaluate_transcript(
            topic=topic,
            video_title=title,
            transcript=transcript,
            previous_summary=previous_summary,
            evaluation_modifier=evaluation_modifier
        )

        score = _parse_score(evaluation.get("score", 0))
        reason = evaluation.get("reason", "No reasoning provided.")
        summary = evaluation.get("summary", "")

        video["ai_score"] = score
        video["ai_reason"] = reason
        video["ai_summary"] = summary

        print(f"  -> Score: {score}/100 | Reason: {reason}")

        if score > highest_score:
            highest_score = score
            best_video = video

    if best_video and highest_score >= MIN_PASSING_SCORE:
        print(f"\n[SELECTED LECTURE]: '{best_video['title']}' (Score: {highest_score}/100)")
        return best_video

    print(f"\n[!] No candidate met the minimum quality threshold ({MIN_PASSING_SCORE}/100) for '{topic}'.")
    return None