from astra import Astra
import time

class Scan:
    def __init__(self, astra: Astra):
        self.astra = astra
        self.scan_id = None
        self.tsid = -1
        self.scan_data = []
        self.psi_cache = []
        self.changed = False

    def get_scan_item(self, pnr):
        for x in self.scan_data:
            if x['pnr'] == pnr:
                return x
        x = {
            'pnr': pnr,
            'name': 'Unknown',
        }
        self.scan_data.append(x)
        self.scan_data.sort(key=lambda x: x['pnr'])
        return x

    def scan_check_psi(self, psi):
        if self.tsid == -1 and psi['psi'] != 'pat':
            self.psi_cache.append(psi)
        elif psi['psi'] in ['pat', 'nit', 'pmt', 'sdt']:
            getattr(self, f'scan_check_psi_{psi["psi"]}')(psi)

    def scan_check_psi_pat(self, pat):
        self.tsid = pat['tsid']
        for psi in self.psi_cache:
            self.scan_check_psi(psi)
        self.psi_cache = []
        self.changed = True

    def scan_check_psi_pmt(self, pmt):
        data = self.get_scan_item(pmt['pnr'])
        data['streams'] = []
        data['cas'] = []

        for d in pmt['descriptors']:
            if d['type_id'] == 9:
                data['cas'].append(hex(d['caid']))

        for x in pmt['streams']:
            if x['type_name'] not in ['VIDEO', 'AUDIO']:
                continue
            r = f"{x['type_name'][0]}PID:{x['pid']}"
            e = None
            l = None
            if x['type_id'] == 27:
                e = 'MPEG-4'
            for d in x['descriptors']:
                if d['type_id'] == 9:
                    data['cas'].append(hex(d['caid']))
                elif d['type_id'] == 10:
                    l = d['lang']
                elif d['type_id'] == 106:
                    e = 'AC-3'
            if e:
                r = f"{r} {e}"
            if l:
                r = f"{r} {l}"
            data['streams'].append(r)

        data['cas'].sort()
        data['cas'] = list(dict.fromkeys(data['cas']))  # remove duplicates
        self.changed = True

    def scan_check_psi_sdt(self, sdt):
        for x in sdt['services']:
            data = self.get_scan_item(x['sid'])
            for d in x['descriptors']:
                if d['type_id'] == 72:
                    data['name'] = d['service_name'] or 'Unknown'
                    data['provider'] = d['service_provider']
        self.changed = True

    def scan_check_psi_nit(self, nit):
        data = self.get_scan_item(0)
        for d in nit['descriptors']:
            if d['type_id'] == 64:
                data['name'] = d['network_name']

        for s in nit['streams']:
            if s['tsid'] != self.tsid:
                continue
            for d in s['descriptors']:
                if d['type_id'] == 67:
                    data['system'] = d
                    if d['s2']:
                        data['name'] = 'DVB-S2 : ' + data['name']
                    else:
                        data['name'] = 'DVB-S : ' + data['name']
                elif d['type_id'] == 68:
                    data['system'] = d
                    data['name'] = 'DVB-C : ' + data['name']
                elif d['type_id'] == 90:
                    data['system'] = d
                    data['name'] = 'DVB-T : ' + data['name']
        self.changed = True

    def scan_check(self):
        data = self.astra.send_api_request({
            "cmd": "scan-check",
            "id": self.scan_id
        })

        if 'scan' in data:
            for psi in data['scan']:
                self.scan_check_psi(psi)

    def destroy(self):
        if self.scan_id:
            self.astra.send_api_request({
                "cmd": "scan-kill",
                "id": self.scan_id
            })
            self.scan_id = None

    def start(self, source: str):
        data = self.astra.send_api_request({
            "cmd": "scan-init",
            "scan": source,
        })

        self.scan_id = data['id']

    def wait(self):
        for _ in range(5):
            time.sleep(2)
            self.scan_check()
            if not self.changed:
                break
            self.changed = False

        return self.scan_data
