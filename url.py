from flask import Flask, request, redirect, jsonify
from flask_cors import CORS
import hashlib
import os
import re
from datetime import datetime
from urllib.parse import urlparse
from firebase_admin import credentials, initialize_app, db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Firebase
cred = credentials.Certificate("../url-shortener-65429-firebase-adminsdk-fbsvc-94d8d312c4.json")
firebase_app = initialize_app(cred, {
    'databaseURL': os.getenv("FIREBASE_DATABASE_URL")
})

# Get reference to the database
db_ref = db.reference('urls')
recent_urls_ref = db.reference('recent_urls')

app = Flask(__name__)
CORS(app)

def is_valid_url(url):
    """Check if the URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def sanitize_url(url):
    """Sanitize the URL by adding https:// if missing."""
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    return url

def generate_short_code(long_url, length=6):
    """Generate a short code for the URL."""
    # Use a simpler approach for faster generation
    hash_object = hashlib.md5(long_url.encode())
    return hash_object.hexdigest()[:length]

@app.route("/shorten", methods=["POST"])
def shorten():
    try:
        data = request.json
        long_url = data.get("long_url")
        user_id = data.get("user_id")
        
        if not long_url:
            return jsonify({"error": "Missing URL"}), 400
            
        if not user_id:
            return jsonify({"error": "Missing user ID"}), 400

        # Sanitize and validate URL
        long_url = sanitize_url(long_url)
        if not is_valid_url(long_url):
            return jsonify({"error": "Invalid URL format"}), 400

        # Generate short code
        short_url = generate_short_code(long_url)

        # Check if URL already exists
        existing_entry = db_ref.child(short_url).get()
        if existing_entry:
            return jsonify({
                "short_url": request.host_url + short_url,
                "message": "URL already shortened"
            })

        # Store URL data
        url_data = {
            "long_url": long_url,
            "created_at": datetime.now().isoformat(),
            "clicks": 0,
            "user_id": user_id
        }
        db_ref.child(short_url).set(url_data)

        # Add to user's recent URLs
        user_recent_urls_ref = recent_urls_ref.child(user_id)
        recent_url_data = {
            "long_url": long_url,
            "short_url": request.host_url + short_url,
            "timestamp": datetime.now().timestamp()
        }
        
        # Use push to add to the end of the list
        user_recent_urls_ref.push(recent_url_data)
        
        # Limit to 10 entries (simplified)
        user_recent_urls = user_recent_urls_ref.get()
        if user_recent_urls and len(user_recent_urls) > 10:
            # Get all keys
            keys = list(user_recent_urls.keys())
            # Sort by timestamp (newest first)
            keys.sort(key=lambda k: user_recent_urls[k].get('timestamp', 0), reverse=True)
            # Keep only the 10 most recent
            keys_to_keep = keys[:10]
            # Delete all entries
            user_recent_urls_ref.delete()
            # Add back only the ones we want to keep
            for key in keys_to_keep:
                user_recent_urls_ref.push(user_recent_urls[key])
        
        return jsonify({
            "short_url": request.host_url + short_url,
            "message": "URL shortened successfully"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/<short_url>", methods=["GET"])
def redirect_to_url(short_url):
    try:
        entry = db_ref.child(short_url).get()
        
        if not entry:
            return jsonify({"error": "URL not found"}), 404

        # Increment click counter
        db_ref.child(short_url).update({
            "clicks": entry.get("clicks", 0) + 1,
            "last_clicked": datetime.now().isoformat()
        })

        return redirect(entry["long_url"])

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/stats/<short_url>", methods=["GET"])
def get_stats(short_url):
    try:
        entry = db_ref.child(short_url).get()
        
        if not entry:
            return jsonify({"error": "URL not found"}), 404

        return jsonify({
            "short_url": request.host_url + short_url,
            "long_url": entry["long_url"],
            "clicks": entry.get("clicks", 0),
            "created_at": entry.get("created_at"),
            "last_clicked": entry.get("last_clicked")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/recent/<user_id>", methods=["GET"])
def get_recent_urls(user_id):
    try:
        user_recent_urls = recent_urls_ref.child(user_id).get()
        if not user_recent_urls:
            return jsonify({"recent_urls": []})
        
        # Convert to list and sort by timestamp
        urls_list = []
        for key, value in user_recent_urls.items():
            value['id'] = key
            urls_list.append(value)
        
        # Sort by timestamp (newest first)
        urls_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return jsonify({"recent_urls": urls_list})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve the static HTML file
@app.route("/")
def index():
    return app.send_static_file('indexer.html')

if __name__ == "__main__":
    # In production, use the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
