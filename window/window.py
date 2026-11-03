# 시계 모양 토큰 계기판 창. 모드가 적은 파일을 읽어 띄운다. 네모 없이 시계 모양만 보이고, 투명한 곳의 클릭은 바탕화면으로 지나간다.
# 동작 규칙은 gauge.py, 그림은 dial.py에 있다. 여기서는 창과 파일과 마우스만 다룬다.
import ctypes
import datetime
import json
import os
import sys
import threading
import traceback
import time
import math
import tkinter as tk
from ctypes import wintypes

# 이미 시계가 떠 있으면 무거운 재료를 읽기 전에 끝난다. 막 꺼지는 시계는 잠깐 기다린다. 사용자 폴더마다 하나씩이라 시험은 임시 폴더로 따로 돈다
이름표 = "token-panel-clock-" + os.path.normcase(os.path.abspath(os.path.expanduser("~"))).replace(chr(92), "/").replace("/", "-").replace(":", "")
커널 = ctypes.WinDLL("kernel32", use_last_error=True); 커널.CreateMutexW.restype = ctypes.c_void_p; 커널.CloseHandle.argtypes = [ctypes.c_void_p]
for 차례 in range(10):
    ctypes.set_last_error(0); 자물쇠 = 커널.CreateMutexW(None, False, 이름표)
    if ctypes.get_last_error() != 183 or os.environ.get("TOKEN_PANEL_TEST"):
        break
    커널.CloseHandle(자물쇠); time.sleep(.2)
else:
    sys.exit(0)

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")  # 큰 계산이 없다. 스레드마다 잡는 메모리를 아낀다
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dial
from PIL import Image, ImageChops

import chrono_dial
from chrono import 크로노
from dial import H, W, 위, 그림
from gauge import 계기, 잘라
from morph import 변신

파일 = os.path.expanduser(r"~\.claude\progress\token-panel.json")
명령파일 = os.path.expanduser(r"~\.claude\progress\token-panel-cmd.json")
자리파일 = os.path.expanduser(r"~\.claude\progress\token-panel-pos.json")
켜짐파일 = os.path.expanduser(r"~\.claude\progress\token-panel-clock.json")
u, g = ctypes.windll.user32, ctypes.windll.gdi32
정밀 = [False]


def 정밀타이머(켬):
    # 기본 타이머는 15.6밀리초 단위라 움직임이 끊긴다. 움직일 때만 켜서 시스템 전체에 부담을 주지 않는다
    if 켬 != 정밀[0]:
        정밀[0] = 켬; (ctypes.windll.winmm.timeBeginPeriod if 켬 else ctypes.windll.winmm.timeEndPeriod)(1)


class 블렌드(ctypes.Structure):
    _fields_ = [("a", ctypes.c_byte), ("b", ctypes.c_byte), ("c", ctypes.c_ubyte), ("d", ctypes.c_byte)]


class 머리(ctypes.Structure):
    _fields_ = [("s", wintypes.DWORD), ("w", wintypes.LONG), ("h", wintypes.LONG), ("p", wintypes.WORD), ("b", wintypes.WORD), ("c", wintypes.DWORD), ("z", wintypes.DWORD), ("x", wintypes.LONG), ("y", wintypes.LONG), ("u", wintypes.DWORD), ("i", wintypes.DWORD)]


u.GetDC.restype = g.CreateCompatibleDC.restype = g.CreateDIBSection.restype = g.SelectObject.restype = ctypes.c_void_p
u.GetDC.argtypes = [ctypes.c_void_p]
u.GetParent.restype = ctypes.c_void_p; u.GetParent.argtypes = [ctypes.c_void_p]
g.CreateCompatibleDC.argtypes = [ctypes.c_void_p]; g.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
g.CreateDIBSection.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, wintypes.DWORD]
u.UpdateLayeredWindow.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
u.GetWindowLongPtrW.restype = ctypes.c_ssize_t; u.GetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int]
u.SetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t]

창 = tk.Tk()
창.overrideredirect(True)
창.attributes("-topmost", True)
# 작업표시줄을 뺀 작업 영역의 우측 하단. 액정이 열릴 자리(아래 54픽셀)를 남긴다
칸 = wintypes.RECT(); u.SystemParametersInfoW(48, 0, ctypes.byref(칸), 0)
x0, y0, 배, 첫모양 = 칸.right - W - 4, 칸.bottom - 354 - 위, 1.0, "큰"
# 빛 색: 푸른 성분만 재서 바꾼다. 은색과 붉은 눈금은 푸른 성분이 없어 그대로다. 길은 검정에서 흰색까지 끊기지 않는다
푸름 = (0, .4, 1); 색시작, 색끝 = .08, .86; 기본색 = 색시작 + (색끝 - 색시작) * (240 - 60 * 푸름[1]) / 300; 색 = [기본색]; 첫밝음 = False
try:
    # 저장 파일이 깨져도 기본값으로 켠다. 값은 하나씩 재서 받는다
    자리 = json.load(open(자리파일, encoding="utf-8")); a, b = int(자리[0]), int(자리[1]); x0, y0 = a, b
    배 = max(.6, min(1.4, float(자리[2]))) if len(자리) > 2 else 1.0
    첫모양 = 자리[3] if len(자리) > 3 and 자리[3] in ("큰", "셋") else 첫모양
    색[0] = max(0.0, min(1.0, float(자리[4]))) if len(자리) > 4 else 기본색
    첫밝음 = 자리[5] is True if len(자리) > 5 else False
    # 그림판 위 여백이 바뀌어도 시계가 화면에서 제자리에 있게 한다. 7번째 칸이 없으면 여백 122 시절에 저장한 것이다
    옛위 = float(자리[6]) if len(자리) > 6 else 122.0; y0 -= round((위 - 옛위) * 배)
except Exception:
    pass
배율 = [배]
폭높이 = [round(W * 배), round(H * 배)]


class 모니터(ctypes.Structure):
    _fields_ = [("s", wintypes.DWORD), ("m", wintypes.RECT), ("w", wintypes.RECT), ("f", wintypes.DWORD)]


u.MonitorFromPoint.restype = ctypes.c_void_p; u.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]; u.GetMonitorInfoW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]


def 안쪽(x, y):
    # 시계 가운데가 가장 가까운 모니터의 작업 영역 밖으로 나가지 않게 한다. 모니터를 뺀 뒤에도 잡을 수 있다
    i = 모니터(); i.s = ctypes.sizeof(모니터); u.GetMonitorInfoW(u.MonitorFromPoint(wintypes.POINT(x + 폭높이[0] // 2, y + 폭높이[1] // 2), 2), ctypes.byref(i)); r = i.w
    return max(r.left - 폭높이[0] // 2, min(r.right - 폭높이[0] // 2, x)), max(r.top - 폭높이[1] // 2, min(r.bottom - 폭높이[1] // 2, y))


x0, y0 = 안쪽(x0, y0)
창.geometry(f"{폭높이[0]}x{폭높이[1]}+{x0}+{y0}")
창.update()
핸들 = u.GetParent(창.winfo_id())
u.SetWindowLongPtrW(핸들, -20, u.GetWindowLongPtrW(핸들, -20) | 0x80000 | 0x80)

화면 = u.GetDC(None); 메모리 = g.CreateCompatibleDC(화면); 비트 = ctypes.c_void_p(); 옛비트맵 = [None]


def 판만들기():
    m = 머리(ctypes.sizeof(머리), 폭높이[0], -폭높이[1], 1, 32, 0, 0, 0, 0, 0, 0)
    새 = g.CreateDIBSection(메모리, ctypes.byref(m), 0, ctypes.byref(비트), None, 0)
    g.SelectObject(메모리, 새)
    if 옛비트맵[0]:
        g.DeleteObject(옛비트맵[0])
    옛비트맵[0] = 새


g.DeleteObject.argtypes = [ctypes.c_void_p]
판만들기()


def 색길(u):
    if u < 색시작:
        return u / 색시작, 0, 0
    if u > 색끝:
        s = (u - 색끝) / (1 - 색끝)
        return 1, s, 1
    h = (u - 색시작) / (색끝 - 색시작) * 5; i = min(int(h), 4) if h < 5 else 4; f = h - i
    return ((1, f, 0), (1 - f, 1, 0), (0, 1, f), (0, 1 - f, 1), (f, 0, 1))[i]


def 색입히기(im):
    if 색[0] == 기본색:
        return im
    # 매 장면 도는 계산이다. 파란 기가 있는 점만 정수로 칠한다
    a = np.array(im); 곳 = np.nonzero(a[..., 2].astype(np.int16) - a[..., 0] > 2); 세기 = a[..., 2][곳].astype(np.int32) - a[..., 0][곳]
    차 = ((np.array(색길(색[0]), np.float32) - np.array(푸름, np.float32)) * 256).astype(np.int32)
    for c in range(3):
        a[..., c][곳] = np.clip(a[..., c][곳].astype(np.int32) + (세기 * 차[c] >> 8), 0, 255)
    return Image.fromarray(a, "RGBA")


def 올리기(im, 고화질=False):
    마지막[0] = im
    if 배율[0] != 1:
        im = im.resize(tuple(폭높이), Image.LANCZOS if 고화질 else Image.BILINEAR)
    im = 색입히기(im)
    픽셀 = im.convert("RGBa").tobytes("raw", "BGRa"); 창쓰기(픽셀)
    return 픽셀


def 창쓰기(픽셀):
    ctypes.memmove(비트, 픽셀, 폭높이[0] * 폭높이[1] * 4)
    위치 = wintypes.POINT(창.winfo_x(), 창.winfo_y()); 크기 = wintypes.SIZE(*폭높이); 출발 = wintypes.POINT(0, 0); 섞기 = 블렌드(0, 0, 255, 1)
    u.UpdateLayeredWindow(핸들, 화면, ctypes.byref(위치), ctypes.byref(크기), 메모리, ctypes.byref(출발), 0, ctypes.byref(섞기), 2)


def 시각(텍스트):
    return datetime.datetime.fromisoformat(텍스트.replace("Z", "+00:00"))


def 수(x, 끝=100.0):
    # 파일의 숫자는 믿지 않는다. 숫자가 아니거나 NaN·무한·음수면 0, 너무 크면 끝에서 자른다
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    return min(max(v, 0.0), 끝) if math.isfinite(v) else 0.0


def 찾아(m, k):
    return next((o for o in (m.get("limits") or []) if isinstance(o, dict) and o.get("kind") == k), None)


def 끝시각(x):
    # 초기화 시각이 깨졌으면 없는 것으로 친다. 시간대가 없으면 UTC로 읽는다
    try:
        t = 시각(x["resetsAt"])
    except (KeyError, TypeError, ValueError, AttributeError):
        return None
    return t if t.tzinfo else t.replace(tzinfo=datetime.timezone.utc)


def 한도(m, k):
    x = 찾아(m, k)
    if not x:
        return 0.0
    끝 = 끝시각(x)
    if 끝 and 끝 <= datetime.datetime.now(datetime.timezone.utc):
        return 0.0
    return 수(x.get("percent"))


def 남은초(m, k):
    x = 찾아(m, k); 끝 = 끝시각(x) if x else None
    if not 끝:
        return 0
    return min(max(0, (끝 - datetime.datetime.now(datetime.timezone.utc)).total_seconds()), 99 * 86400)


def 요청():
    # 지금 시계가 보여 주는 세션의 모드에게 대화 압축을 맡긴다. 쓰는 중인 파일을 모드가 읽지 않게 바꿔 끼운다
    if 세션[0]:
        for _ in range(3):
            try:
                with open(명령파일 + ".tmp", "w", encoding="utf-8") as f:
                    json.dump({"state": "asked", "at": int(time.time() * 1000), "session": 세션[0]}, f)
                os.replace(명령파일 + ".tmp", 명령파일)
                return True
            except OSError:
                time.sleep(.02)
    세.요청실패(); 크.요청실패()
    return False


세션 = [None]
세 = 계기(요청); 크 = 크로노(요청); 변 = 변신(첫모양)
마지막 = [None]; 전판 = [None]; 잡음 = [None]; 크기속 = [0.0]
chrono_dial.기["줄"] = 배 * 1720
if 첫밝음:
    chrono_dial.테마(True)
본 = [None, 0.0]
활동 = ["idle", 0.0, False]  # 모드가 적은 클로드 상태, 그 시각(초), 백그라운드 작업 유무
상태밝기 = 1.0  # 바늘을 꾹 눌렀을 때와 같은 빛(gauge 빛목표 1.0). 낮추면 야광 숫자가 흰색까지 오르지 않는다
창끌기 = [None]
모양 = {"공전": "hand2", "전체": "hand2", "창": "fleur", "용두": "sb_h_double_arrow", "액정": "hand2", "바늘": "hand2"}
커서 = [""]


들림 = [0]


def 계():
    # 지금 보이는 시계. 값은 두 시계가 함께 받고, 손짓은 보이는 쪽만 받는다
    return 세 if 변.모양 == "셋" else 크


def 바닥들림():
    # 시계 하나는 더 커서 화면 아래로 나갈 수 있다. 나가는 만큼만 올린다
    return max(0, round(창.winfo_y() + 들림[0] + (139 + 위 + 170 + 12) * 배율[0] - 칸.bottom))


def 기둥곳(x, y):
    # 두 시계 공통 기둥. 시계가 돌아가 있으면 돌아간 자리를 되돌려서 잰다
    if 변.모양 == "큰":
        px, py = 크.제자리(2, x, y); 자리들 = (("위", 431, 50), ("아래", 431, 228))
    else:
        px, py = 세.제자리(1, x, y); 자리들 = (("위", 531, 107), ("아래", 531, 201))
    return next((n for n, a, b in 자리들 if math.hypot(px - a, py - b) < 16), None)


def 크기쓰기(새):
    # 가운데 시계의 중심은 화면에서 움직이지 않는다
    새 = round(max(.6, min(1.4, 새)), 3)
    if abs(새 - 배율[0]) < .002:
        return False
    중심x = 창.winfo_x() + 277 * 배율[0]; 중심y = 창.winfo_y() + (139 + 위) * 배율[0]
    배율[0] = 새; 폭높이[:] = [round(W * 새), round(H * 새)]; chrono_dial.기["줄"] = 새 * 1720
    창.geometry(f"{폭높이[0]}x{폭높이[1]}+{round(중심x - 277 * 새)}+{round(중심y - (139 + 위) * 새)}"); 창.update_idletasks()
    판만들기(); 앞그림[0] = 0.0; 들기(1 if 변.모양 == "큰" else 0)
    return True


def 내보내기(im, 고화질=False):
    # 흰 시계와 검은 시계는 0.35초에 걸쳐 겹쳐 바뀐다
    if 전판[0]:
        s = (time.perf_counter() - 전판[0][1]) / .35
        if s >= 1:
            전판[0] = None
        else:
            im = Image.blend(전판[0][0], im, s)
    올리기(im, 고화질)


def 들기(비):
    목표 = round(바닥들림() * 비)
    if 목표 != 들림[0]:
        창.geometry(f"+{창.winfo_x()}+{창.winfo_y() + 들림[0] - 목표}"); 창.update_idletasks(); 들림[0] = 목표


def 읽기():
    s = os.stat(파일).st_mtime; 벽 = time.time()
    for g in (세, 크):
        g.낡음 = 벽 - s > 3600  # 파일이 깨져 읽지 못해도 오래됐으면 흐리게 보인다
    if s == 본[0] and 벽 - 본[1] < 30:
        return
    d = json.load(open(파일, encoding="utf-8")); m = d["meter"]
    if not isinstance(m, dict):
        raise ValueError("meter")
    # 두 시계가 같은 값을 갖도록 값을 다 거른 다음에 넣는다
    토큰 = 수(m.get("contextTokens"), 1e8); 창크기 = 수(m.get("contextWindow"), 1e8); 대화 = min(토큰 / 창크기 * 100, 100.0) if 창크기 else 0.0
    이번, 지난 = d.get("current") or {}, d.get("last") or {}
    턴 = 수((이번.get("fresh") if isinstance(이번, dict) else 0) or (지난.get("fresh") if isinstance(지난, dict) else 0), 1e8)
    주간, 다섯시간 = 한도(m, "seven_day"), 한도(m, "five_hour"); 다섯 = 남은초(m, "five_hour"); 주 = 남은초(m, "seven_day")
    for g in (세, 크):
        g.값넣기(주간, 대화, 다섯시간, time.perf_counter())
        g.남은분 = int(다섯 // 60); g.시간없음 = 다섯 <= 0
        g.주간글 = (str(int(주 // 86400)), f"{int(주 % 86400 // 3600):02d}"); g.대화만 = 토큰 / 10000; g.턴만 = 턴 / 10000
    본[:] = [s, 벽]; 세션[0] = d.get("session") if isinstance(d.get("session"), str) else None
    상태 = d.get("activity"); 활동[:] = [상태 if 상태 in ("working", "waiting") else "idle", 수(d.get("at"), 1e15) / 1000, d.get("background") is True]


def 상태빛값(벽):
    # 일하는 중이면 켜 두고, 사용자를 기다리면 0.3초씩 깜빡인다. 30초 넘게 소식이 없으면 그 세션이 멈춘 것으로 보고 끈다
    상태, 때, _ = 활동
    if 상태 == "idle" or abs(벽 - 때) > 30:  # 시각이 미래로 찍혀도(시계를 뒤로 돌림) 30초 넘게 벌어지면 끈다
        return 0.0
    return 상태밝기 if 상태 == "working" or 벽 % .6 < .3 else 0.0


def 백빛값(벽):
    # 백그라운드 작업이 도는 동안 CHAT 바늘을 켜 둔다. 깜빡이지 않는다
    _, 때, 백 = 활동
    return 상태밝기 if 백 and abs(벽 - 때) <= 30 else 0.0


def 명령확인():
    if 세.덮개 is None and 크.덮개 is None:
        return
    try:
        상태 = json.load(open(명령파일, encoding="utf-8")).get("state")
    except (OSError, ValueError, AttributeError):
        return
    if 상태 in ("failed", "done"):
        세.요청실패(); 크.요청실패()
    elif 상태 == "queued":
        세.대기 = 크.대기 = True  # 모드가 받아 줄 세웠다. 턴이 끝나면 돈다


def 꺼달라나():
    try:
        return json.load(open(켜짐파일, encoding="utf-8")).get("on") is False
    except (OSError, ValueError, AttributeError):
        return False  # 깨진 표시는 켜 둔 것으로 본다(모드의 wanted와 같다)


def 끄기(e=None):
    # 사용자가 끈 시계는 다음 세션이 다시 띄우지 않는다. /clock 으로만 켠다
    try:
        with open(켜짐파일 + ".tmp", "w", encoding="utf-8") as f:
            json.dump({"on": False}, f)
        os.replace(켜짐파일 + ".tmp", 켜짐파일)
    except OSError:
        pass
    창.destroy()


앞읽기 = [0.0]
앞그림 = [0.0]
끝남 = [False]
세대 = [0]
색만짐 = [-9.0]
멈춤장면 = {}
일꾼 = [None]
앞돌기 = [None]
앞키 = [None]
변끝 = [0.0]
뗀시각 = [None]
끌렸다 = [False]
오류파일 = os.path.expanduser(r"~/.claude/progress/token-panel-error.log")


def 띠밀기(지금, dt):
    # 색을 만진 뒤 1.2초까지 켜 두고 천천히 끈다. 움직이는 동안 참을 돌려준다
    목표 = 1.0 if 지금 - 색만짐[0] < 1.2 else 0.0; 띠 = chrono_dial.기["띠"]
    if 띠 == 목표:
        return False
    칸 = dt / (.15 if 목표 else .5); chrono_dial.기["띠"] = min(1.0, 띠 + 칸) if 목표 else max(0.0, 띠 - 칸)
    return True


def 멈춤키(g, 지금, 등):
    # 멈춘 장면의 모든 재료. 같으면 그리지 않고 만들어 둔 장면을 그대로 쓴다
    return (tuple(round(g.표시값(i), 1) for i in range(3)), g.상태빛, g.백빛, g.남은분, tuple(g.주간글), round(g.대화만, 2), round(g.턴만, 2), g.낡음, round(g.액정, 2), g.붉음, 지금 % 1 < .5, round((.725 + .275 * math.cos(math.pi * 지금 / 1.2)) * 8) if 등 else 0,
            g.시간없음, 변.모양, 색[0], tuple(폭높이), chrono_dial.기["밝음"], chrono_dial.기["눌"], round(chrono_dial.기["줄"]), round(chrono_dial.기["띠"], 2))


def 데우기멈춤():
    # 흑백을 바꾸기 전에 멈춰 옛 색 그림이 새 캐시에 들어가지 않게 한다
    세대[0] += 1
    if 일꾼[0]:
        일꾼[0].join(1)


def 데우기시작():
    # 시작과 흑백 전환 뒤에 한 번. 새로 시작하면 앞 일은 멈춘다
    데우기멈춤(); 세대[0] += 1; 내세대 = 세대[0]
    일꾼[0] = threading.Thread(target=chrono_dial.데우기, args=(lambda: 세대[0] == 내세대,), daemon=True); 일꾼[0].start()


def 시계그림(g, 지금, 고화질=False):
    return 그림(g, 지금, 고화질) if g is 세 else chrono_dial.그림(g, 지금, 고화질)


def 돌기():
    # 한 번 틀려도 다음 장면은 반드시 예약한다. 틀린 내용은 파일에 남긴다
    뒤 = 50
    try:
        뒤 = 돌기속()
    except Exception:
        try:
            open(오류파일, "w", encoding="utf-8").write(traceback.format_exc())
        except OSError:
            pass
    if 끝남[0]:
        창.destroy()
        return
    창.after(뒤, 돌기)


def 놓침풀기(지금):
    # 버튼을 누른 채 포커스를 잃으면 놓임 신호가 안 온다. 0.3초 넘게 안 눌렸으면 잡음을 푼다
    g = 계()
    if not (잡음[0] or 창끌기[0] or g.누름) or u.GetAsyncKeyState(1) & 0x8000 or u.GetAsyncKeyState(2) & 0x8000:
        뗀시각[0] = None
    elif 뗀시각[0] is None:
        뗀시각[0] = 지금
    elif 지금 - 뗀시각[0] > .3:
        뗀시각[0] = None
        if 잡음[0] and 잡음[0]["종류"] == "위":
            잡음[0] = None; chrono_dial.기["눌"] = False  # 놓은 적이 없으니 흑백은 바꾸지 않는다
            return
        if g.용두진행:
            g.용두가득 = False  # 놓친 것을 요청으로 치지 않는다
        놓임(None)


def 돌기속():
    시작 = time.perf_counter(); 놓침풀기(시작)
    if 시작 - 앞읽기[0] > .5:
        앞읽기[0] = 시작; 끝남[0] = 꺼달라나()
        try:
            읽기(); 명령확인()
        except Exception:
            pass  # 사용량 파일이 잠시 깨져도 시계는 멈추지 않는다. 다음 읽기에서 다시 본다
    벽 = time.time(); 세.상태빛 = 크.상태빛 = 상태빛값(벽); 세.백빛 = 크.백빛 = 백빛값(벽)
    세.틱(시작); 크.틱(시작)
    dt = 잘라(시작 - 앞돌기[0], 0, .05) if 앞돌기[0] is not None else .016; 앞돌기[0] = 시작
    장면 = 변.틱(dt, 시작)
    if 크기속[0] and not 잡음[0]:
        전 = 배율[0]; 크기쓰기(전 + 크기속[0] * dt); 크기속[0] *= math.exp(-dt / .16)
        if abs(크기속[0]) < .01 or 배율[0] == 전:
            크기속[0] = 0.0; 자리저장()
    if 장면:
        들기(잘라((장면["k"] - 130) / 40, 0, 1))
        정밀타이머(True); 변끝[0] = 시작; 내보내기(chrono_dial.합체그림(세, 크, 장면, 시작, 변.흔들림(시작))); 앞그림[0] = 0.0
        return max(1, 16 - int((time.perf_counter() - 시작) * 1000))
    g = 계()
    띠 = 띠밀기(시작, dt)
    if g.활동중() or 변.쿵 is not None or 전판[0] or 잡음[0] or 크기속[0] or 띠:
        정밀타이머(True); 판 = 시계그림(g, 시작); 흔 = 변.흔들림(시작)
        내보내기(ImageChops.offset(판, 0, 흔) if 흔 else 판); 앞그림[0] = 0.0
        return max(1, 16 - int((time.perf_counter() - 시작) * 1000))
    # 멈춘 동안은 또렷한 바늘로 그리고, 경고등과 콜론만 움직이도록 드물게 다시 그린다
    # 깜빡임은 0.05초마다 키만 보고, 켜짐 · 꺼짐 두 장면은 한 번씩만 그려 캐시에서 꺼내 쓴다
    정밀타이머(False); 등 = any(g.표시값(i) >= 80 for i in range(3)); 간격 = .05 if 활동[0] == "waiting" else .1 if 등 else .5
    if 시작 - 앞그림[0] >= 간격:
        if not 앞그림[0]:
            앞키[0] = None  # 움직인 뒤에는 같은 키여도 화면을 다시 쓴다
        앞그림[0] = 시작; 키 = 멈춤키(g, 시작, 등); 픽셀 = 멈춤장면.get(키)
        if 키 != 앞키[0]:
            앞키[0] = 키
            if 픽셀:
                창쓰기(픽셀)
            else:
                if len(멈춤장면) >= 40:  # 경고등 8단 × 콜론 2 × 깜빡임 2가 다 들어가게 한다
                    멈춤장면.clear()
                멈춤장면[키] = 올리기(시계그림(g, 시작, True), True)
    if chrono_dial.맞춤캐시 and 시작 - 변끝[0] > 30:
        chrono_dial.맞춤캐시.clear()  # 변신 재료는 끝나고 30초 뒤 내려놓는다
    return 50


def 논리(e):
    # 창 안 좌표를 100% 크기 기준 좌표로 바꾼다. 동작 규칙은 크기를 모른다
    return e.x / 배율[0], e.y / 배율[0] - 위


def 눌림(e):
    if 변.진행:
        return
    기 = 기둥곳(*논리(e))
    if 기 == "위":
        잡음[0] = dict(종류="위"); chrono_dial.기["눌"] = True
        return
    if 기 == "아래":
        잡음[0] = dict(종류="크기", y=e.y_root, s0=배율[0], 앞=배율[0], 시=time.perf_counter()); 크기속[0] = 0.0
        return
    곳 = 계().눌림(*논리(e), time.perf_counter())
    if 곳 == "창":
        창끌기[0] = (e.x, e.y)
    elif 곳 == "용두":
        잡음[0] = dict(종류="용두", x=e.x_root, y=e.y_root, u0=색[0], 축=None)


def 끌림(e):
    if 창끌기[0]:
        창.geometry(f"+{창.winfo_pointerx() - 창끌기[0][0]}+{창.winfo_pointery() - 창끌기[0][1]}"); 끌렸다[0] = True
        return
    n = 잡음[0]
    if n and n["종류"] == "크기":
        지금 = time.perf_counter(); dt = max(.004, 지금 - n["시"]); 크기쓰기(n["s0"] - (e.y_root - n["y"]) * .0035)
        크기속[0] = 크기속[0] * .6 + (배율[0] - n["앞"]) / dt * .4; n["앞"] = 배율[0]; n["시"] = 지금
        return
    if n and n["종류"] == "위":
        return
    if n and n["종류"] == "용두":
        # 용두는 처음 움직인 방향으로 정해진다. 위아래는 빛 색, 바깥쪽은 초기화다
        dx = e.x_root - n["x"]; dy = e.y_root - n["y"]
        if n["축"] is None:
            if math.hypot(dx, dy) <= 5:
                return
            n["축"] = "세로" if abs(dy) > abs(dx) else "가로"
        if n["축"] == "세로":
            u = max(0.0, min(1.0, n["u0"] - dy * .003)); 색[0] = 기본색 if abs(u - 기본색) < .006 else u; 색만짐[0] = time.perf_counter(); 앞그림[0] = 0.0
            return
    if not 변.진행:
        계().끌림(*논리(e), time.perf_counter())


def 자리저장():
    # 쓰는 중에 꺼져도 파일이 깨지지 않게 다른 이름으로 쓰고 바꿔 끼운다
    임시 = 자리파일 + ".tmp"
    try:
        with open(임시, "w", encoding="utf-8") as f:
            json.dump([창.winfo_x(), 창.winfo_y() + 들림[0], 배율[0], "큰" if 변.합 else "셋", 색[0], chrono_dial.기["밝음"], 위], f)
        os.replace(임시, 자리파일)
    except OSError:
        pass


def 놓임(e):
    n = 잡음[0]; 잡음[0] = None
    if n and n["종류"] == "위":
        chrono_dial.기["눌"] = False
        데우기멈춤(); 옛장면 = 시계그림(계(), time.perf_counter()); chrono_dial.테마(not chrono_dial.기["밝음"]); 앞그림[0] = 0.0; 자리저장()
        if 옛장면:
            시계그림(계(), time.perf_counter()); 전판[0] = (옛장면, time.perf_counter())  # 첫 장면을 만든 뒤에 시간을 재야 겹침이 잘리지 않는다
        데우기시작()
        return
    if n and n["종류"] == "크기":
        if time.perf_counter() - n["시"] > .09:
            크기속[0] = 0.0
        크기속[0] = max(-1.6, min(1.6, 크기속[0])); 자리저장()
        return
    if n and n["종류"] == "용두" and n["축"] == "세로":
        계().누름 = None; 자리저장()
        return
    if 창끌기[0]:
        창끌기[0] = None
        if 끌렸다[0]:
            끌렸다[0] = False; 들림[0] = 0; x, y = 안쪽(창.winfo_x(), 창.winfo_y()); 창.geometry(f"+{x}+{y}"); 창.update_idletasks()
        자리저장()
    if not 변.진행:
        계().놓임(time.perf_counter())


def 전환(e):
    # 우클릭: 시계 하나와 세 시계가 서로 바뀐다. 움직이는 중에 다시 누르면 그 자리에서 되돌아간다
    현 = 계(); 다른 = 크 if 현 is 세 else 세; 창끌기[0] = None
    변.시작(세, 크); 다른.덮개 = 현.덮개; 다른.요청시각 = 현.요청시각; 자리저장()


def 지나감(e):
    기 = None if 변.진행 else 기둥곳(*논리(e)); 곳 = None if 변.진행 or 기 else 계().찾기(*논리(e)); c = "hand2" if 기 == "위" else "sb_v_double_arrow" if 기 else 모양[곳[0]] if 곳 else "arrow"
    if c != 커서[0]:
        커서[0] = c; 창.configure(cursor=c)


def 굴림(e):
    # 휠: 용두 위는 빛 색, 아래 기둥 위는 크기, 시계 위는 그 시계 바늘을 쌩쌩 돌린다(아래로 굴리면 시계 방향)
    x, y = 논리(e); 기 = None if 변.진행 else 기둥곳(x, y); 곳 = None if 변.진행 or 기 else 계().찾기(x, y); 쪽 = 1 if e.delta > 0 else -1
    if 변.진행 or not (곳 or 기):
        return
    if 곳 and 곳[0] == "용두":
        u = max(0.0, min(1.0, 색[0] + 쪽 * .012)); 색[0] = 기본색 if abs(u - 기본색) < .006 else u; 색만짐[0] = time.perf_counter(); 앞그림[0] = 0.0; 자리저장()
        return
    if 기 and 기 != "위":
        크기속[0] = max(-1.6, min(1.6, 크기속[0] + 쪽 * .24))
        return
    if 곳:
        i = 곳[1] if 곳[0] in ("바늘", "공전") else 2
        계().휠돌림(i, -쪽, time.perf_counter())


try:
    읽기()
except Exception:
    pass
창.bind("<Button-1>", 눌림)
창.bind("<B1-Motion>", 끌림)
창.bind("<ButtonRelease-1>", 놓임)
창.bind("<Motion>", 지나감)
창.bind("<MouseWheel>", 굴림)
창.bind("<Button-3>", 전환)
창.bind("<Shift-Button-3>", 끄기)
if 변.모양 == "큰":
    들기(1)
데우기시작()
돌기()
창.mainloop()
