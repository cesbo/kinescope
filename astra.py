import subprocess
import requests
import json

class Astra:
    def __init__(self, port):
        self.process = None
        self.port = port

    def start(self):
        self.process = subprocess.Popen([
            '/usr/bin/astra',
            '-p', f'127.0.0.1:{self.port}',
            '--no-web-auth',
        ])

    def stop(self):
        if self.process:
            self.process.kill()

    def send_api_request(self, data):
        headers = {
            'Content-Type': 'application/json',
        }
        response = requests.post(
            f'http://127.0.0.1:{self.port}/control/',
            data=json.dumps(data),
            headers=headers,
        )
        if response.status_code == 200:
            try:
                return response.json()
            except json.decoder.JSONDecodeError:
                print("Failed to decode JSON")
        else:
            print("Request failed with status code:", response.status_code)
