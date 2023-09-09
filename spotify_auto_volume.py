import pygetwindow as gw
import time
import datetime
import requests
import threading
import queue

from pynput import keyboard
from spotify_auth import fetch_tokens, refresh_access_token
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)


def adjust_volume_hourly():
    print("Hourly volume check and adjustment")

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(adjust_volume_hourly, trigger="interval", hours=1, next_run_time=datetime.datetime.now() + datetime.timedelta(hours=1))
scheduler.start()


@app.route('/')
def index():
    return "Server running. Volume adjusting in the background."


# Function to get the latest access token
def get_latest_access_token():
    tokens = fetch_tokens()
    if not tokens:
        print("No tokens found in the database!")
        return None
    return tokens['access_token']


# Function to adjust Spotify volume
def adjust_spotify_volume_with_token(direction, adjustment):
    
    access_token = get_latest_access_token()
    if not access_token:
        return

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
    
    if not response.content:
        print("No content in the response")
        return

    if response.status_code != 200:
        if 'The access token expired' in response.text or 'Permissions missing' in response.text:
            refresh_access_token()
            access_token = get_latest_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            response = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
            if response.status_code != 200:
                print(f"Error after refreshing token: {response.text}")
                return
        else:
            print(f"Error getting current volume: {response.text}")
            return
    
    try:
        current_volume = response.json().get('device', {}).get('volume_percent', 50)

    except requests.exceptions.JSONDecodeError:
        
        print(f"Error decoding JSON. Response content: {response.content}")
        return
    
    if direction == 'up':
        new_volume = min(current_volume + adjustment, 100)
    elif direction == 'down':
        new_volume = max(current_volume - adjustment, 0)

    response = requests.put(f"https://api.spotify.com/v1/me/player/volume?volume_percent={new_volume}", headers=headers)

    if response.status_code == 429:  # Spotify's rate-limiting code
        print("Rate limited by Spotify. Please wait a bit before adjusting the volume again.")
    elif response.status_code == 204:
     print(f"Spotify volume adjusted to {new_volume}%")
    else:
        print(f"Error adjusting Spotify volume: {response.text}")


def run_flask():

    app.run(use_reloader=False)


volume_queue = queue.Queue()

def process_volume_queue(adjustment_value):
    while True:
        direction = volume_queue.get()
        print(f"Processing volume direction: {direction}")

        if direction == "up":
            adjust_spotify_volume_with_token('up', adjustment_value)
        elif direction == "down":
            adjust_spotify_volume_with_token('down', adjustment_value)
        volume_queue.task_done()



last_adjustment_time = 0
right_ctrl_pressed = False

def on_press(key):

    global right_ctrl_pressed, last_adjustment_time

    if key == keyboard.Key.ctrl_r:
        right_ctrl_pressed = True

    if time.time() - last_adjustment_time < 0.5:
        return

    if right_ctrl_pressed and key == keyboard.Key.up:
        volume_queue.put('up')
        last_adjustment_time = time.time()

    if right_ctrl_pressed and key == keyboard.Key.down:
        volume_queue.put('down')
        last_adjustment_time = time.time()


def on_release(key):

    global right_ctrl_pressed, last_adjustment_time

    if key == keyboard.Key.ctrl_r:
        right_ctrl_pressed = False

    last_adjustment_time = 0


def start_key_listener():

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
        
    # starts flask on a separate thread.
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # start volume queue in separate thread
    volume_thread = threading.Thread(target=process_volume_queue)
    volume_thread.start()

    # start key listener in separate thread
    key_listener_thread = threading.Thread(target=start_key_listener, daemon=True)
    key_listener_thread.start()