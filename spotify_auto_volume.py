import time
import datetime
import requests
import threading
import queue
import atexit

from pynput import keyboard
from apscheduler.schedulers.background import BackgroundScheduler


#globals

last_adjustment_time = 0
adjustment_lock = threading.Lock()

volume_adjustments = []
click_timestamps = []

task_queue = queue.Queue()

adjustment_value = 10  # default value

BASE_URL = "https://spotifyautovolume-efd5d02c1318.herokuapp.com/"

def adjust_volume_hourly():
    print("Hourly volume check and adjustment")

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(adjust_volume_hourly, trigger="interval", hours=1, next_run_time=datetime.datetime.now() + datetime.timedelta(hours=1))
scheduler.start()
atexit.register(scheduler.shutdown)



global cached_token, token_expiry
cached_token = None
token_expiry = None


def get_latest_access_token():
    global cached_token, token_expiry
    if cached_token and token_expiry and time.time() < token_expiry:
        return cached_token
    
    response = requests.get(f"{BASE_URL}/get_tokens")
    if response.status_code != 200:
        return None
    tokens = response.json()
    cached_token = tokens['access_token']
    token_expiry = time.time() + 3500  # setting expiry 100 seconds before the actual 1-hour expiry
    return tokens['access_token']


# Function to adjust Spotify volume
def adjust_spotify_volume_with_token(direction, adjustment, tokens, retries=3):

    if not tokens['access_token']:
        return

    headers = {
        "Authorization": f"Bearer {tokens['access_token']}"
    }
    
    response = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
    
    if not response.content:
        print("No content in the response")
        return

    if response.status_code != 200:

        if 'The access token expired' in response.text or 'Permissions missing' in response.text:

            # Request the server to refresh the token
            response_refresh = requests.get(f"{BASE_URL}/refresh_token")

            if response_refresh.status_code != 200:

                print(f"Error refreshing token via server: {response_refresh.text}")
                return
            
            tokens['access_token'] = response_refresh.json().get('access_token')

            if not tokens['access_token']:
                
                print("Failed to get refreshed access token.")
                return
            
            headers = {
                "Authorization": f"Bearer {tokens['access_token']}"
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

    print(f"API response for volume adjustment: {response.status_code}, {response.text}")

    if response.status_code == 429:  # Spotify's rate-limiting code
        if retries > 0:
            wait_time = int(response.headers.get('Retry-After', 1))  # get the wait time, default to 1 second if not provided
            print(f"Rate limited by Spotify. Waiting for {wait_time} seconds.")
            time.sleep(wait_time)
            adjust_spotify_volume_with_token(direction, adjustment, tokens, retries-1)  # retry
        else:
            print("Max retries reached. Abandoning volume adjustment.")
    elif response.status_code == 204:
        print(f"Spotify volume adjusted to {new_volume}%")
    else:
        print(f"Error adjusting Spotify volume: {response.text}")

volume_queue = queue.Queue()

def process_volume_adjustments(custom_adjustment=None):
    global adjustment_value, cached_token, token_expiry
    if custom_adjustment:
        try:
            adjustment_value = int(custom_adjustment)
        except ValueError:
            print('Invalid custom adjustment value provided.')
    
    # Fetch tokens from the server.
    response = requests.get(f"{BASE_URL}/get_tokens")
    tokens = response.json()

    while True:
        if not task_queue.empty():
            task = task_queue.get()
            direction, adjustment, tokens = task
            adjust_spotify_volume_with_token(direction, adjustment, tokens)
            time.sleep(2)  # Add a delay of 2 seconds between adjustments


last_adjustment_time = 0
right_ctrl_pressed = False


volume_event = threading.Event()

def volume_task_processor():
    print("Entered volume_task_processor.")

    while True:
        print("Waiting for volume_event to be set.")
        volume_event.wait()  # Wait for an event to be set
        print("volume_event detected. Processing tasks.")
        task = task_queue.get()
        print(f"Processing task: {task}")
        if task:
            direction, adjustment, tokens = task
            adjust_spotify_volume_with_token(direction, adjustment, tokens)
            task_queue.task_done()
        volume_event.clear()  # Clear the event

def on_press(key):
    global right_ctrl_pressed

    # Check if the key is one of the relevant keys
    if key not in [keyboard.Key.ctrl_r, keyboard.Key.up, keyboard.Key.down]:
        return

    if key == keyboard.Key.ctrl_r:
        right_ctrl_pressed = True

    tokens = {"access_token": get_latest_access_token()}
    print(f"Fetched token: {tokens['access_token']}")

    if right_ctrl_pressed and key == keyboard.Key.up:
        print("Detected right control + up arrow key press.")
        task_queue.put(('up', adjustment_value, tokens))
        volume_event.set()

    elif right_ctrl_pressed and key == keyboard.Key.down:
        print("Detected right control + down arrow key press.")
        task_queue.put(('down', adjustment_value, tokens))
        volume_event.set()


def on_release(key):
    global right_ctrl_pressed

    if key == keyboard.Key.ctrl_r:
        right_ctrl_pressed = False


def start_key_listener():
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    listener.join()

if __name__ == "__main__":
    # Start volume task processor in a separate thread
   # volume_task_processor_thread = threading.Thread(target=volume_task_processor, daemon=True)
   # volume_task_processor_thread.start()
    
    # Start volume queue in separate thread
    volume_thread = threading.Thread(target=process_volume_adjustments)
    volume_thread.start()

    # Start key listener in separate thread
    key_listener_thread = threading.Thread(target=start_key_listener, daemon=True)
    key_listener_thread.start()

    # Directly call the volume_task_processor
    volume_task_processor()

    # Keep the main thread running
    while True:
        time.sleep(10)
