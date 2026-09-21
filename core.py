import requests
import json
import base64
import os
import re # Added for robust JSON extraction

# ==========================================
# API CONFIG
# ==========================================
API_KEY = os.getenv("API_KEY") # Replace with your Lightning AI key
URL = "https://lightning.ai/api/v1/chat/completions"

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def call_ai(system_instruction, user_prompt, image_path=None, require_json=False):
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": [{"type": "text", "text": system_instruction}]})
        
    user_content = [{"type": "text", "text": user_prompt}]
    
    if image_path and os.path.exists(image_path):
        base64_image = encode_image(image_path)
        ext = image_path.split('.')[-1].lower()
        mime_type = "image/png" if ext == "png" else "image/jpeg"
        user_content.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}})

    messages.append({"role": "user", "content": user_content})

    payload = {"model": "google/gemini-3-flash-preview", "messages": messages}
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    response = requests.post(URL, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        raise Exception(f"API Error {response.status_code}: {response.text}")
        
    content = json.loads(response.content)['choices'][0]['message']['content']
    
    if require_json:
        try:
            # BULLETPROOF JSON PARSING: Finds the JSON object even if AI adds markdown or conversational text
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return json.loads(content)
        except Exception as e:
            print(f"    [!] JSON Parse Error. Raw Output:\n{content}")
            return {}
        
    return content

def parse_syllabus(text=None, image_path=None):
    system_prompt = """
    You are an expert curriculum architect and pedagogy specialist.
    Analyze the provided syllabus (text or image) along with any custom instructions (e.g. language preferences, target depth).
    
    CRITICAL TOPIC EXTRACTION RULES:
    1. Do NOT create broad, vague umbrella topics (e.g. avoid 'Data Structures' or 'Advanced Math').
    2. Deconstruct the curriculum into a detailed sequence of 6 to 8 highly granular, bite-sized, single-concept micro-topics (e.g. 'Pointers and Memory Addresses in C', 'Matrix Determinants and Inverses').
    3. Ensure the topics follow a strict pedagogical progression where each concept builds directly on the previous one.
    4. Extract any search modifier (e.g., 'in Hindi', 'practical code demo') and evaluation rules.

    Return ONLY a valid JSON object matching this schema:
    {
        "course_title": "Clear Name of the Course",
        "topics": [
            "Topic 1: Specific single concept",
            "Topic 2: Specific single concept",
            "Topic 3: Specific single concept",
            "Topic 4: Specific single concept",
            "Topic 5: Specific single concept",
            "Topic 6: Specific single concept"
        ],
        "search_modifier": "Search keywords or empty string",
        "evaluation_modifier": "Evaluation criteria or empty string"
    }
    """
    prompt = text if text else "Please break down this syllabus into granular, sequential micro-topics."
    
    print("\n[AI] Generating Granular Micro-Curriculum...")
    result = call_ai(system_prompt, prompt, image_path=image_path, require_json=True)
    return result