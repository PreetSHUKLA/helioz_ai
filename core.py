import requests
import json
import base64
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# ==========================================
# META API CONFIGURATION
# ==========================================
# Supports official Meta Model API, Llama API, or any OpenAI-compatible Meta endpoint
META_API_KEY = (
    os.getenv("META_API_KEY")
    or os.getenv("MODEL_API_KEY")
    or os.getenv("LLAMA_API_KEY")
    or os.getenv("API_KEY")
)
META_API_URL = os.getenv("META_API_URL", "https://api.meta.ai/v1/chat/completions")
META_MODEL = os.getenv("META_MODEL", "llama-3.3-70b-instruct")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_json_from_text(text):
    """
    Bulletproof JSON extractor that cleans markdown code fences,
    comments, and extracts pure JSON dicts or lists.
    """
    if not text:
        return {}
    
    # 1. Clean markdown code fences like ```json ... ```
    cleaned = re.sub(r'```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    cleaned = cleaned.replace('```', '').strip()
    
    # 2. Try direct parse first
    try:
        return json.loads(cleaned)
    except Exception:
        pass
        
    # 3. Find outer-most JSON object using regex
    match = re.search(r'(\{[\s\S]*\})', text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # 4. Find outer-most JSON array if needed
    match_arr = re.search(r'(\[[\s\S]*\])', text)
    if match_arr:
        try:
            return json.loads(match_arr.group(1))
        except Exception:
            pass

    return {}

def call_ai(system_instruction, user_prompt, image_path=None, require_json=False):
    """
    Executes a completion call to the Meta API.
    """
    api_key = (
        os.getenv("META_API_KEY")
        or os.getenv("MODEL_API_KEY")
        or os.getenv("LLAMA_API_KEY")
        or os.getenv("API_KEY")
        or META_API_KEY
    )
    api_url = os.getenv("META_API_URL", META_API_URL)
    model = os.getenv("META_MODEL", META_MODEL)

    if not api_key or api_key.strip() in ("", "your_meta_api_key_here"):
        raise ValueError(
            "META_API_KEY is missing or unconfigured. "
            "Please add your Meta API key to the .env file (META_API_KEY=your_key)."
        )

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
        
    if image_path and os.path.exists(image_path):
        base64_image = encode_image(image_path)
        ext = image_path.split('.')[-1].lower()
        mime_type = "image/png" if ext == "png" else "image/jpeg"
        user_content = [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
        ]
        messages.append({"role": "user", "content": user_content})
    else:
        messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=90)
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to connect to Meta API at {api_url}: {e}")

    if response.status_code != 200:
        raise Exception(f"Meta API Error ({response.status_code}): {response.text}")
        
    try:
        response_json = response.json()
        content = response_json['choices'][0]['message']['content']
    except Exception as e:
        raise ValueError(f"Unexpected response structure from Meta API: {response.text}") from e
    
    if require_json:
        parsed = extract_json_from_text(content)
        if not parsed:
            print(f"    [!] JSON Parse Warning. Raw Meta Output:\n{content}")
        return parsed
        
    return content

def parse_syllabus(text=None, image_path=None):
    system_prompt = """
    You are an expert curriculum architect and pedagogy specialist.
    
    CRITICAL INPUT HANDLING (TWO MODES):
    - MODE A (SYLLABUS IMAGE OR MULTI-LINE SYLLABUS PROVIDED): 
      Strictly anchor to the exact topics visible in the provided syllabus image/text. Do NOT invent outside subjects or hallucinate unrelated modules. Extract the syllabus topics in their exact serial order, and break down any broad syllabus headings into sequential 10-minute micro-topics.
    - MODE B (SHORT 1-LINE TOPIC PROVIDED): 
      Auto-generate a logical, step-by-step serial sequence of 10-minute micro-topics to teach that subject from the ground up.

    CRITICAL MICRO-TOPIC RULES:
    1. 10-MINUTE RULE: Every single item in "topics" MUST be a narrow, single-concept micro-topic that can be clearly explained in a 10-minute video (e.g., 'Pointer Arithmetic and Array Decay in C', NOT 'Pointers').
    2. STRICT SERIAL ORDER: Order micro-topics sequentially so each concept builds directly on the previous one.
    3. CLEAN TITLES: Do NOT include labels like 'Topic 1:', 'Unit 1:', or numbers in the title field.
    4. MODIFIERS: Extract any language/style preferences (e.g., 'in Hindi', 'practical code demo') into `search_modifier` and grading rules into `evaluation_modifier`.

    Return ONLY a valid JSON object matching this exact schema:
    {
        "course_title": "Clear Name of the Course",
        "topics": [
            {
                "title": "Exact single-concept micro-topic name",
                "core_concept": "What will be explained in this 10-minute micro-session",
                "prerequisite": "The immediate prior concept required, or 'None'",
                "search_query": "Targeted YouTube search query for this exact micro-topic"
            }
        ],
        "search_modifier": "Search keywords or empty string",
        "evaluation_modifier": "Evaluation criteria or empty string"
    }
    """
    
    # Properly combine image + custom text instructions so neither gets ignored
    if image_path and text:
        prompt = (
            f"Extract the exact topics serially from the attached syllabus image and convert them into "
            f"10-minute micro-topics. Also apply these user instructions/modifiers: {text}"
        )
    elif image_path:
        prompt = (
            "Strictly extract the topics in serial order from the attached syllabus image and break "
            "them into sequential 10-minute micro-topics. Do not invent outside topics."
        )
    elif text:
        prompt = f"Analyze this input (if it is a short topic, auto-generate serial micro-topics; if it is a syllabus, strictly extract and break down its topics):\n\n{text}"
    else:
        raise ValueError("You must provide either syllabus text or a syllabus image_path.")
    
    print("\n[AI - Meta Llama] Generating Granular Micro-Curriculum...")
    result = call_ai(system_prompt, prompt, image_path=image_path, require_json=True)
    
    # Parse only the top 3 sequential micro-topics
    if isinstance(result, dict) and isinstance(result.get("topics"), list):
        result["topics"] = result["topics"][:3]
        
    return result