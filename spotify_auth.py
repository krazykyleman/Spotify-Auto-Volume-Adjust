from flask import Flask, request, redirect
from database_manager import setup_database, store_tokens, fetch_tokens
from apscheduler.schedulers.background import BackgroundScheduler

import webbrowser
import threading
import requests
import sqlite3


app = Flask(__name__)

CLIENT_ID = '11f1598b050346ed8bd490975b11c9f5'
REDIRECT_URI = 'http://localhost:8080/callback'
CLIENT_SECRET = 'c40a1001f76b486792d89b1dde6da902'

def auto_refresh_token():
    print("Refreshing access token...")
    refresh_access_token()

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(auto_refresh_token, trigger="interval", seconds=3400)  # Refresh every 56 minutes (just under an hour)
scheduler.start()

@app.route('/')
def index():
    print("Index route triggered!")
    auth_url = f"https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=user-modify-playback-state"
    webbrowser.open_new_tab(auth_url)  # directly open the Spotify authorization URL here
    return "Redirecting to Spotify for authorization..."



@app.route('/callback')
def callback():

    print("Callback route triggered!")

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
    token_response_data = response.json()
    
    access_token = token_response_data.get("access_token")
    refresh_token = token_response_data.get("refresh_token")

    # Store the tokens in the SQLite database
    store_tokens(access_token, refresh_token)

    return redirect('/success')

@app.route('/success')
def success():

    print("Success route triggered!")

    return """<html><body><script>
              setTimeout(function() { window.close(); }, 3000);
              </script>Authorization successful! This window will close in 3 seconds.</body></html>"""


def refresh_access_token():
    tokens = fetch_tokens()
    if not tokens:
        return

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


if __name__ == '__main__':
    # Setup the SQLite database before the app starts
    setup_database()
    #threading.Timer(1, lambda: webbrowser.open("http://127.0.0.1:8080/") ).start()
    app.run(port=8080)
