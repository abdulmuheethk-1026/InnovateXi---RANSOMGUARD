import psutil

APP_NAME = "RansomGuard.exe"

found = False

for process in psutil.process_iter(['pid', 'name']):
    try:
        if process.info['name'] and APP_NAME in process.info['name']:
            print(f"Stopping {APP_NAME} (PID {process.pid})")
            process.kill()
            found = True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

if found:
    print("RansomGuard stopped successfully.")
else:
    print("RansomGuard is not running.")