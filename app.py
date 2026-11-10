from flask import Flask, request, jsonify, send_file
import os
import json
import uuid
import threading
from functools import wraps
from dotenv import load_dotenv
from main import generate_full_course

# Load environment variables
load_dotenv(override=True)

app = Flask(__name__, static_folder='static', static_url_path='/static')

# ===================================================
# FIREBASE & DATA PERSISTENCE INITIALIZATION
# ===================================================
FIREBASE_ENABLED = False
db = None
auth = None

firebase_creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")

try:
    import firebase_admin
    from firebase_admin import credentials, auth as fb_auth, firestore as fb_firestore

    firebase_creds_raw = os.getenv("FIREBASE_CREDENTIALS_RAW")
    if firebase_creds_raw:
        cred_dict = json.loads(firebase_creds_raw)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        db = fb_firestore.client()
        auth = fb_auth
        FIREBASE_ENABLED = True
        print("[Firebase] Initialized successfully from FIREBASE_CREDENTIALS_RAW environment variable.")
    elif os.path.exists(firebase_creds_path):
        cred = credentials.Certificate(firebase_creds_path)
        firebase_admin.initialize_app(cred)
        db = fb_firestore.client()
        auth = fb_auth
        FIREBASE_ENABLED = True
        print(f"[Firebase] Initialized successfully with credentials: {firebase_creds_path}")
    else:
        print(f"[Firebase] Notice: Credentials file '{firebase_creds_path}' not found.")
        print("[Persistence] Falling back to local workspace JSON database for notebooks.")
except ImportError:
    print("[Firebase] Notice: 'firebase_admin' package not installed in environment.")
    print("[Persistence] Using local workspace JSON storage for notebooks.")
except Exception as e:
    print(f"[Firebase] Notice: Firebase initialization bypassed ({e}).")
    print("[Persistence] Using local workspace JSON storage for notebooks.")

# Local storage fallback directory, file & thread-lock
LOCAL_DATA_FILE = os.path.join(os.path.dirname(__file__), "local_notebooks.json")
local_db_lock = threading.Lock()

def load_local_notebooks():
    with local_db_lock:
        if os.path.exists(LOCAL_DATA_FILE):
            try:
                with open(LOCAL_DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

def save_local_notebooks(notebooks):
    with local_db_lock:
        with open(LOCAL_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(notebooks, f, indent=2)

# ===================================================
# AUTHENTICATION MIDDLEWARE
# ===================================================
def verify_firebase_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            # If Firebase is not enabled, default to local demo user
            if not FIREBASE_ENABLED:
                request.user_id = "local-developer"
                return f(*args, **kwargs)
            return jsonify({"error": "Missing or invalid authorization header (Bearer token required)."}), 401

        token = auth_header.split('Bearer ')[1].strip()

        if FIREBASE_ENABLED and auth:
            try:
                decoded_token = auth.verify_id_token(token)
                request.user_id = decoded_token['uid']
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({"error": f"Invalid or expired Firebase token: {str(e)}"}), 401
        else:
            # Fallback for development without live Firebase project
            request.user_id = token if (token and token != "demo-token") else "local-developer"
            return f(*args, **kwargs)

    return decorated_function

# ===================================================
# STATIC & FRONTEND ROUTING
# ===================================================
@app.route('/')
def index():
    return send_file('static/index.html')

# Telemetry status endpoint
@app.route('/api/status', methods=['GET'])
def get_system_status():
    meta_key = os.getenv("META_API_KEY") or os.getenv("MODEL_API_KEY") or os.getenv("LLAMA_API_KEY")
    rapid_key = os.getenv("RAPIDAPI_KEY")
    yt_key = os.getenv("YOUTUBE_API_KEY")

    def is_configured(k):
        if not k or "your_" in k or len(k.strip()) < 8:
            return False
        return True

    return jsonify({
        "status": "online",
        "llm_provider": "Meta Llama API",
        "meta_model": os.getenv("META_MODEL", "llama-3.3-70b-instruct"),
        "meta_api_configured": is_configured(meta_key),
        "rapidapi_configured": is_configured(rapid_key),
        "youtube_api_configured": is_configured(yt_key),
        "firebase_enabled": FIREBASE_ENABLED,
        "storage_mode": "Firestore Cloud" if FIREBASE_ENABLED else "Local Workspace Storage"
    })


import time

@app.route('/api/test-slow', methods=['GET'])
def test_slow_endpoint():
    """Simulates a 3-second wait for Meta AI / YouTube API"""
    req_id = request.args.get('id', '1')
    print(f"[Thread Worker] Request {req_id} received. Simulating 3-second API wait...")
    time.sleep(3)
    print(f"[Thread Worker] Request {req_id} API response received!")
    return jsonify({"message": f"Request {req_id} finished after 3s API wait"})
# ===================================================
# 1. GENERATE AND SAVE NOTEBOOK (Enforces 3 notebook limit)
# ===================================================
@app.route('/api/generate', methods=['POST'])
@verify_firebase_token
def generate_course():
    try:


        if not request.user_id or request.user_id in ["local-developer", "demo-token", "guest-user-1"]:
            return jsonify({
                "error": "Authentication required. Please sign in to compile and save notebooks."
            }), 401
        # Check existing notebook count for this user
        if FIREBASE_ENABLED:
            existing_docs = list(db.collection('notebooks').where('user_id', '==', request.user_id).stream())
            if len(existing_docs) >= 3:
                return jsonify({
                    "error": "Notebook limit reached (Max 3). Please delete an existing notebook to create a new one."
                }), 400
        else:
            all_nbs = load_local_notebooks()
            user_nbs = [n for n in all_nbs if n.get('user_id') == request.user_id]
            if len(user_nbs) >= 3:
                return jsonify({
                    "error": "Notebook limit reached (Max 3). Please delete an existing notebook to create a new one."
                }), 400

        syllabus_text = request.form.get('syllabus_text')
        image_file = request.files.get('image')

        course_data = None
        if image_file and image_file.filename != '':
            temp_filename = f"temp_syllabus_{uuid.uuid4().hex[:8]}.jpg"
            temp_path = os.path.join(os.path.dirname(__file__), temp_filename)
            image_file.save(temp_path)
            try:
                course_data = generate_full_course(syllabus_image=temp_path, max_topics=3)
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
        elif syllabus_text and syllabus_text.strip() != '':
            course_data = generate_full_course(syllabus_text=syllabus_text, max_topics=3)
        else:
            return jsonify({"error": "Please provide syllabus text or upload an image."}), 400

        if not course_data or not course_data.get("modules"):
            return jsonify({
                "error": "Course generation produced no modules. Please verify your Meta API and YouTube keys in .env."
            }), 500

        # Save to database
        if FIREBASE_ENABLED:
            doc_ref = db.collection('notebooks').document()
            course_data['id'] = doc_ref.id
            course_data['user_id'] = request.user_id
            doc_ref.set(course_data)
        else:
            course_id = str(uuid.uuid4())[:8]
            course_data['id'] = course_id
            course_data['user_id'] = request.user_id
            all_nbs = load_local_notebooks()
            all_nbs.append(course_data)
            save_local_notebooks(all_nbs)

        return jsonify(course_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===================================================
# 2. GET USER NOTEBOOKS
# ===================================================
@app.route('/api/notebooks', methods=['GET'])
@verify_firebase_token
def get_notebooks():
    try:
        if FIREBASE_ENABLED:
            docs = db.collection('notebooks').where('user_id', '==', request.user_id).stream()
            notebooks = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                notebooks.append(data)
            return jsonify(notebooks)
        else:
            all_nbs = load_local_notebooks()
            user_nbs = [n for n in all_nbs if n.get('user_id') == request.user_id]
            return jsonify(user_nbs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===================================================
# 3. DELETE NOTEBOOK
# ===================================================
@app.route('/api/notebooks/<notebook_id>', methods=['DELETE'])
@verify_firebase_token
def delete_notebook(notebook_id):
    try:
        if FIREBASE_ENABLED:
            doc_ref = db.collection('notebooks').document(notebook_id)
            doc = doc_ref.get()
            if not doc.exists:
                return jsonify({"error": "Notebook not found"}), 404
            if doc.to_dict().get('user_id') != request.user_id:
                return jsonify({"error": "Unauthorized"}), 403

            doc_ref.delete()
            return jsonify({"success": True})
        else:
            all_nbs = load_local_notebooks()
            found = False
            updated = []
            for nb in all_nbs:
                if nb.get('id') == notebook_id:
                    if nb.get('user_id') != request.user_id:
                        return jsonify({"error": "Unauthorized"}), 403
                    found = True
                else:
                    updated.append(nb)
            if not found:
                return jsonify({"error": "Notebook not found"}), 404
            save_local_notebooks(updated)
            return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"\n[+] Helioz AI Course Studio running on http://127.0.0.1:{port}")
    
    # Check if high-concurrency WSGI server (Waitress) is available
    try:
        from waitress import serve
        threads = int(os.getenv("SERVER_THREADS", 16))
        print(f"[*] Multi-threaded Waitress WSGI server active with {threads} worker threads.")
        print(f"[*] Concurrent requests will be handled in parallel across threads.\n")
        serve(app, host='0.0.0.0', port=port, threads=threads)
    except ImportError:
        print(f"[*] Running Flask multi-threaded server (threaded=True).")
        print(f"[*] (For production high-load concurrency, run: pip install waitress)\n")
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
