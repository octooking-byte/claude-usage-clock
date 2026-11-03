# 크로노그래프 시계의 그림과 곧장 도킹 장면. 층을 얹는 도구는 dial.py를 그대로 쓴다.
import math
import numpy as np
import os
import time

from PIL import Image, ImageChops, ImageDraw

import dial
from chrono import 가x, 가y, 판표
from dial import H, W, 위, 돌린손, 등그림, 빨강, 손붙이기, 시각그림, 붉은그림, 붙, 액정그림, 액정틀, 약하게, 열기, 칠획, 파동판, 흰색
from morph import 사이, 이음

반면, 반작 = 205, 52              # 큰 판과 작은 다이얼 조각의 반지름. 용두와 그림자까지 들어간다
작은손, 큰손 = 3, 4


def 원판(이름):
    return 열기(os.path.join("..", "center", 이름), (420, 470))


def 자른(im, cx, cy, h):
    return im.crop((cx - h, cy - h, cx + h, cy + h))


def 둥글게(층, 반지름):
    # 빛이 판 바깥으로 새지 않게 원으로 자른다
    크 = 층.width * 3; c = 크 / 2; q = 반지름 * 3
    m = Image.new("L", (크, 크), 0); ImageDraw.Draw(m).ellipse((c - q, c - q, c + q, c + q), fill=255)
    층.putalpha(ImageChops.multiply(층.getchannel("A"), m.resize(층.size, Image.LANCZOS)))
    return 층


def 몸과그늘(면, 반지름=168):
    return dial.몸과그늘(면, 반지름)


바탕면, 그늘면 = 몸과그늘(자른(원판("base.png"), 210, 200, 반면))
작은판 = [자른(원판("sub0.png"), 155, 191, 반작), 자른(원판("sub1.png"), 265, 191, 반작)]
빛면 = dial.파랑줄이기(둥글게(자른(원판("glow.png"), 210, 200, 반면), 155))  # 시계 하나의 빛은 검은 시계도 파랑 45%다
빛작 = [dial.파랑줄이기(둥글게(자른(원판("gsub0.png"), 155, 191, 반작), 44), 반경=2), dial.파랑줄이기(둥글게(자른(원판("gsub1.png"), 265, 191, 반작), 44), 반경=2)]
액정틀c = 열기("panelc.png", (178, 208))
꼭지c = [열기(f"crownc{n}.png", (27, 40)) for n in range(5)]
줄기색 = [tuple(round(이음(a, b, 사이(0, 1, t))) for a, b in zip(앞, 뒤)) + (255,) for 앞, 뒤, t in
         [((51, 53, 58), (212, 215, 220), n / 4) for n in range(5)] + [((212, 215, 220), (133, 136, 142), n / 2.4) for n in range(1, 3)] + [((133, 136, 142), (35, 37, 41), n / 3.4) for n in range(1, 4)]]
돌림면 = {}; 돌림작 = {}; 맞춤캐시 = {}; 회전손캐시 = {}
# 기둥: 위는 검은 시계와 흰 시계 전환, 아래는 굴려서 크기 조절. 줄은 아래 기둥의 회전각이다
기 = dict(밝음=False, 줄=860.0, 눌=False, 띠=0.0)
기둥판 = Image.open(os.path.join(dial.여기, "pusher.png")).convert("RGBA")
기둥캐시 = {}; 면캐시 = [None, None]; 흰세트 = [None]
띠면 = 몸과그늘(자른(원판("base_ring.png"), 210, 200, 반면))[0]
검세트 = dict(바=list(dial.바탕), 면=바탕면, 늘=그늘면, 띠=띠면, 작=list(작은판), 손1=list(dial.손1), 손3=list(dial.손3), 빛=list(dial.빛판), 빛면=빛면, 빛작=list(빛작))


def 기둥그림(각도, 줄):
    키 = (각도, None if 줄 is None else round(줄 / 3))
    if 키 not in 기둥캐시:
        if len(기둥캐시) > 60:
            기둥캐시.clear()
        im = 기둥판.copy()
        if 줄 is not None:
            d = ImageDraw.Draw(im)
            for n in range(8):
                a = math.radians(줄 + n * 45); 앞 = math.cos(a)
                if 앞 > .05:
                    x = 18 + 3 * (7.5 + 7 * math.sin(a)); w = max(1.5, 7.2 * 앞)
                    d.rectangle((x, 21, x + w, 68), fill=(0, 0, 0, int(174 * (.3 + .7 * 앞)))); d.rectangle((x + w, 21, x + w + 2, 68), fill=(255, 255, 255, int(107 * (.3 + .7 * 앞))))
        기둥캐시[키] = im.resize((27, 38), Image.LANCZOS).rotate(-각도, Image.BICUBIC, expand=True)
    return 기둥캐시[키]


def 기둥붙(판, cx, cy, r, 각도, 줄=None, 눌=0):
    im = 기둥그림(각도, 줄); a = math.radians(각도)
    붙(판, im, cx + (r - 눌) * math.sin(a) - im.width / 2, cy - (r - 눌) * math.cos(a) - im.height / 2)


def 기둥들(면):
    기둥붙(면, 반면, 반면, 178, 60, None, 3.5 if 기["눌"] else 0); 기둥붙(면, 반면, 반면, 178, 120, 기["줄"])


def 곁장식(조각, h):
    기둥붙(조각, h, h, 94, 60, None, 3.5 if 기["눌"] else 0); 기둥붙(조각, h, h, 94, 120, 기["줄"])


dial.곁장식[0] = 곁장식


def 바닥면():
    키 = (round(기["줄"] / 3), 기["눌"], 기["밝음"])
    if 면캐시[0] != 키:
        면 = Image.new("RGBA", 바탕면.size, (0, 0, 0, 0)); 기둥들(면); 붙(면, 꼭지c[0], 375 - 6, 191 - 6); 면.alpha_composite(바탕면); 면캐시[:] = [키, 면]
    return 면캐시[1]


def 어둡게(im):
    r, g, b, a = im.split(); 표 = [int(v * .3) for v in range(256)]
    return Image.merge("RGBA", (r.point(표), g.point(표), b.point(표), a))


def 흰재료():
    if 흰세트[0] is None:
        흰세트[0] = dict(바=[열기(f"base{i}_lt.png", (554, 296)).crop(dial.칸(i)) for i in range(3)], 면=몸과그늘(자른(원판("base_lt.png"), 210, 200, 반면))[0], 늘=몸과그늘(자른(원판("base_lt.png"), 210, 200, 반면))[1], 띠=몸과그늘(자른(원판("base_lt_ring.png"), 210, 200, 반면))[0],
                       작=[자른(원판("sub0_lt.png"), 155, 191, 반작), 자른(원판("sub1_lt.png"), 265, 191, 반작)], 손1=[어둡게(h) for h in 검세트["손1"]], 손3=[어둡게(h) for h in 검세트["손3"]], 빛=[dial.파랑줄이기(x) for x in 검세트["빛"]], 빛면=dial.테글자빼기(검세트["빛면"], 반면, 반면, 131), 빛작=검세트["빛작"])


def 테마(밝음):
    # 위 기둥: 재료를 통째로 바꾸고 캐시를 비운다. 흰 재료는 처음 누를 때 읽는다
    global 바탕면, 그늘면, 빛면, 띠면
    if 밝음:
        흰재료()
    t = 흰세트[0] if 밝음 else 검세트
    dial.바탕[:] = t["바"]; dial.곁나누기(); 바탕면 = t["면"]; 그늘면 = t["늘"]; 띠면 = t["띠"]; 작은판[:] = t["작"]; dial.손1[:] = t["손1"]; dial.손3[:] = t["손3"]; dial.어두운글[0] = 밝음; 기["밝음"] = 밝음; dial.빛판[:] = t["빛"]; 빛면 = t["빛면"]; 빛작[:] = t["빛작"]
    for c in (dial.바탕캐시, dial.돌림캐시, dial.손캐시, 돌림면, 돌림작, 맞춤캐시, 회전손캐시):
        c.clear()
    면캐시[0] = None; 옛곁만들기()


def 용두얹기(x):
    # 빠진 만큼 줄기가 드러나고 홈이 돌아간다
    면 = Image.new("RGBA", 바탕면.size, (0, 0, 0, 0)); 길이 = round(10 + x); 기둥들(면)
    줄기 = Image.new("RGBA", (1, 10)); 줄기.putdata(줄기색)
    붙(면, 줄기.resize((길이, 10), Image.NEAREST), 366, 200); 붙(면, 꼭지c[int(x * 2.2) % 5], 375 + x - 6, 191 - 6); 면.alpha_composite(바탕면)
    return 면


def 빛층(층, 세기, 부채, 시작, h):
    층 = 약하게(층, 세기)
    if 부채 is not None:
        m = Image.new("L", 층.size, 0)
        if 부채 > 0:
            ImageDraw.Draw(m).pieslice((h - 300, h - 300, h + 300, h + 300), 시작 - 90, 시작 - 90 + 부채, fill=255)
        층.putalpha(ImageChops.multiply(층.getchannel("A"), m))
    return 층


def 깜빡(지금):
    return .725 + .275 * math.cos(math.pi * 지금 / 1.2)


def 작은조각(g, i, 지금, 고화질):
    h = 반작; 조각 = 작은판[i].copy(); 세기 = g.빛세기(i, 지금)
    if 세기 > .02:
        조각.alpha_composite(빛층(빛작[i], 세기, g.빛부채[i] if g.연출[i] else None, 판표[i][3], h))
    if g.표시값(i) >= 80:
        등 = 등그림(i, 깜빡(지금), 54.5); 붙(조각, 등, h - 등.width / 2, h + 44 * .56 - 등.height / 2)
    if i == 1 and g.붉음 > 0:
        붉 = 붉은그림(g.용두표시, g.붉음).resize((85, 85), Image.BILINEAR); 붙(조각, 붉, h - 42.5, h - 42.5)
    손붙이기(조각, 작은손, h, h, g.각[i] if g.각[i] is not None else g.목표(i), g.속[i], 고화질 or g.각[i] is None)
    return 조각


def 돈자리(i, 각):
    cx, cy = 판표[i][:2]; r = math.radians(각); dx = cx - 가x; dy = cy - 가y
    return dx * math.cos(r) - dy * math.sin(r), dx * math.sin(r) + dy * math.cos(r)


네모 = (None, Image.ROTATE_270, Image.ROTATE_180, Image.ROTATE_90)


def 돌린작(i, a):
    # 90도까지만 저장하고 나머지는 뒤집는다
    배, 남 = divmod(round(a / 3) % 120, 30); 키 = (i, 남)
    if 키 not in 돌림작:
        돌림작[키] = 작은판[i].rotate(-남 * 3, Image.BILINEAR)
    return 돌림작[키].transpose(네모[배]) if 배 else 돌림작[키]


def 시각글(g):
    분 = g.표시분 if g.표시분 is not None else g.남은분
    return f"{분 // 60}:{분 % 60:02d}", g.남은분 < 30 and not g.시간없음


def 면그림(g, 지금, 고화질):
    면 = 용두얹기(g.용두x) if g.용두x > .05 else 바닥면().copy(); 세기 = g.빛세기(2, 지금)
    if 기["띠"] > .02:
        면.alpha_composite(약하게(띠면, 기["띠"]))  # 용두로 색을 고르는 동안만 켜지는 오른쪽 빛
    if 세기 > .02:
        면.alpha_composite(빛층(빛면, 세기, g.빛부채[2] if g.연출[2] else None, -135, 반면))
    if g.표시값(2) >= 80:
        등 = 등그림(2, 깜빡(지금), 161); 붙(면, 등, 반면 - 등.width / 2, 반면 + 100 - 등.height / 2)
    a = g.공전각; L = max(0, min(1, (abs(g.공전속) - 500) / 1500)) if a else 0
    for i in (0, 1):
        if L > 0:
            for 뒤, 세기 in ((.011, .16), (.0055, .34)):
                각 = a - g.공전속 * 뒤; x, y = 돈자리(i, 각); im = 약하게(돌린작(i, 각), L * 세기); 붙(면, im, 반면 + x - 반작, 반면 + y - 반작)
    for i in (0, 1):
        x, y = 돈자리(i, a)
        if abs(g.공전속) >= 300 and g.빛세기(i, 지금) <= .02 and g.표시값(i) < 80 and g.붉음 == 0:
            붙(면, 돌린작(i, a), 반면 + x - 반작, 반면 + y - 반작)
            손붙이기(면, 작은손, 반면 + x, 반면 + y, (g.각[i] if g.각[i] is not None else g.목표(i)) + a, g.속[i] + g.공전속, False)
            continue
        조각 = 작은조각(g, i, 지금, 고화질 and not a)
        if a:
            조각 = 조각.rotate(-a, Image.BILINEAR)
        붙(면, 조각, 반면 + x - 반작, 반면 + y - 반작)
    글, 임박 = 시각글(g); 시각 = 칠획(글, 19, 빨강 if 임박 else 흰색, 지금 % 1 < .5); 붙(면, 시각, 반면 - 시각.width / 2, 반면 + 74 - 시각.height / 2)
    손붙이기(면, 큰손, 반면, 반면, g.각[2] if g.각[2] is not None else g.목표(2), g.속[2], 고화질 or g.각[2] is None)
    return 면


def 정지면():
    # 빠르게 돌 때 쓰는 바늘과 숫자 없는 판. 숫자는 그때그때 얹어 이 캐시를 버리지 않는다
    면 = 바닥면().copy()
    for i in (0, 1):
        x, y = 돈자리(i, 0); 붙(면, 작은판[i], 반면 + x - 반작, 반면 + y - 반작)
    return 면


def 돌린면(a):
    배, 남 = divmod(round(a / 3) % 120, 30)
    if "판" not in 돌림면:
        돌림면["판"] = 정지면()
    if 남 not in 돌림면:
        돌림면[남] = 돌림면["판"].rotate(-남 * 3, Image.BILINEAR)
    return 돌림면[남].transpose(네모[배]) if 배 else 돌림면[남]


def 데우기(살았나):
    # 뒤에서 스핀 그림을 미리 만든다. 첫 바퀴가 버벅이지 않게 하는 일이고, 살았나()가 거짓이면 멈춘다
    흰재료()  # 처음 흰 시계로 바꿀 때 멈칫하지 않게 미리 읽는다
    일 = [lambda a=a: 돌린면(a * 3) for a in range(30)]
    일 += [lambda i=i, a=a: 돌린작(i, a * 3) for i in (0, 1) for a in range(30)]
    일 += [lambda i=i, a=a: dial.돌린바탕(i, a * 3) for i in (0, 1) for a in range(30)]
    일 += [lambda i=i, s=s, a=a: dial.돌린손(i, a * 2, s, True) for i in (큰손, 작은손, 0, 1, 2) for s in (True, False) for a in range(45)]
    for 할일 in 일:
        if not 살았나():
            return
        할일(); time.sleep(.001)


def 그림(g, 지금, 고화질=False):
    판 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); a = g.전체각; 공 = g.공전각; cy = 가y + 위
    붙(판, 액정그림(g.주간글, g.대화만, g.턴만, 액정틀c, 125), 188, 186 + 위 - 78 * (1 - g.액정))
    붙(판, 그늘면, 가x - 반면, cy - 반면)
    빠름 = abs(g.전체속) >= 300 and g.붉음 == 0 and not any(g.연출) and all(g.빛세기(i, 지금) <= .02 for i in range(3)) and g.용두x < .05 and all(g.표시값(i) < 80 for i in range(3))
    if 빠름:
        글, 임박 = 시각글(g); L = max(0, min(1, (abs(g.전체속) - 500) / 1500))
        if L > 0:
            for 뒤, 세기 in ((.011, .14), (.0055, .3)):
                붙(판, 약하게(돌린면(a - g.전체속 * 뒤), L * 세기), 가x - 반면, cy - 반면)
        붙(판, 돌린면(a), 가x - 반면, cy - 반면)
        시각 = 칠획(글, 19, 빨강 if 임박 else 흰색, True).rotate(-a, Image.BILINEAR, expand=True); 라 = math.radians(a); 붙(판, 시각, 가x - 74 * math.sin(라) - 시각.width / 2, cy + 74 * math.cos(라) - 시각.height / 2)
        for i in (0, 1):
            x, y = 돈자리(i, a + 공); 손붙이기(판, 작은손, 가x + x, cy + y, (g.각[i] if g.각[i] is not None else g.목표(i)) + a + 공, g.속[i] + g.전체속, False)
        손붙이기(판, 큰손, 가x, cy, (g.각[2] if g.각[2] is not None else g.목표(2)) + a, g.속[2] + g.전체속, False)
    else:
        면 = 면그림(g, 지금, 고화질 and not a)
        if a:
            면 = 면.rotate(-a, Image.BILINEAR)
        붙(판, 면, 가x - 반면, cy - 반면)
    for i, t0 in g.파동:
        s = (지금 - t0) / .9; 비 = .82 + ((1.28 if i == 2 else 2.1) - .82) * (1 - (1 - s) ** 3.4); im = 파동판(판표[i][2] * 비, .95 * (1 - s))
        x, y = (0, 0) if i == 2 else 돈자리(i, 공 + a); 붙(판, im, 가x + x - im.width / 2, cy + y - im.height / 2)
    if g.흔들 is not None:
        s = (지금 - g.흔들) / .34; dx = round(2.4 * math.sin(s * 17) * (1 - s)); dy = round(1.6 * math.cos(s * 19) * (1 - s)); 판 = ImageChops.offset(판, dx, dy)
    if g.낡음:
        판.putalpha(판.getchannel("A").point(lambda v: int(v * .55)))
    return 판


# 곧장 도킹 장면. 크기별로 한 번 만든 그림을 다시 쓰고, 양 끝 시계의 재료를 그대로 쓴다
dial.곁나누기()
옛곁 = []


def 옛곁만들기():
    옛곁.clear()
    for i in (0, 1):
        조각 = Image.new("RGBA", dial.바탕[i].size, (0, 0, 0, 0))
        if i == 1:
            붙(조각, dial.꼭지, 522 - 330, 143 - 34); 곁장식(조각, 120)
        조각.alpha_composite(dial.그늘[i]); 조각.alpha_composite(dial.바탕[i]); 옛곁.append(조각)


옛곁만들기()
그늘격 = np.mgrid[0:120, 0:120].astype(np.float32); 그늘거리 = np.hypot(그늘격[0] - 59.5, 그늘격[1] - 59.5) / 60
그늘원 = Image.fromarray((158 * np.clip((1 - 그늘거리) / .38, 0, 1)).astype(np.uint8), "L")  # 가장자리까지 원으로 사라진다. 시안의 .곁그늘과 같다
그늘판 = Image.new("RGBA", (120, 120), (0, 0, 0, 255)); 그늘판.putalpha(그늘원)


def 맞춤(이름, 원본, 크기):
    키 = (이름, 크기)
    if 키 not in 맞춤캐시:
        맞춤캐시[키] = 원본.resize((크기, 크기), Image.BILINEAR)
    return 맞춤캐시[키]


def 회전손(번호, 각, 그림자):
    키 = (번호, round(각, 1), 그림자)
    if 키 not in 회전손캐시:
        if len(회전손캐시) > 80:
            회전손캐시.clear()
        회전손캐시[키] = 돌린손(번호, round(각, 1), 그림자, False)
    return 회전손캐시[키]


def 손얹기(판, 번호, cx, cy, 각, 비):
    for 그림자, ax, ay in ((True, 2, 3), (False, 0, 0)):
        im, x, y = 회전손(번호, 각, 그림자); 크 = (max(1, round(im.width * 비)), max(1, round(im.height * 비)))
        붙(판, im.resize(크, Image.BILINEAR), cx + x * 비 + ax, cy + y * 비 + ay)


def 곁그리기(판, 세, 크, c, i, 공, cy, 지금):
    라 = math.radians(공); cx = 가x + c["x"] * math.cos(라) - c["y"] * math.sin(라); y = cy + c["x"] * math.sin(라) + c["y"] * math.cos(라); R = c["R"]; 섞 = c["섞"]
    if c["뜸"] > .02:
        크기 = max(8, round(120 * R / 46)); 붙(판, 약하게(맞춤("그늘", 그늘판, 크기), c["뜸"] * .75), cx - 크기 / 2, y + 5 + 7 * c["뜸"] - 크기 / 2)
    옛진하기 = 1 - 사이(.55, 1, 섞)
    if 옛진하기 > .01:
        크기 = round(240 * R / 86); im = 맞춤(f"옛곁{i}", 옛곁[i], 크기); im = im if 옛진하기 > .98 else 약하게(im, 옛진하기); im = im.rotate(-공, Image.BILINEAR) if abs(공) > .5 else im; 붙(판, im, cx - 크기 / 2, y - 크기 / 2)
    if 섞 > .01:
        크기 = round(2 * 반작 * R / 44); im = 맞춤(f"새곁{i}", 작은판[i], 크기); im = im if 섞 > .98 else 약하게(im, 섞); im = im.rotate(-공, Image.BILINEAR) if abs(공) > .5 else im; 붙(판, im, cx - 크기 / 2, y - 크기 / 2)
    비 = R / 이음(86, 44, 섞)
    if 크.표시값(i) >= 80:
        등 = 등그림(i, 깜빡(지금), round(이음(86, 54.5, 섞) * 비 / 4) * 4); 붙(판, 등, cx - 등.width / 2, y + 이음(53, 24.6, 섞) * 비 - 등.height / 2)
    옛각 = 세.각[i] if 세.각[i] is not None else 세.목표(i); 새각 = 크.각[i] if 크.각[i] is not None else 크.목표(i)
    손얹기(판, i, cx, y, 이음(옛각, 새각, 섞) + 공, R / 86)


def 합체그림(세, 크, q, 지금, 흔):
    판 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); k = q["k"]; 섞 = q["섞"]; cy = 가y + 위; 공 = q["공"]
    for i in (0, 1):
        if not q["곁"][i]["위"]:
            곁그리기(판, 세, 크, q["곁"][i], i, 공, cy, 지금)
    붙(판, 액정그림(크.주간글, 크.대화만, 크.턴만, 액정틀c, 125) if 섞 > .5 else 액정그림(세.주간글, 세.대화만, 세.턴만), 188, 146 + 위 - 78 + (k - 130))
    if q["용"] > .01:
        붙(판, 꼭지c[0], 가x + (170 + 이음(-20, 0, q["용"]) - 6) * k / 170, cy + (-14 - 6) * k / 170)
        기둥붙(판, 가x, cy, 178 * k / 170 - 18 * (1 - q["용"]), 60); 기둥붙(판, 가x, cy, 178 * k / 170 - 18 * (1 - q["용"]), 120, 기["줄"])
    옛진하기 = 1 - 사이(.55, 1, 섞)
    if 옛진하기 > .01:
        크기 = round(300 * k / 130); im = 맞춤("옛큰", dial.바탕[2], 크기); im = im if 옛진하기 > .98 else 약하게(im, 옛진하기); 붙(판, im, 가x - 크기 / 2, cy - 크기 / 2)
    if 섞 > .01:
        크기 = round(2 * 반면 * k / 170); im = 맞춤("새늘", 그늘면, 크기); im = im if 섞 > .98 else 약하게(im, 섞); 붙(판, im, 가x - 크기 / 2, cy - 크기 / 2)
        im = 맞춤("새큰", 바탕면, 크기); im = im if 섞 > .98 else 약하게(im, 섞); 붙(판, im, 가x - 크기 / 2, cy - 크기 / 2)
    판비 = k / 이음(130, 170, 섞)
    if 크.표시값(2) >= 80:
        등 = 등그림(2, 깜빡(지금), round(이음(130, 161, 섞) * 판비 / 4) * 4); 붙(판, 등, 가x - 등.width / 2, cy + 이음(80.6, 100, 섞) * 판비 - 등.height / 2)
    글, 임박 = 시각글(크); 콜론 = 지금 % 1 < .5; 시y = cy + 이음(29, 74, 섞) * 판비
    if 섞 < .99:
        im = 약하게(시각그림(글, 임박, 콜론), 1 - 섞); 붙(판, im, 가x - im.width / 2, 시y - im.height / 2)
    if 섞 > .01:
        im = 약하게(칠획(글, 19, 빨강 if 임박 else 흰색, 콜론), 섞); 붙(판, im, 가x - im.width / 2, 시y - im.height / 2)
    for i in (0, 1):
        if q["곁"][i]["위"]:
            곁그리기(판, 세, 크, q["곁"][i], i, 공, cy, 지금)
    손얹기(판, 큰손, 가x, cy, 크.각[2] if 크.각[2] is not None else 크.목표(2), k / 170)
    if abs(q["회"]) > .3:
        판 = 판.rotate(-q["회"], Image.BILINEAR, center=(가x, cy))
    if 흔:
        판 = ImageChops.offset(판, 0, 흔)
    if 크.낡음:
        판.putalpha(판.getchannel("A").point(lambda v: int(v * .55)))
    return 판
