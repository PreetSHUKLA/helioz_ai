import json
from core import call_ai

def generate_quiz(topic, transcript, num_questions=4):
    """
    Generates a JSON-formatted multiple-choice quiz based strictly 
    on the content of the winning video's transcript.
    """
    print(f"\n--- Generating Quiz for: '{topic}' ---")
    
    # Notice the DOUBLE curly braces {{ }} below. 
    # This tells Python to ignore them and treat them as normal text for the JSON schema.
    system_instruction = f"""
    You are an expert Computer Science professor. 
    Based STRICTLY on the provided video transcript about "{topic}", generate a multiple-choice quiz with {num_questions} questions.
    
    Guidelines:
    1. Test conceptual understanding and application, not just rote memorization.
    2. Do not ask about topics that were not explicitly covered in the transcript.
    
    Return ONLY a valid JSON object exactly matching this schema:
    {{
        "quiz": [
            {{
                "question": "Clear question text?",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "B"
            }}
        ]
    }}
    """
    
    user_prompt = f"TRANSCRIPT:\n{transcript}"
    
    try:
        # We enforce require_json=True so core.py cleans the output
        result = call_ai(
            system_instruction=system_instruction, 
            user_prompt=user_prompt, 
            require_json=True
        )
        return result
    except Exception as e:
        print(f"    [AI Error generating quiz]: {e}")
        return None

# ==========================================
# TEST IT OUT (Standalone)
# ==========================================
if __name__ == "__main__":
    sample_topic = "Time Complexity and Big O"
    dummy_transcript = "Time complexity measures how the runtime grows... A simple loop is O(n)."
    
    quiz_data = generate_quiz(sample_topic, dummy_transcript, num_questions=2)
    
    if quiz_data:
        print("\n✅ Quiz Generated Successfully!\n")
        print(json.dumps(quiz_data, indent=2))