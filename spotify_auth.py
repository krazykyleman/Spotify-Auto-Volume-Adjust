from flask import Flask, request, redirect, jsonify
from database_manager import setup_database, store_tokens, fetch_tokens
from apscheduler.schedulers.background import BackgroundScheduler

import requests
import atexit
import os


app = Flask('spotify_auth')

CLIENT_ID = os.environ.get('CLIENT_ID')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

def auto_refresh_token():
    refresh_access_token()

@app.route('/refresh_token', methods=['GET'])
def handle_refresh_token():
    refresh_access_token()
    tokens = fetch_tokens()
    if tokens:
        return jsonify({'access_token': tokens['access_token']})
    else:
        return jsonify({'error': 'Failed to refresh access token'}), 400

@app.route('/get_tokens', methods=['GET'])
def get_tokens():
    tokens = fetch_tokens()
    return jsonify(tokens)

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(auto_refresh_token, trigger="interval", seconds=3400)  # Refresh every 56 minutes (just under an hour)
scheduler.start()

@app.route('/authorize')
def authorize():
    auth_url = f"https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=user-modify-playback-state"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Error: Code not found in the callback!"
    
    token_url = "https://accounts.spotify.com/api/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(token_url, data=token_data)
    
    if response.status_code != 200:
        return f"Error: Received status code {response.status_code} from Spotify."

    token_response_data = response.json()
    
    access_token = token_response_data.get("access_token")
    refresh_token = token_response_data.get("refresh_token")

    # Store the tokens in the SQLite database
    store_tokens(access_token, refresh_token)

    return redirect('/success')

@app.route('/success')
def success():
    return """<html><body><script>
            setTimeout(function() { window.close(); }, 3000);
            </script>Authorization successful! This window will close in 3 seconds.</body></html>"""

@app.route('/')
def index():
    return "Server running. Volume adjusting in the background."

@app.route('/start', methods=['POST'])
def start_volume_adjustment():
    data = request.json
    volume = data.get('volume')
    
    # Get the access token from the database
    tokens = fetch_tokens()
    if not tokens:
        return jsonify({"success": False, "message": "Failed to fetch access token."})
    
    access_token = tokens['access_token']
    
    # Spotify API endpoint to adjust volume
    endpoint = f"https://api.spotify.com/v1/me/player/volume?volume_percent={volume}"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.put(endpoint, headers=headers)
    
    if response.status_code == 204:  # 204 No Content means the request was successful
        return jsonify({"success": True, "message": "Volume adjusted successfully."})
    else:
        return jsonify({"success": False, "message": f"Failed to adjust volume. Status code: {response.status_code}"})


def refresh_access_token():
    tokens = fetch_tokens()
    if not tokens:
        return None

    token_url = "https://accounts.spotify.com/api/token"
    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": tokens['refresh_token'],
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(token_url, data=token_data)
    token_response_data = response.json()
    
    # Update the access token in the SQLite database
    store_tokens(token_response_data.get("access_token"), tokens['refresh_token'])

    return token_response_data.get("access_token")


atexit.register(scheduler.shutdown)

if __name__ == '__main__':
    setup_database()
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080), debug=False)