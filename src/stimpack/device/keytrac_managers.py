import subprocess
import signal

from stimpack.device.loco_managers import LocoManager, LocoClosedLoopManager

KEYTRAC_HOST = '127.0.0.1'  # The server's hostname or IP address
KEYTRAC_PORT = 33335         # The port used by the server
# PYTHON_BIN =   '/home/mc/venv/stimpack/bin/python'
# KEYTRAC_PY =   '/home/mc/src/stimpack/src/stimpack/device/keytrac.py'
PYTHON_BIN =   'python'
KEYTRAC_PY =   'keytrac.py'

class KeytracManager(LocoManager):
    def __init__(self, python_bin=PYTHON_BIN, kt_py_fn=KEYTRAC_PY, start_at_init=True):
        self.python_bin = python_bin
        self.kt_py_fn = kt_py_fn
        self.keytrac_host = KEYTRAC_HOST
        self.keytrac_port = KEYTRAC_PORT

        self.started = False
        self.p = None

        if start_at_init:
            self.start()

    def start(self):
        if self.started:
            print("Keytrac is already running.")
        else:
            self.p = subprocess.Popen([self.python_bin, self.kt_py_fn, self.keytrac_host, str(self.keytrac_port)], start_new_session=True)
            self.started = True

    def close(self, timeout=5):
        if self.started:
            self.p.send_signal(signal.SIGINT)
            
            try:
                self.p.wait(timeout=timeout)
            except:
                print("Timeout expired for closing Keytrac. Killing process...")
                self.p.kill()
                self.p.terminate()

            self.p = None
            self.started = False
        else:
            print("Keytrac hasn't been started yet. Cannot be closed.")

class KeytracClosedLoopManager(LocoClosedLoopManager):
    def __init__(self, fs_manager, host=KEYTRAC_HOST, port=KEYTRAC_PORT, python_bin=PYTHON_BIN, kt_py_fn=KEYTRAC_PY, start_at_init=False, udp=True):
        super().__init__(fs_manager=fs_manager, host=host, port=port, save_directory=None, start_at_init=False, udp=udp)
        self.kt_manager = KeytracManager(python_bin=python_bin, kt_py_fn=kt_py_fn, start_at_init=False)

        if start_at_init:    self.start()

    def start(self):
        super().start()
        self.kt_manager.start()

    def close(self):
        super().close()
        self.kt_manager.close()

    def _parse_line(self, line):
        toks = line.split(", ")

        # Keytrac lines always starts with KT
        if toks.pop(0) != "KT":
            print('Bad read')
            return None
        
        key_count = int(toks[0])
        key_pressed = toks[1]
        x = float(toks[2])
        y = float(toks[3])
        z = float(toks[4])
        theta = float(toks[5])
        ts = float(toks[6])

        return {'theta': theta, 'x': x, 'y': y, 'z':z, 'frame_num': key_count, 'ts': ts}
