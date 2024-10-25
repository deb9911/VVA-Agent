import os
import json
import requests
import webbrowser
import time
import platform
import psutil

FLASK_APP_URL = 'http://127.0.0.1:5000'  # VVA Dock Microservice URL
TOKEN_FILE = os.path.join(os.path.expanduser("~"), 'Vaani Virtual Assistant', 'user_token.json')


class VaaniAgent:
    def __init__(self):
        self.token = None
        self.load_token()

    def load_token(self):
        """Load the token from the local system if it exists."""
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as file:
                data = json.load(file)
                self.token = data.get('token')
                print(f"Token loaded: {self.token}")
        else:
            print("Token file not found. You need to log in via VVA Dock.")
            self.prompt_user_login()

    def prompt_user_login(self):
        """Prompt the user to log in via the VVA Dock microservice."""
        print(f"Please log in via: {FLASK_APP_URL}")
        webbrowser.open(FLASK_APP_URL + '/login')

        # Ask user to press Enter after they have logged in
        input("Press Enter once you have logged in through the VVA Dock and the token is generated.")

        # After pressing Enter, the token should be checked again
        self.load_token()
        if not self.token:
            print("Token not found after login. Please try logging in again.")
        else:
            print("Login successful! Token retrieved.")

    def validate_token(self):
        """Validate the token with the VVA Dock microservice."""
        if not self.token:
            print("No token found.")
            return False
        try:
            response = requests.post(f"{FLASK_APP_URL}/validate_token", json={"token": self.token})
            if response.status_code != 200:
                print(f"Error validating token: {response.status_code} {response.text}")
                return False

            response_data = response.json()
            if response_data.get("status") == "valid":
                print("Token validated successfully.")
                return True
            else:
                print(f"Token validation failed: {response_data.get('message')}")
                return False
        except requests.RequestException as e:
            print(f"Error validating token: {e}")
            return False
        except json.JSONDecodeError:
            print("Invalid JSON response from the server.")
            return False

    def execute_command(self, command):
        if command == 'start_app':
            self.start_application()
        elif command == 'read_log':
            self.read_log()
        # Add more command handling logic as necessary

    def poll_server(self):
        """Poll the server periodically for updates or commands."""
        while True:
            try:
                print("Polling the server for updates...")
                response = requests.get(f"{FLASK_APP_URL}/check_updates",
                                        headers={"Authorization": f"Bearer {self.token}"})
                if response.status_code == 200:
                    data = response.json().get('data')
                    if data != 'No updates':
                        print(f"Executing command: {data}")
                        self.execute_command(data)  # Function to handle execution of received commands
                else:
                    print("No updates or an issue with the request.")
            except requests.RequestException as e:
                print(f"Error polling server: {e}")
            time.sleep(10)  # Poll every 10 seconds

    def run(self):
        """Main logic to run the agent."""
        if self.token:
            if self.validate_token():
                print("Agent running with valid token.")
                self.poll_server()
            else:
                print("Invalid token. Please log in again.")
                self.prompt_user_login()
        else:
            self.prompt_user_login()

    def sync_system_info(self):
        """Sync local system information with VVA Dock."""
        system_info = {
            'os': platform.system(),
            'processor': platform.processor(),
            'ram': f"{psutil.virtual_memory().total / (1024 ** 3):.2f} GB"
        }
        try:
            response = requests.post(f"{FLASK_APP_URL}/sync_system_info",
                                     json=system_info,
                                     headers={"Authorization": f"Bearer {self.token}"})
            if response.status_code == 200:
                print("System info synced successfully.")
            else:
                print("Failed to sync system info.")
        except requests.RequestException as e:
            print(f"Error syncing system info: {e}")


if __name__ == "__main__":
    agent = VaaniAgent()
    agent.run()
