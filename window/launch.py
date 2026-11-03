# 시계를 앱과 떼어 띄운다. 앱이 꺼져도 시계는 남고, 이미 떠 있으면 window.py가 스스로 끝난다
# 3초 안에 오류로 끝나면(재료 부족 따위) 실패로 알리고, 그 내용은 token-panel-start.log에 남긴다
import os
import subprocess
import sys

폴더 = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    # 파이썬 없이 도는 실행 파일판(token-clock.exe). 같은 파일이 --run으로 다시 불리면 시계 자체가 된다
    if "--run" in sys.argv:
        import window  # noqa: F401  창을 띄우고 닫힐 때까지 돈다
        sys.exit(0)
    명령 = [sys.executable, "--run"]
else:
    실행 = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(실행):
        실행 = sys.executable
    명령 = [실행, os.path.join(폴더, "window.py")]
기록폴더 = os.path.join(os.path.expanduser("~"), ".claude", "progress")
os.makedirs(기록폴더, exist_ok=True)
떼기 = 0x8 | 0x200  # DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP
for 깃발 in (떼기 | 0x01000000, 떼기):  # 0x01000000은 앱의 작업 묶음에서 빠져나오는 CREATE_BREAKAWAY_FROM_JOB
    try:
        with open(os.path.join(기록폴더, "token-panel-start.log"), "w", encoding="utf-8") as 기록:
            자식 = subprocess.Popen(명령, cwd=폴더, creationflags=깃발, close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=기록)
    except OSError:
        continue
    try:
        sys.exit(0 if 자식.wait(timeout=3) == 0 else 1)
    except subprocess.TimeoutExpired:
        sys.exit(0)  # 떠서 돌고 있다
sys.exit(1)
