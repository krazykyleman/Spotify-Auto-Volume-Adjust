import threading
import time
import os
import webview
import spotify_auth  

from spotify_auto_volume import start_key_listener, run_flask, process_volume_adjustments
from spotify_auth import setup_database, app

# Global flag to signal when to start the listener
should_start_listener = False

class App:

    def __init__(self):
        setup_database()  # initializes database

    def run(self):
        # Start Flask server in a separate thread
        flask_thread = threading.Thread(target=self.run_flask)
        flask_thread.start()

        current_path = os.path.dirname(os.path.abspath(__file__))
        web_path = os.path.join(current_path, 'web')
        webview.create_window('Spotify Auto Volume Controller', 'http://127.0.0.1:8080/', width=800, height=600)

        # Polling loop to check if we should start the listener
        while True:
            time.sleep(1)  # Check every second
            if should_start_listener:
                print("Starting key listener from GUI loop")
                # Start volume queue in separate thread
                volume_thread = threading.Thread(target=process_volume_adjustments)
                volume_thread.start()

                # start key listener in separate thread
                key_listener_thread = threading.Thread(target=start_key_listener, daemon=True)
                key_listener_thread.start()
                break

    @staticmethod
    def run_flask():
        app.run(port=8080)

if __name__ == "__main__":
    app_instance = App()
    app_instance.run()
