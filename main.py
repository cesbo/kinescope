import sys
import time
import signal
import uuid
from astra import Astra
from scan import Scan


ADAPTER = 30


class Instance:
    def __init__(self, astra: Astra, source: str, adapter_number: int):
        self.astra = astra
        self.source = source
        self.adapter_number = adapter_number
        self.id = str(uuid.uuid4())

        dvb_type, freq_symbolrate = source.split('/')

        self.adapter_config = {
            "id": self.id,
            "enable": True,
            "adapter": self.adapter_number,
            "device": 0,
            "budget": True,
        }

        if dvb_type == "dvbc":
            frequency, symbolrate = freq_symbolrate.split(':')
            self.name = f"adapter {frequency}"

            self.adapter_config["type"] = "C"
            self.adapter_config["name"] = self.name
            self.adapter_config["frequency"] = int(frequency)
            self.adapter_config["symbolrate"] = int(symbolrate)

        elif dvb_type == "dvbs":
            frequency, polarization, symbolrate = freq_symbolrate.split(':')
            self.name = f"adapter {frequency}"

            self.adapter_config["type"] = "S"
            self.adapter_config["name"] = self.name
            self.adapter_config["frequency"] = int(frequency)
            self.adapter_config["symbolrate"] = int(symbolrate)
            self.adapter_config["polarization"] = polarization

        elif dvb_type == "dvbs2":
            frequency, polarization, symbolrate = freq_symbolrate.split(':')
            self.name = f"adapter {frequency}"

            self.adapter_config["type"] = "S2"
            self.adapter_config["name"] = self.name
            self.adapter_config["frequency"] = int(frequency)
            self.adapter_config["symbolrate"] = int(symbolrate)
            self.adapter_config["polarization"] = polarization

    def scan(self):
        # Create adapter
        print(f"Creating adapter {self.source}...")
        self.astra.send_api_request({
            "cmd": "set-adapter",
            "id": self.id,
            "adapter": self.adapter_config
        })

        time.sleep(1)

        scan = Scan(self.astra)
        scan.start("dvb://" + self.id)
        print(f"Scanning {self.source}...")
        dvb_scan_data = scan.wait()
        scan.destroy()

        for i in dvb_scan_data:
            print(i)

        # To be implemented


class KineScope:
    def __init__(self, sources: str):
        self.astra = Astra(7999)
        self.instances = [Instance(self.astra, source, ADAPTER) for source in sources]

    def run(self):
        self.astra.start()
        time.sleep(2)  # Give Astra a moment to start up

        for instance in self.instances:
            instance.scan()

        self.astra.stop()


if __name__ == "__main__":
    sources = sys.argv[1:]
    kine_scope = KineScope(sources)

    def signal_handler(sig, frame):
        print('Ctrl+C pressed. Stopping Astra and exiting...')
        kine_scope.astra.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        kine_scope.run()
    except Exception as e:
        print(f"An exception occurred: {e}")
        kine_scope.astra.stop()
        sys.exit(1)
