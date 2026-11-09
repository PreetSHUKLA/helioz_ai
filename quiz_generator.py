import json
from core import call_ai

MAX_TRANSCRIPT_CHARS = 12000

def _normalize_quiz_output(raw_result, num_questions):
    """
    Ensures the return value is always {"quiz": [...]} and guarantees that
    'correct_answer' exactly matches one of the strings inside 'options'.
    """
    if isinstance(raw_result, list):
        quiz_list = raw_result
    elif isinstance(raw_result, dict):
        quiz_list = raw_result.get("quiz", [])
    else:
        return {"quiz": []}

    if not isinstance(quiz_list, list):
        return {"quiz": []}

    letter_to_idx = {"A": 0, "B": 1, "C": 2, "D": 3}
    cleaned_quiz = []

    for item in quiz_list:
        if not isinstance(item, dict):
            continue

        question = str(item.get("question", "")).strip()
        options = item.get("options", [])
        correct = str(item.get("correct_answer", "")).strip()

        if not question or not isinstance(options, list) or len(options) < 2:
            continue

        options = [str(opt).strip() for opt in options[:4]]

        # If the LLM returned "B" or "B)" instead of the actual option text, map it to the option string
        upper_correct = correct.rstrip(").:").upper()
        if correct not in options and upper_correct in letter_to_idx:
            idx = letter_to_idx[upper_correct]
            if idx < len(options):
                correct = options[idx]

        # Secondary check: if options have "A) ..." prefixes and correct doesn't (or vice versa)
        if correct not in options:
            for opt in options:
                if correct.lower() in opt.lower() or opt.lower() in correct.lower():
                    correct = opt
                    break
            else:
                # Fallback to first option only if completely unmatched so UI never breaks
                correct = options[0]

        cleaned_quiz.append({
            "question": question,
            "options": options,
            "correct_answer": correct
        })

    return {"quiz": cleaned_quiz[:num_questions]}


def generate_quiz(topic, transcript, num_questions=3):
    """
    Generates a JSON-formatted multiple-choice quiz based strictly
    on the content of the winning video's transcript.
    """
    print(f"\n--- Generating Quiz for: '{topic}' ---")

    if not transcript or not transcript.strip():
        print("    [!] Empty transcript provided to quiz generator.")
        return {"quiz": []}

    system_instruction = f"""
    You are an expert technical professor and pedagogical examiner.
    Based STRICTLY on the provided video transcript about the micro-topic "{topic}", generate a multiple-choice quiz with exactly {num_questions} questions.

    CRITICAL QUIZ RULES:
    1. Test conceptual understanding and practical application, not rote memorization.
    2. Base every question strictly on facts/examples covered in the transcript.
    3. Write all questions and options in clear English (even if the transcript is in Hindi or another language).
    4. Each question must have exactly 4 distinct options (do NOT prefix options with "A.", "B.", etc.).
    5. The "correct_answer" field MUST be an exact character-for-character copy of the winning string from the "options" array (NOT a single letter like "A" or "B").
    6. Randomize which option position (1st, 2nd, 3rd, or 4th) holds the correct answer across questions.

    Return ONLY a valid JSON object matching this exact schema:
    {{
        "quiz": [
            {{
                "question": "Clear, specific conceptual question?",
                "options": [
                    "First plausible option text",
                    "Second plausible option text",
                    "Third plausible option text",
                    "Fourth plausible option text"
                ],
                "correct_answer": "Exact copy of the correct option text from the options list above"
            }}
        ]
    }}
    """

    trimmed_transcript = transcript[:MAX_TRANSCRIPT_CHARS]
    user_prompt = f"MICRO-TOPIC: {topic}\n\nTRANSCRIPT:\n{trimmed_transcript}"

    try:
        result = call_ai(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            require_json=True
        )
        return _normalize_quiz_output(result, num_questions)
    except Exception as e:
        print(f"    [AI Error generating quiz]: {e}")
        return {"quiz": []}


# ==========================================
# TEST IT OUT (Standalone)
# ==========================================
if __name__ == "__main__":
    sample_topic = "Time Complexity and Big O"
    dummy_transcript = (
        "Time complexity measures how the runtime of an algorithm grows as the input size n increases. "
        "Accessing an array element by index takes O(1) constant time. "
        "A single loop iterating through n elements takes O(n) linear time, while nested loops over n elements take O(n^2) quadratic time."
    )

    quiz_data = generate_quiz(sample_topic, dummy_transcript, num_questions=2)

    if quiz_data and quiz_data.get("quiz"):
        print("\n[+] Quiz Generated Successfully!\n")
        print(json.dumps(quiz_data, indent=2))