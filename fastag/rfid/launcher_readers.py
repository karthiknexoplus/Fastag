import subprocess
import sys

procs = []
for module in ["fastag.rfid.rfid_reader1_service", "fastag.rfid.rfid_reader2_service"]:
    print(f"Starting {module} ...")
    procs.append(subprocess.Popen([sys.executable, "-m", module]))

try:
    for proc in procs:
        proc.wait()
except KeyboardInterrupt:
    print("Shutting down both readers...")
    for proc in procs:
        proc.terminate()
    for proc in procs:
        proc.wait() 