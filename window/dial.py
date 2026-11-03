# 시계 모양 토큰 계기판의 그림. 원판과 바늘, 빛, 액정, 용두는 브라우저가 뽑은 PNG이고, 여기서는 층을 조립한다. AI를 부르지 않는다.
# 세 시계를 조각으로 나눠 좌우 시계가 가운데를 돌 수 있게 한다.
import math
import numpy as np
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from gauge import 시계들

여기 = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    여기 = os.path.join(sys._MEIPASS, "window")  # 실행 파일판은 그림을 window/ · center/로 나눠 품는다
W, H, 위 = 554, 564, 142        # 창 크기와 시계 묶음의 세로 시작. 투명한 곳은 클릭이 바탕화면으로 지나간다
반 = (120, 120, 150)               # 시계 조각의 반지름. 용두와 그림자까지 들어간다
손크기 = (178, 178, 270, 91, 353)  # 뒤의 둘은 크로노그래프의 작은 다이얼과 큰 판
빨강, 흰색 = (255, 58, 34), (230, 244, 255)


def 열기(이름, 크기=None):
    im = Image.open(os.path.join(여기, 이름)).convert("RGBA")
    return im.resize(크기, Image.LANCZOS) if 크기 else im


def 칸(i):
    cx, cy = 시계들[i][:2]; h = 반[i]
    return cx - h, cy - h, cx + h, cy + h


바탕 = [열기(f"base{i}.png", (554, 296)).crop(칸(i)) for i in range(3)]
빛판 = []
for i in range(3):
    층 = 열기(f"glow{i}.png", (554, 296)).crop(칸(i)); 큼 = 2 * 반[i] * 3; q = 시계들[i][2] * .847
    m = Image.new("L", (큼, 큼), 0); c = 큼 / 2
    ImageDraw.Draw(m).ellipse((c - q * 3, c - q * 3, c + q * 3, c + q * 3), fill=255)
    층.putalpha(ImageChops.multiply(층.getchannel("A"), m.resize(층.size, Image.LANCZOS))); 빛판.append(층)
바늘 = 열기("hand.png")
손3 = [바늘.resize((s * 3, s * 3), Image.LANCZOS) for s in 손크기]
손1 = [바늘.resize((s, s), Image.LANCZOS) for s in 손크기]
손그림자 = []
for h in 손1:
    검정 = Image.new("RGBA", h.size, (0, 0, 0, 255)); 검정.putalpha(h.getchannel("A").point(lambda v: int(v * .6))); 손그림자.append(검정.filter(ImageFilter.GaussianBlur(1.6)))
액정틀 = 열기("panel.png", (178, 208))
꼭지 = 열기("crown.png", (30, 22))
세기표 = [[int(v * k / 32) for v in range(256)] for k in range(33)]
곁장식 = [None]; 어두운글 = [False]
손캐시 = {}; 글캐시 = {}; 액정캐시 = {}; 등캐시 = {}; 돌림캐시 = {}; 바탕캐시 = {}; 붉음캐시 = {}


def 파랑줄이기(im, a=.45, 반경=3):
    # 흰 시계 전용 빛. 야광 숫자와 그 둘레는 두고 파란 빛만 줄인다
    arr = np.array(im).astype(np.float32); m = np.clip((arr[..., 0] - 105) / 70, 0, 1)
    h = np.clip(np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(반경))).astype(np.float32) / 255 * 2.2, 0, 1)
    arr[..., 3] *= a + (1 - a) * np.maximum(m, h * .75); return Image.fromarray(arr.astype(np.uint8), "RGBA")


def 테글자빼기(im, cx, cy, 안):
    # 빛 층에서 바깥 테의 흰 글씨만 뺀다. 테 글씨는 판의 검정 그대로 남고 눈금등은 야광으로 빛난다
    arr = np.array(im).astype(np.float32); y, x = np.mgrid[0:arr.shape[0], 0:arr.shape[1]]; 테 = np.clip((np.hypot(x - cx, y - cy) - 안) / 2, 0, 1)
    arr[..., 3] *= 1 - 테 * np.clip((arr[..., 0] - 105) / 70, 0, 1); return Image.fromarray(arr.astype(np.uint8), "RGBA")


def 약하게(im, 세기):
    im = im.copy(); im.putalpha(im.getchannel("A").point(세기표[max(0, min(32, round(세기 * 32)))]))
    return im


def 붙(판, im, x, y):
    x, y = round(x), round(y); sx = max(0, -x); sy = max(0, -y)
    if sx >= im.width or sy >= im.height or x >= 판.width or y >= 판.height:
        return
    판.alpha_composite(im, (max(0, x), max(0, y)), (sx, sy, min(im.width, sx + 판.width - max(0, x)), min(im.height, sy + 판.height - max(0, y))))


def 획(k, w, h, t):
    g = .35
    가로 = lambda x1, x2, y: [(x1, y), (x1 + t / 2, y - t / 2), (x2 - t / 2, y - t / 2), (x2, y), (x2 - t / 2, y + t / 2), (x1 + t / 2, y + t / 2)]
    세로 = lambda y1, y2, x: [(x, y1), (x + t / 2, y1 + t / 2), (x + t / 2, y2 - t / 2), (x, y2), (x - t / 2, y2 - t / 2), (x - t / 2, y1 + t / 2)]
    왼, 오, 상, 중, 하 = t / 2 + g, w - t / 2 - g, t / 2, h / 2, h - t / 2
    return {"a": 가로(왼, 오, 상), "g": 가로(왼, 오, 중), "d": 가로(왼, 오, 하), "f": 세로(상 + g, 중 - g, t / 2), "b": 세로(상 + g, 중 - g, w - t / 2), "e": 세로(중 + g, 하 - g, t / 2), "c": 세로(중 + g, 하 - g, w - t / 2)}[k]


획표 = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg"}


def 칠획(글, 높이, 색=흰색, 콜론=True):
    키 = (글, 높이, 색, 콜론)
    if 키 in 글캐시:
        return 글캐시[키]
    w, h, t, 간 = 10, 18, 2.3, 2.6; 배 = 높이 / h * 4; 조각 = []; x = 0.0
    for c in 글:
        if c == ":":
            for y in (4.6, 11.1):
                조각.append(([(x + .6, y), (x + 2.9, y), (x + 2.9, y + 2.3), (x + .6, y + 2.3)], 255 if 콜론 else 38))
            x += 3.5 + 간 - .6
        elif c == ".":
            조각.append(([(x, h - 2.3), (x + 2.3, h - 2.3), (x + 2.3, h), (x, h)], 255)); x += 2.3 + 간 - .6
        else:
            for k in "abcdefg":
                조각.append(([(x + a, b) for a, b in 획(k, w, h, t)], 255 if k in 획표[c] else 18))
            x += w + 간
    폭 = x - 간 + 4
    m = Image.new("L", (int(폭 * 배) + 8, int(h * 배) + 4), 0); d = ImageDraw.Draw(m)
    for 점들, 값 in 조각:
        d.polygon([((a + 1.6 - b * .0875 + .9) * 배, b * 배) for a, b in 점들], fill=값)
    m = m.resize((max(1, m.width // 4), max(1, m.height // 4)), Image.LANCZOS)
    im = Image.new("RGBA", m.size, 색 + (255,)); im.putalpha(m)
    글캐시[키] = im
    return im


def 시각그림(글, 임박, 콜론, 빛받음=False):
    어둡 = 어두운글[0] and not 빛받음; 키 = ("시각", 글, 임박, 콜론, 어둡)
    if 키 not in 글캐시:
        겉 = 칠획(글, 17, 빨강 if 임박 else (21, 23, 27) if 어둡 else 흰색, 콜론); 여백 = 8
        판 = Image.new("RGBA", (겉.width + 여백 * 2, 겉.height + 여백 * 2), (0, 0, 0, 0))
        어둠 = Image.new("RGBA", 겉.size, (138, 20, 8, 255) if 임박 else (5, 21, 63, 255)); 어둠.putalpha(겉.getchannel("A"))
        층 = Image.new("RGBA", 판.size, (0, 0, 0, 0)); 층.alpha_composite(어둠, (여백, 여백))
        if not 어둡:
            판.alpha_composite(층.filter(ImageFilter.GaussianBlur(3))); 판.alpha_composite(층.filter(ImageFilter.GaussianBlur(1.4)))
        판.alpha_composite(겉, (여백, 여백))
        글캐시[키] = 판
    return 글캐시[키]


def 한국어인가():
    # 컴퓨터 표시 언어가 한국어면 「일 · 시간 · 만」, 아니면 「d · h · k」. 환경 변수 TOKEN_PANEL_LANG=ko|en으로 정할 수도 있다
    정함 = os.environ.get("TOKEN_PANEL_LANG", "").lower()
    if 정함 in ("ko", "en"):
        return 정함 == "ko"
    try:
        import ctypes
        return ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x12
    except Exception:
        return False


# 한국어 단위는 한국어 윈도우에 늘 있는 맑은 고딕으로, 영어 단위는 Pillow에 들어 있는 글꼴로 그린다. 글꼴을 따로 내려받지 않는다
_맑은 = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "malgunbd.ttf")
한국어 = 한국어인가() and os.path.exists(_맑은)
try:
    단위글꼴 = ImageFont.truetype(_맑은, 9) if 한국어 else ImageFont.load_default(size=9)
except TypeError:
    단위글꼴 = ImageFont.load_default()  # Pillow 10.1보다 옛 판


def 천단위(만):
    # 「만」(1만 토큰) 값을 영어 단위 「k」(1천 토큰)로 바꾼다. 100k 아래는 소수 한 자리
    k = 만 * 10
    return f"{k:.1f}" if k < 100 else f"{k:.0f}"


def 액정그림(주간글, 대화만, 턴만, 틀=None, 여백=124):
    # 일곱 획 숫자에는 음수 부호·inf·nan 획이 없다. 그릴 수 없는 값은 0으로 그린다
    대화만, 턴만 = (v if math.isfinite(v) and v >= 0 else 0.0 for v in (대화만, 턴만))
    키 = (주간글, f"{대화만:.1f}", f"{턴만:.1f}", 여백)
    if 키 not in 액정캐시:
        액정캐시.clear()
        판 = (틀 or 액정틀).copy(); 글꼴 = 단위글꼴; d = ImageDraw.Draw(판)
        if 한국어:
            줄들 = ([(주간글[0], "일"), (주간글[1], "시간")], [(키[1], "만")], [(키[2], "만")])
        else:
            줄들 = ([(주간글[0], "d"), (주간글[1], "h")], [(천단위(대화만), "k")], [(천단위(턴만), "k")])
        for n, 칸들 in enumerate(줄들):
            x = 178 - 4 - 14; y = 4 + 여백 + 9 + 18 * n
            for 수, 단위 in reversed(칸들):
                폭 = d.textlength(단위, font=글꼴); d.text((x, y), 단위, font=글꼴, fill=(159, 176, 198, 255), anchor="rm"); x -= 폭 + 2
                im = 칠획(수, 12); 붙(판, im, x - im.width, y - im.height // 2); x -= im.width + 2
        액정캐시[키] = 판
    return 액정캐시[키]


def 호칠(W, H, cx, cy, R, 반각, t):
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for k in range(91):
        각 = math.radians(-반각 + 반각 * k / 45); x = cx + R * math.sin(각); y = cy + R * math.cos(각); d.ellipse((x - t / 2, y - t / 2, x + t / 2, y + t / 2), fill=255)
    return m


def 등그림(i, 밝기, 크기=None):
    # 판을 파낸 홈 안의 붉은 막대. 시계 곡선을 따른다. 크기는 곡선의 기준 반지름이다
    r = 크기 or 시계들[i][2]; 흰 = 어두운글[0]; k = (i, round(밝기 * 8), 크기, 흰)
    if k not in 등캐시:
        b = k[1] / 8; 배 = 4; 폭 = int(r * .6); 높 = int(r * .3); W, H = 폭 * 배, 높 * 배; cx = W / 2; R = r * .62 * 배; cy = H / 2 - R
        반각 = 11.5 + max(0, r - 130) * .155; t = min(max(3.4, r * .05), 6.5 - max(0, r - 130) * .05) * 배
        홈 = 호칠(W, H, cx, cy, R, 반각, t * 1.35); 속 = 호칠(W, H, cx, cy, R, 반각, t * .82); 층 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        밑빛 = ImageChops.subtract(ImageChops.offset(홈, 0, 3), 홈).point(lambda v: int(v * (.9 if 흰 else .34))); 층.paste(Image.new("RGBA", (W, H), (255, 255, 255, 255)), (0, 0), 밑빛)
        판 = Image.new("RGBA", (W, H), (70, 72, 78, 255) if 흰 else (6, 6, 8, 255)); 판.putalpha(홈.point(lambda v: int(v * .92))); 층.alpha_composite(판)
        붉 = Image.new("RGBA", (W, H), tuple(int(a + (z - a) * b) for a, z in zip((86, 12, 10), (206, 30, 22))) + (255,)); 붉.putalpha(속); 층.alpha_composite(붉)
        그늘 = ImageChops.subtract(속, ImageChops.offset(속, 0, 4)).filter(ImageFilter.GaussianBlur(2)); 검 = Image.new("RGBA", (W, H), (0, 0, 0, 255)); 검.putalpha(ImageChops.multiply(그늘, 속).point(lambda v: int(v * .75))); 층.alpha_composite(검)
        등캐시[k] = 층.resize((폭, 높), Image.LANCZOS)
    return 등캐시[k]


def 붉은그림(p, 세기):
    # 가운데 검은 원이 시계 방향으로 붉게 찬다. 테두리에는 가는 붉은 선이 함께 둘러진다
    키 = round(p * 500)
    if 키 not in 붉음캐시:
        if len(붉음캐시) > 120:
            붉음캐시.clear()
        크 = 160; c = 80; r = 34 * 2; 선 = 34.7 * 2; q = 키 / 500
        판 = Image.new("RGBA", (크, 크), (0, 0, 0, 0)); d = ImageDraw.Draw(판)
        d.ellipse((c - r, c - r, c + r, c + r), fill=(214, 30, 14, 26))
        if q > 0:
            d.pieslice((c - r, c - r, c + r, c + r), -90, -90 + 360 * q, fill=(214, 30, 14, 158))
        고리 = Image.new("RGBA", (크, 크), (0, 0, 0, 0)); e = ImageDraw.Draw(고리)
        e.ellipse((c - 선, c - 선, c + 선, c + 선), outline=(238, 55, 34, 56), width=2)
        if q > 0:
            e.arc((c - 선, c - 선, c + 선, c + 선), -90, -90 + 360 * q, fill=(255, 74, 48, 255), width=3)
        판.alpha_composite(고리.filter(ImageFilter.GaussianBlur(4))); 판.alpha_composite(고리)
        붉음캐시[키] = 판.resize((80, 80), Image.BILINEAR)
    return 약하게(붉음캐시[키], 세기) if 세기 < .98 else 붉음캐시[키]


def 다듬기(im):
    # 빈 곳을 잘라 내면 얹는 면적이 크게 줄어든다
    b = im.getbbox() or (0, 0, 1, 1)
    return im.crop(b), b[0] - im.width / 2, b[1] - im.height / 2


def 돌린층(원본, 각, 필터):
    # 판 전체를 돌리지 않고 바늘이 도착하는 사각형만 계산한다. 결과는 rotate와 같고 훨씬 빠르다
    w, h = 원본.size; cx, cy = w / 2, h / 2; 틀 = 원본.getbbox() or (0, 0, 1, 1); 라 = math.radians(각); c, s = math.cos(라), math.sin(라)
    xs, ys = zip(*[(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x in (틀[0], 틀[2]) for y in (틀[1], 틀[3])])
    x0, y0, x1, y1 = max(0, math.floor(min(xs)) - 2), max(0, math.floor(min(ys)) - 2), min(w, math.ceil(max(xs)) + 2), min(h, math.ceil(max(ys)) + 2)
    c0 = cx - c * cx - s * cy; f0 = cy + s * cx - c * cy
    im = 원본.transform((x1 - x0, y1 - y0), Image.AFFINE, (c, s, c0 + c * x0 + s * y0, -s, c, f0 - s * x0 + c * y0), 필터); b = im.getbbox() or (0, 0, 1, 1)
    return im.crop(b), x0 + b[0] - cx, y0 + b[1] - cy


def 네모돌림(im, x, y, 배):
    # 90도 단위는 그림을 다시 계산하지 않고 뒤집어서 얻는다
    if 배 == 1:
        return im.transpose(Image.ROTATE_270), -(y + im.height), x
    if 배 == 2:
        return im.transpose(Image.ROTATE_180), -(x + im.width), -(y + im.height)
    if 배 == 3:
        return im.transpose(Image.ROTATE_90), y, -(x + im.width)
    return im, x, y


def 돌린손(i, 각, 그림자, 저장):
    # 빠르게 돌 때는 2도 단위로 저장해 둔 그림을 쓴다. 90도까지만 저장하고 나머지는 뒤집는다
    원본 = (손그림자 if 그림자 else 손1)[i]; 필터 = Image.BILINEAR if 그림자 else Image.BICUBIC
    if not 저장:
        return 돌린층(원본, 각, 필터)
    배, 남 = divmod(round(각 / 2) % 180, 45); 키 = (i, 그림자, 남)
    if 키 not in 돌림캐시:
        돌림캐시[키] = 돌린층(원본, 남 * 2, 필터)
    return 네모돌림(*돌림캐시[키], 배)


def 손붙이기(판, i, cx, cy, 각, 속도, 고화질):
    저장 = abs(속도) >= 300
    im, x, y = 돌린손(i, 각, True, True); 붙(판, im, cx + x + 2, cy + y + 3)
    if 고화질:
        키 = (i, round(각, 1))
        if 키 not in 손캐시:
            if len(손캐시) > 12:
                손캐시.clear()
            s = 손크기[i]; 손캐시[키] = 다듬기(손3[i].rotate(-각, Image.BICUBIC).resize((s, s), Image.LANCZOS))
        im, x, y = 손캐시[키]; 붙(판, im, cx + x, cy + y)
        return
    L = max(0, min(1, (abs(속도) - 500) / 1500))
    if L > 0:
        for 뒤, 세기 in ((.011, .2), (.0055, .4)):
            im, x, y = 돌린손(i, 각 - 속도 * 뒤, False, True); 붙(판, 약하게(im, L * 세기), cx + x, cy + y)
    im, x, y = 돌린손(i, 각, False, 저장); 붙(판, im, cx + x, cy + y)


그늘 = [None, None]


def 몸과그늘(면, 반지름):
    # 바깥 그늘은 빛 방향이 있어 판과 함께 돌면 안 된다. 돌지 않게 따로 뗀다
    크 = 면.width * 3; c = 크 / 2; q = 반지름 * 3
    m = Image.new("L", (크, 크), 0); ImageDraw.Draw(m).ellipse((c - q, c - q, c + q, c + q), fill=255); m = m.resize(면.size, Image.LANCZOS)
    몸 = 면.copy(); 몸.putalpha(ImageChops.multiply(면.getchannel("A"), m)); 늘 = 면.copy(); 늘.putalpha(ImageChops.multiply(면.getchannel("A"), ImageChops.invert(m)))
    return 몸, 늘


def 곁나누기(반지름=85):
    for i in (0, 1):
        바탕[i], 그늘[i] = 몸과그늘(바탕[i], 반지름)


def 곁바탕(i):
    # 돌릴 곁 시계의 재료. 오른쪽 곁은 용두와 기둥까지 함께 돈다
    if ("원", i) not in 바탕캐시:
        cx, cy, *_ = 시계들[i]; h = 반[i]; 조각 = Image.new("RGBA", 바탕[i].size, (0, 0, 0, 0))
        if i == 1:
            붙(조각, 꼭지, 522 - (cx - h), 143 - (cy - h))
            if 곁장식[0]:
                곁장식[0](조각, h)
        조각.alpha_composite(바탕[i]); 바탕캐시[("원", i)] = 조각
    return 바탕캐시[("원", i)]


def 돌린바탕(i, a):
    배, 남 = divmod(round(a / 3) % 120, 30); 키 = (i, 남)
    if 키 not in 바탕캐시:
        바탕캐시[키] = 곁바탕(i).rotate(-남 * 3, Image.BILINEAR)
    im = 바탕캐시[키]
    return im.transpose((None, Image.ROTATE_270, Image.ROTATE_180, Image.ROTATE_90)[배]) if 배 else im


def 시계조각(i, g, 지금, 고화질):
    cx, cy, r, 시작, _ = 시계들[i]; h = 반[i]
    if i == 1:
        조각 = Image.new("RGBA", 바탕[1].size, (0, 0, 0, 0)); 붙(조각, 꼭지, 522 + g.용두x - (cx - h), 143 - (cy - h))
        if 곁장식[0]:
            곁장식[0](조각, h)
        조각.alpha_composite(바탕[1])
    else:
        조각 = 바탕[i].copy()
    세기 = g.빛세기(i, 지금)
    if 세기 > .02:
        층 = 약하게(빛판[i], 세기); 부채 = g.빛부채[i] if g.연출[i] else None
        if 부채 is not None:
            m = Image.new("L", 층.size, 0)
            if 부채 > 0:
                ImageDraw.Draw(m).pieslice((h - 300, h - 300, h + 300, h + 300), 시작 - 90, 시작 - 90 + 부채, fill=255)
            층.putalpha(ImageChops.multiply(층.getchannel("A"), m))
        조각.alpha_composite(층)
    if g.표시값(i) >= 80:
        등 = 등그림(i, .725 + .275 * math.cos(math.pi * 지금 / 1.2)); 붙(조각, 등, h - 등.width / 2, h + r * .62 - 등.height / 2)
    if i == 1 and g.붉음 > 0:
        조각.alpha_composite(붉은그림(g.용두표시, g.붉음), (h - 40, h - 40))
    손붙이기(조각, i, h, h, g.각[i] if g.각[i] is not None else g.목표(i), g.속[i], 고화질 or g.각[i] is None)
    return 조각


def 돌린자리(i, 각):
    cx, cy = 시계들[i][:2]; r = math.radians(각); dx = cx - 277; dy = cy - 139
    return 277 + dx * math.cos(r) - dy * math.sin(r), 139 + dx * math.sin(r) + dy * math.cos(r)


파동원본 = Image.new("RGBA", (500, 500), (0, 0, 0, 0))
ImageDraw.Draw(파동원본).ellipse((20, 20, 480, 480), outline=(90, 170, 255, 255), width=5)
파동원본 = 파동원본.filter(ImageFilter.GaussianBlur(7))
ImageDraw.Draw(파동원본).ellipse((20, 20, 480, 480), outline=(190, 228, 255, 255), width=2)


def 파동판(반지름, 세기):
    # 460픽셀 지름의 고리를 크기만 바꿔 쓴다
    크 = max(8, int(반지름 / 230 * 500))
    return 약하게(파동원본.resize((크, 크), Image.BILINEAR), 세기)


def 그림(g, 지금, 고화질=False):
    판 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); a = g.공전각; L = max(0, min(1, (abs(g.공전속) - 500) / 1500)) if a else 0
    for i in (0, 1):
        if 그늘[i]:
            x, y = 돌린자리(i, a); 붙(판, 그늘[i], x - 반[i], y - 반[i] + 위)
    for i in (0, 1):
        for 뒤, 세기 in ((.011, .16), (.0055, .34)):
            if L > 0:
                각 = a - g.공전속 * 뒤; x, y = 돌린자리(i, 각); im = 약하게(돌린바탕(i, 각), L * 세기); 붙(판, im, x - 반[i], y - 반[i] + 위)
    for i in (0, 1):
        x, y = 돌린자리(i, a)
        if abs(g.공전속) >= 300 and g.빛세기(i, 지금) <= .02 and g.표시값(i) < 80 and g.붉음 == 0:
            # 빠른 공전: 저장해 둔 회전 그림에 바늘만 얹는다
            붙(판, 돌린바탕(i, a), x - 반[i], y - 반[i] + 위)
            손붙이기(판, i, x, y + 위, (g.각[i] if g.각[i] is not None else g.목표(i)) + a, g.속[i] + g.공전속, False)
            continue
        조각 = 시계조각(i, g, 지금, 고화질 and not a)
        if a:
            조각 = 조각.rotate(-a, Image.BILINEAR)
        붙(판, 조각, x - 반[i], y - 반[i] + 위)
    붙(판, 액정그림(g.주간글, g.대화만, g.턴만), 188, 146 + 위 - 78 * (1 - g.액정))
    조각 = 시계조각(2, g, 지금, 고화질); 분 = g.표시분 if g.표시분 is not None else g.남은분
    시각 = 시각그림(f"{분 // 60}:{분 % 60:02d}", g.남은분 < 30 and not g.시간없음, 지금 % 1 < .5, g.빛세기(2, 지금) > .3); 붙(조각, 시각, 150 - 시각.width / 2, 150 + 29 - 시각.height / 2)
    붙(판, 조각, 277 - 150, 139 - 150 + 위)
    for i, t0 in g.파동:
        s = (지금 - t0) / .9; 비 = .82 + (1.75 - .82) * (1 - (1 - s) ** 3.4); 판넓이 = 파동판(시계들[i][2] * 비, .95 * (1 - s)); x, y = 돌린자리(i, a); 붙(판, 판넓이, x - 판넓이.width / 2, y - 판넓이.height / 2 + 위)
    if g.흔들 is not None:
        s = (지금 - g.흔들) / .34; dx = round(2.4 * math.sin(s * 17) * (1 - s)); dy = round(1.6 * math.cos(s * 19) * (1 - s)); 판 = ImageChops.offset(판, dx, dy)
    if g.낡음:
        판.putalpha(판.getchannel("A").point(lambda v: int(v * .55)))
    return 판
