import subprocess
import webbrowser
import threading
import time
import os

# Step 1: Vite (Vue) 빌드
print("📦 Vue 빌드 중...\n")
subprocess.run("npm run build", shell=True)

# Step 2: FastAPI 서버 실행 (서브 프로세스로)
def start_fastapi():
    os.system("uvicorn app:app --host 0.0.0.0 --port 8000")

threading.Thread(target=start_fastapi).start()

# Step 3: 서버가 뜰 시간을 잠깐 기다린 후 자동으로 브라우저 열기
time.sleep(2)
webbrowser.open("http://localhost:8000")
