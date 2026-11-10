import os
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# 1. Load environment variables
load_dotenv(override=True)
creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")

# 2. Check if credentials file exists
if not os.path.exists(creds_path):
    print(f"[Error] Firebase credentials file not found at: {creds_path}")
    print("Please make sure firebase-credentials.json is placed in this folder.")
    exit(1)

# 3. Initialize Firebase Admin SDK
cred = credentials.Certificate(creds_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

print("[Firebase] Successfully connected to FireDB (Firestore)!")

def store_course_file(file_path, user_id="local-developer"):
    """Reads a JSON course file and uploads it to FireDB under 'notebooks' collection."""
    if not os.path.exists(file_path):
        print(f"[-] File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        course_data = json.load(f)

    # Create a new document in the 'notebooks' collection
    doc_ref = db.collection("notebooks").document()
    course_data["id"] = doc_ref.id
    course_data["user_id"] = user_id

    # Store into Firestore
    doc_ref.set(course_data)
    print(f"[+] Successfully stored '{course_data.get('course_title', file_path)}' into FireDB!")
    print(f"    Document ID: {doc_ref.id}")

if __name__ == "__main__":
    # Upload Course_Content.json
    store_course_file("Course_Content.json")

    # Upload Data_Structures.json
    store_course_file("Data_Structures.json")