from flask import Flask, request, jsonify, send_file
import os
from main import generate_full_course 
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, firestore
from functools import wraps

load_dotenv(override=True)

app = Flask(__name__)

# Initialize Firebase Admin & Firestore
cred = credentials.Certificate("firebase-credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def verify_firebase_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid token"}), 401
        token = auth_header.split('Bearer ')[1]
        try:
            decoded_token = auth.verify_id_token(token)
            request.user_id = decoded_token['uid'] 
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 401
    return decorated_function

@app.route('/')
def index():
    return send_file('index.html')

# 1. GENERATE AND SAVE NOTEBOOK (Enforces 3 notebook limit)
@app.route('/api/generate', methods=['POST'])
@verify_firebase_token
def generate_course():
    try:
        # Check existing notebook count for this user
        existing_docs = list(db.collection('notebooks').where('user_id', '==', request.user_id).stream())
        if len(existing_docs) >= 3:
            return jsonify({
                "error": "Notebook limit reached (Max 3). Please delete an existing notebook to create a new one."
            }), 400

        syllabus_text = request.form.get('syllabus_text')
        image_file = request.files.get('image')

        course_data = None
        if image_file and image_file.filename != '':
            temp_path = "temp_syllabus.jpg"
            image_file.save(temp_path)
            course_data = generate_full_course(syllabus_image=temp_path, max_topics=3)
            if os.path.exists(temp_path):
                os.remove(temp_path)
        elif syllabus_text and syllabus_text.strip() != '':
            course_data = generate_full_course(syllabus_text=syllabus_text, max_topics=3)
        else:
            return jsonify({"error": "Please provide text or an image."}), 400

        if course_data:
            doc_ref = db.collection('notebooks').document()
            course_data['id'] = doc_ref.id
            course_data['user_id'] = request.user_id
            doc_ref.set(course_data)
            return jsonify(course_data)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. GET USER NOTEBOOKS (Proper ID Injection)
@app.route('/api/notebooks', methods=['GET'])
@verify_firebase_token
def get_notebooks():
    try:
        docs = db.collection('notebooks').where('user_id', '==', request.user_id).stream()
        notebooks = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id  # Guarantee ID matches Firestore document ID
            notebooks.append(data)
        return jsonify(notebooks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. DELETE NOTEBOOK
@app.route('/api/notebooks/<notebook_id>', methods=['DELETE'])
@verify_firebase_token
def delete_notebook(notebook_id):
    try:
        doc_ref = db.collection('notebooks').document(notebook_id)
        doc = doc_ref.get()
        if not doc.exists:
            return jsonify({"error": "Notebook not found"}), 404
        if doc.to_dict().get('user_id') != request.user_id:
            return jsonify({"error": "Unauthorized"}), 403
            
        doc_ref.delete()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)