import eel
import threading
import time
import webbrowser

from spotify_auto_volume import adjust_spotify_volume_with_token, start_key_listener, process_volume_queue
from spotify_auth import setup_database, app

# Initialize Eel
eel.init('web')


class App:

    def __init__(self):
        # You can add any initialization code here
        setup_database()  # initializes database

    @staticmethod
    @eel.expose
    def start_flask():
        threading.Thread(target=app.run, kwargs={'port': 8080}).start()
        time.sleep(1)  # give a small delay for the server to start up
        webbrowser.open("http://127.0.0.1:8080/")

    @staticmethod
    @eel.expose
    def start(volume):
        try:
            adjustment_value = int(volume) if volume else 10
            print("Starting the volume controller...")

            # Start the key listener in a separate thread
            threading.Thread(target=start_key_listener, daemon=True).start()

            # Start the queue processor in a separate thread
            threading.Thread(target=process_volume_queue, args=(adjustment_value,)).start()

        except ValueError:
            eel.show_error("Error", "Please enter a valid volume adjustment value!")  # JS function placeholder

    def run(self):
        eel.start('index.html', size=(600, 400), port=8080)


if __name__ == "__main__":
    app = App()
    app.run()
