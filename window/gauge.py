# 토큰 계기판의 동작 규칙. 그림과 창을 모르는 순수 계산이라 창 없이 시험할 수 있다.
# 손짓: 안쪽 누르기=램프, 안쪽 돌리기=태엽, 짧게 튕기기=스핀, 시계 위 휠=바늘 스핀, 좌우 테=공전, 가운데 테=창 이동, 용두=대화 초기화, 초승달=액정
import math

# 주간, 대화, 5시간 순서: 중심 x, y, 반지름, 시작각, 쓸각
시계들 = ((104, 154, 86, -150, 180), (450, 154, 86, -30, 180), (277, 139, 130, -135, 270))
바늘감속 = (70, .38)
공전감속 = (45, .3)
공전상한 = 7200  # 피젯스피너(공전과 시계 하나 통째 돌리기)의 최고 속도. 휠과 같은 초당 20바퀴
밀기게인 = 16
태엽최대 = 4
# 휠은 태엽처럼 바늘에 힘(토크)을 건다. 한 칸이 미는 양(도/초)과 그 힘이 걸리는 시간(초). 굴릴수록 점점 빨라져 상한(초당 20바퀴)까지 간다
휠힘 = 520
힘시간 = .18
휠상한 = 7200
# 반대 칸은 돌던 쪽을 거스르는 힘이다. 더 오래 걸쳐 걸리고, 빠를수록 한 칸이 덜 먹혀 저항이 크다(최고 속도에서 한 칸의 55%)
역힘시간 = .28
역저항 = .45
# 손을 떼고 이 속도 아래로 내려오면 튕길 때와 같은 감속으로 지금 값에 내려앉는다
넘김속도 = 700
액정길이 = 78
초기화초 = 6
요청제한 = 120
대기제한 = 15 * 60  # 모드가 압축을 줄 세웠다고 알린 뒤에는 턴이 길어도 이만큼 기다린다


def 잘라(v, a, b):
    return max(a, min(b, v))


def 짧게(d):
    return (d + 180) % 360 - 180


def 부드럽게(s):
    return 4 * s * s * s if s < .5 else 1 - (-2 * s + 2) ** 3 / 2


def 거리(w, a, b):
    return w / b - a / (b * b) * math.log(1 + b * w / a)


def 착지(현재, 기준, 속도, 감속, 지금):
    # 피젯스피너 감속: 놓는 순간 멈출 자리까지의 거리를 풀어 마찰만 살짝 바꾼다. 끝에 끌어당기는 보정이 없다
    a, b = 감속; w = abs(속도)
    쪽 = 1 if 속도 > 0 else -1
    if w < 40:
        쪽 = 1 if (기준 - 현재) % 360 <= 180 else -1
    기본 = 0 if w < 40 else 거리(w, a, b)
    D = ((기준 - 현재) * 쪽) % 360
    while D < 기본:
        D += 360
    if D < .3:
        return None
    w0, k = w, 1.0
    if 기본 / D >= .5:
        k = 기본 / D
    else:
        낮, 높 = 0.0, 8000.0
        for _ in range(40):
            w0 = (낮 + 높) / 2
            if 거리(w0, a, b) < D:
                낮 = w0
            else:
                높 = w0
    return dict(t0=지금, 각0=현재, 쪽=쪽, w0=w0, k=k, a=a, b=b, 끝=math.log(1 + b * w0 / a) / (k * b))


def 어디(s, 지금):
    t = min(s["끝"], 지금 - s["t0"]); e = math.exp(-s["k"] * s["b"] * t); c = s["w0"] + s["a"] / s["b"]
    return s["각0"] + s["쪽"] * (c * (1 - e) / (s["k"] * s["b"]) - s["a"] / s["b"] * t), s["쪽"] * max(0, c * e - s["a"] / s["b"]), t >= s["끝"]


def 휠적분(r, 지금):
    # 휠 바늘의 운동을 지금까지 잘게 나눠 쌓는다: 걸린 힘(칸마다 종 모양으로 퍼짐) − 베어링 마찰. 끝났는가 = 힘이 다 걸렸고 넘김속도 아래
    a, b = 바늘감속
    t = r["앞"]
    while t < 지금 - 1e-9:
        dt = min(1 / 240, 지금 - t); 가운데 = t + dt / 2
        힘 = 0.0
        for t0, 양, T in r["힘"]:
            u = (가운데 - t0) / T
            if 0 <= u <= 1:
                힘 += 양 / T * 6 * u * (1 - u)
        w = r["w"]; 마찰 = math.copysign(a + b * abs(w), w) if w else 0.0
        새 = w + (힘 - 마찰) * dt
        if 힘 == 0 and w and 새 * w < 0:
            새 = 0.0  # 마찰만으로는 거꾸로 돌지 않는다
        r["w"] = max(-휠상한, min(휠상한, 새)); r["각"] += (w + r["w"]) / 2 * dt; t += dt
    r["앞"] = 지금; r["힘"] = [p for p in r["힘"] if 지금 < p[0] + p[2]]
    return r["각"], r["w"], not r["힘"] and abs(r["w"]) < 넘김속도


class 계기:
    판 = 시계들

    def __init__(s, 요청=None):
        s.요청 = 요청 or (lambda: None)
        s.값 = [0.0, 0.0, 0.0]; s.덮개 = None; s.요청시각 = 0; s.대기 = False; s.처음 = True
        s.각 = [None, None, None]; s.속 = [0.0, 0.0, 0.0]; s.회전 = [None, None, None]; s.연출 = [None, None, None]
        s.누름 = None; s.공전각 = 0.0; s.공전속 = 0.0; s.공전회전 = None
        s.상태빛 = 0.0  # 클로드가 일하는 중이거나 사용자를 기다릴 때 메인 바늘(2번)에 드는 빛. 움직임으로 치지 않는다
        s.백빛 = 0.0  # 백그라운드 작업이 도는 동안 CHAT 바늘(1번)에 드는 빛
        s.빛값 = [0.0, 0.0, 0.0]; s.빛목표 = [0.0, 0.0, 0.0]; s.빛부채 = [None, None, None]; s.번쩍 = []; s.파동 = []; s.흔들 = None
        s.앞클릭 = -1e9; s.앞시각 = None
        s.액정 = 0.0; s.액정목표 = 0.0; s.액정끌기 = False
        s.용두진행 = False; s.용두취소 = False; s.용두가득 = False; s.용두표시 = 0.0; s.용두시작 = 0.0; s.용두x = 0.0; s.붉음 = 0.0
        s.남은분 = 0; s.시간없음 = True; s.표시분 = None; s.주간글 = ("0", "00"); s.대화만 = 0.0; s.턴만 = 0.0; s.낡음 = False

    def 표시값(s, i):
        return s.덮개 if i == 1 and s.덮개 is not None else s.값[i]

    def 목표(s, i):
        return s.판[i][3] + s.판[i][4] * 잘라(s.표시값(i), 0, 100) / 100

    def 값넣기(s, 주간, 대화, 다섯, 지금):
        새값 = (주간, 대화, 다섯)
        for i in range(3):
            옛 = s.값[i]; 옛목표 = s.목표(i); s.값[i] = 새값[i]
            if s.처음:
                continue
            if i == 1 and s.덮개 is not None:
                if 새값[1] <= 옛 - 10:
                    s.덮개 = None
                    if s.각[1] is None and s.회전[1] is None:
                        s.각[1] = 옛목표
                continue
            if 옛 - 새값[i] >= 10:
                if i == 1:
                    s.대화연출(지금, 옛목표)
                else:
                    s.초기화연출(i, 지금, 옛목표)
            elif s.각[i] is None and s.회전[i] is None and not s.연출[i] and abs(s.목표(i) - 옛목표) > .2:
                s.각[i] = 옛목표
        s.처음 = False

    def 요청실패(s):
        # 압축이 끝났거나 실패하면 덮개를 내린다. 바늘은 순간이동하지 않고 지금 자리에서 간다
        옛목표 = s.목표(1); s.덮개 = None; s.대기 = False
        if s.각[1] is None and s.회전[1] is None:
            s.각[1] = 옛목표

    def 초기화연출(s, i, 지금, 옛목표=None):
        현재 = s.각[i] if s.각[i] is not None else (옛목표 if 옛목표 is not None else s.목표(i))
        s.회전[i] = None; s.속[i] = 0.0
        s.연출[i] = dict(t0=지금, 시작=s.판[i][3] + 짧게(현재 - s.판[i][3]), 정점=False, 빛만=False)

    def 대화연출(s, 지금, 옛목표=None):
        # 푸른 빛 연출은 다른 초기화와 같고, 바늘만 되감기 방향으로 빙글빙글 돌다가 새 값에 멈춘다
        현재 = s.각[1] if s.각[1] is not None else (옛목표 if 옛목표 is not None else s.목표(1))
        s.각[1] = 현재; s.회전[1] = 착지(현재, s.목표(1), -2200, 바늘감속, 지금)
        s.연출[1] = dict(t0=지금, 시작=0, 정점=False, 빛만=True)

    def 제자리(s, i, x, y):
        if i == 2 or not s.공전각:
            return x, y
        r = -math.radians(s.공전각); dx = x - 277; dy = y - 139
        return 277 + dx * math.cos(r) - dy * math.sin(r), 139 + dx * math.sin(r) + dy * math.cos(r)

    def 액정안(s, x, y):
        dx = x - 277
        if abs(dx) > 85:
            return False
        아래 = 272 + 액정길이 * s.액정 - 32 + 32 * math.sqrt(1 - dx * dx / 7225)
        return y < 아래 + 10 and math.hypot(dx, y - 139) >= 130

    def 찾기(s, x, y):
        중심 = math.hypot(x - 277, y - 139); yx, yy = s.제자리(1, x, y)
        if 528 < yx < 560 and abs(yy - 154) < 15 and 중심 >= 130:
            return "용두", 1
        if s.공전회전 and abs(s.공전속) > 200 and 130 <= 중심 < 268:
            return "공전", 0
        if s.액정안(x, y):
            return "액정", 2
        if 중심 < 130:
            return ("바늘", 2) if 중심 < 110 else ("창", 2)
        for i in (0, 1):
            px, py = s.제자리(i, x, y); cx, cy, r = s.판[i][:3]; d = math.hypot(px - cx, py - cy)
            if d < r * .847:
                return "바늘", i
            if d < r * 1.04:
                return "공전", i
        return None

    def 각재기(s, i, x, y):
        px, py = s.제자리(i, x, y)
        return math.degrees(math.atan2(px - s.판[i][0], -(py - s.판[i][1])))

    @staticmethod
    def 공전재기(x, y):
        return math.degrees(math.atan2(x - 277, -(y - 139)))

    def 눌림(s, x, y, 지금):
        곳 = s.찾기(x, y)
        if not 곳:
            return None
        종류, i = 곳
        if i == 1 and 종류 != "공전" and (s.용두진행 or s.용두취소):
            return None
        if 종류 == "바늘" and s.연출[i] and not s.연출[i]["빛만"]:
            return None
        if 종류 == "공전":
            밀기 = bool(s.공전회전) and abs(s.공전속) > 200; s.공전회전 = None
            if not 밀기:
                s.공전속 = 0.0
            s.누름 = dict(종류=종류, i=i, t0=지금, 전각=s.공전재기(x, y), 전시=지금, 속도=0.0, 밀기=밀기, 민시각=-1e9)
        elif 종류 == "창":
            s.누름 = dict(종류=종류)
        elif 종류 == "용두":
            s.누름 = dict(종류=종류, x=x, 당김=False, 끝=False)
        elif 종류 == "액정":
            s.누름 = dict(종류=종류, y=y, 비0=s.액정, 움직임=0.0)
        else:
            s.회전[i] = None; s.속[i] = 0.0
            if s.각[i] is None:
                s.각[i] = s.목표(i)
            s.누름 = dict(종류=종류, i=i, t0=지금, x=x, y=y, 전각=s.각재기(i, x, y), 전시=지금, 속도=0.0, 끌림=False, 시작각=s.각[i], 감김=0.0, u=0.0, 표시=0)
            s.빛목표[i] = 1.0
        return 종류

    def 끌림(s, x, y, 지금):
        n = s.누름
        if not n or n["종류"] == "창":
            return
        if n["종류"] == "액정":
            n["움직임"] = max(n["움직임"], abs(y - n["y"]))
            if n["움직임"] > 4:
                s.액정끌기 = True; s.액정 = s.액정목표 = 잘라(n["비0"] + (y - n["y"]) / 액정길이, 0, 1)
            return
        if n["종류"] == "용두":
            if x - n["x"] > 4:
                n["당김"] = True
            return
        dt = max(.004, 지금 - n["전시"])
        if n["종류"] == "공전":
            새 = s.공전재기(x, y); 차 = 짧게(새 - n["전각"]); n["전각"] = 새; n["전시"] = 지금
            if n["밀기"]:
                # 도는 중에 누르고 있으면 멈추고, 쓸면 그만큼 속도가 더해진다. 상한이 있다
                s.공전속 = 잘라(s.공전속 + 차 * 밀기게인, -공전상한, 공전상한); n["민시각"] = 지금
            else:
                s.공전각 += 차; n["속도"] = n["속도"] * .6 + 차 / dt * .4; s.공전속 = n["속도"]
            return
        i = n["i"]
        if math.hypot(x - n["x"], y - n["y"]) > 5:
            n["끌림"] = True
        if not n["끌림"]:
            return
        새 = s.각재기(i, x, y); 차 = 짧게(새 - n["전각"]); 한계 = 360 * 태엽최대
        n["감김"] = 잘라(n["감김"] + 차, -한계, 한계); n["속도"] = n["속도"] * .6 + 차 / dt * .4; n["전각"] = 새; n["전시"] = 지금
        # 태엽: 처음엔 손을 그대로 따라오고, 감을수록 덜 따라온다. 3도씩 톱니처럼 걸린다
        u = abs(n["감김"]) / 한계; n["u"] = u
        n["표시"] = math.copysign(1, n["감김"]) * round(한계 * (u - .4 * u * u) / 3) * 3

    def 놓임(s, 지금):
        n = s.누름; s.누름 = None
        if not n or n["종류"] == "창":
            return
        if n["종류"] == "액정":
            s.액정끌기 = False
            if n["움직임"] > 4:
                s.액정목표 = 1.0 if s.액정 > (.3 if n["비0"] < .5 else .7) else 0.0
            else:
                s.액정목표 = 1.0 if n["비0"] < .5 else 0.0
            return
        if n["종류"] == "용두":
            if s.용두진행:
                s.용두진행 = False
                if s.용두가득:
                    s.덮개 = 12.0; s.요청시각 = 지금
                    if s.요청() is not False:
                        s.대화연출(지금)
                else:
                    s.용두취소 = True
            return
        if n["종류"] == "공전":
            v = s.공전속 if n["밀기"] else 잘라(n["속도"] * 3.2, -공전상한, 공전상한)
            s.공전회전 = 착지(s.공전각, 0, v, 공전감속, 지금)
            if not s.공전회전:
                s.공전각 = 0.0; s.공전속 = 0.0
            return
        i = n["i"]; s.빛목표[i] = 0.0; s.속[i] = 0.0; 길이 = 지금 - n["t0"]
        if s.각[i] is None:
            s.각[i] = s.목표(i)  # 누른 동안 초기화 연출이 끝나면 각이 비어 있다
        if n["끌림"]:
            if 길이 < .26 and abs(n["속도"]) > 500:
                s.회전[i] = 착지(s.각[i], s.목표(i), 잘라(n["속도"] * 2.2, -휠상한, 휠상한), 바늘감속, 지금)
            elif n["u"] > .02:
                # 태엽 풀림: 감은 양만큼의 토크가 잠깐에 걸쳐 속도로 바뀐 뒤 베어링 감속으로 넘어간다
                s.회전[i] = dict(풀림=True, t0=지금, 각0=s.각[i], 쪽=-math.copysign(1, n["감김"]), W=300 + (휠상한 - 300) * n["u"] ** .8, T=.22 + .38 * n["u"])
            else:
                s.회전[i] = 착지(s.각[i], s.목표(i), 0, 바늘감속, 지금)
        else:
            s.회전[i] = 착지(s.각[i], s.목표(i), 0, 바늘감속, 지금)
            if i == 2 and 길이 < .3:
                if 지금 - s.앞클릭 < .38:
                    s.액정목표 = 0.0 if s.액정목표 > .5 else 1.0; s.앞클릭 = -1e9
                else:
                    s.앞클릭 = 지금

    def 틱(s, 지금):
        dt = 잘라(지금 - s.앞시각, 0, .05) if s.앞시각 is not None else .016
        s.앞시각 = 지금; n = s.누름
        if n:
            if "속도" in n:
                n["속도"] *= math.exp(-6 * dt)
            if n["종류"] == "공전":
                if n["밀기"]:
                    쓰는중 = 지금 - n["민시각"] < .09
                    s.공전속 *= math.exp(-공전감속[1] * dt) if 쓰는중 else math.exp(-dt / .09); s.공전각 += s.공전속 * dt
                    if not 쓰는중 and abs(s.공전속) < 30:
                        s.공전속 = 0.0; n["밀기"] = False; n["속도"] = 0.0
                else:
                    s.공전속 = n["속도"]
            elif n["종류"] == "용두":
                # 앞 압축이 끝나기 전(덮개가 떠 있는 동안)에는 다시 걸리지 않는다. 같은 대화를 두 번 압축하지 않게 한다
                if not n["끝"] and n["당김"] and not s.용두취소 and not s.연출[1] and not s.회전[1] and s.덮개 is None:
                    n["끝"] = True; s.용두진행 = True; s.용두가득 = False; s.용두표시 = 0.0; s.용두시작 = 지금
                elif n["당김"] and s.덮개 is not None and not n.get("거절"):
                    # 앞 압축이 바쁜 세션에서 줄을 서 있으면 최대 15분 걸린다. 아무 반응이 없으면 고장으로 보이니 한 번 흔들어 「지금은 안 됨」을 알린다
                    n["거절"] = True; s.흔들 = 지금
            elif n["종류"] == "바늘" and n["끌림"]:
                떨림 = math.sin(지금 * 62) * 2.4 * (n["u"] - .8) / .2 if n["u"] > .8 else 0
                s.각[n["i"]] = n["시작각"] + n["표시"] + 떨림
        # 용두: 잡아 뺀 동안 끊김 없이 차오르고 용두도 함께 빠진다
        if s.용두진행:
            q = min(1, (지금 - s.용두시작) / 초기화초); s.용두표시 = .55 * q + .45 * (.5 - .5 * math.cos(math.pi * q)); s.용두가득 = q >= 1
        elif s.용두취소:
            s.용두표시 *= math.exp(-dt / .5)
            if s.용두표시 < .004:
                s.용두취소 = False
        붉음목표 = 1.0 if s.용두진행 or s.용두취소 else 0.0
        s.붉음 += (붉음목표 - s.붉음) * (1 - math.exp(-dt / .13)); s.붉음 = 0.0 if s.붉음 < .01 else s.붉음
        용두목표 = 3 + 5 * s.용두표시 if s.용두진행 else 0.0
        s.용두x += (용두목표 - s.용두x) * (1 - math.exp(-dt / .05))
        if not s.액정끌기:
            s.액정 += (s.액정목표 - s.액정) * (1 - math.exp(-dt / .09))
            if abs(s.액정 - s.액정목표) < .002:
                s.액정 = s.액정목표
        if s.덮개 is not None and 지금 - s.요청시각 > (대기제한 if s.대기 else 요청제한):
            s.요청실패()
        if s.공전회전:
            a, w, 끝 = 어디(s.공전회전, 지금); s.공전각 = a; s.공전속 = w
            if 끝:
                s.공전회전 = None; s.공전각 = 0.0; s.공전속 = 0.0
        s.번쩍 = [x for x in s.번쩍 if 지금 - x[1] < 1.2]; s.파동 = [x for x in s.파동 if 지금 - x[1] < .9]
        if s.흔들 is not None and 지금 - s.흔들 > .34:
            s.흔들 = None
        for i in range(3):
            s.빛값[i] += (s.빛목표[i] - s.빛값[i]) * (1 - math.exp(-dt / .08)); s.빛값[i] = 0.0 if s.빛값[i] < .01 else s.빛값[i]
            눌린 = n and n["종류"] == "바늘" and n["i"] == i
            if s.연출[i]:
                s.연출틱(i, 지금)
                if not s.연출[i] or not s.연출[i]["빛만"]:
                    if s.연출[i] is not None and not s.연출[i]["빛만"]:
                        continue
            if 눌린:
                continue
            if s.회전[i] and s.회전[i].get("휠"):
                s.각[i], s.속[i], 끝 = 휠적분(s.회전[i], 지금)
                if 끝:
                    s.회전[i] = 착지(s.각[i], s.목표(i), s.속[i], 바늘감속, 지금)
            elif s.회전[i] and s.회전[i].get("풀림"):
                r = s.회전[i]; q = min(1, (지금 - r["t0"]) / r["T"])
                s.각[i] = r["각0"] + r["쪽"] * r["W"] * r["T"] * (q * q - q * q * q / 3); s.속[i] = r["쪽"] * r["W"] * (1 - (1 - q) ** 2)
                if q >= 1:
                    s.회전[i] = 착지(s.각[i], s.목표(i), r["쪽"] * r["W"], 바늘감속, 지금)
            elif s.회전[i]:
                a, w, 끝 = 어디(s.회전[i], 지금); s.각[i] = a; s.속[i] = w
                if 끝:
                    s.회전[i] = None; s.속[i] = 0.0; s.각[i] = s.목표(i) - 짧게(s.목표(i) - a)
            elif s.각[i] is not None:
                차 = 짧게(s.목표(i) - s.각[i])
                if abs(차) < .2:
                    s.각[i] = None
                else:
                    s.각[i] += 차 * min(1, 7 * dt)

    def 연출틱(s, i, 지금):
        r = s.연출[i]; t = 지금 - r["t0"]; 시작, 쓸각 = s.판[i][3:5]; 빛만 = r["빛만"]
        if t < .24:
            q = t / .24
            if not 빛만:
                s.각[i] = r["시작"] + (시작 - r["시작"]) * q * q
            s.빛부채[i] = 0.0
        elif t < 1.02:
            p = 부드럽게((t - .24) / .78); d = 쓸각 * p
            if not 빛만:
                s.각[i] = 시작 + d
            s.빛부채[i] = d
            if i == 2:
                s.표시분 = round(p * 300)
        else:
            if not r["정점"]:
                r["정점"] = True; s.빛부채[i] = None; s.파동.append((i, 지금)); s.흔들 = 지금
                s.번쩍 += [(j, 지금) for j in range(3) if j != i and not s.연출[j]]
                if i == 2:
                    s.표시분 = 300
                if i == 0:
                    s.공전회전 = 착지(s.공전각, 0, 1500, 공전감속, 지금)
            q = (t - 1.02) / 1.5
            if not 빛만:
                끝각 = 시작 + 쓸각; s.각[i] = s.목표(i) + (끝각 - s.목표(i)) * math.exp(-4.6 * q) * math.cos(8 * q)
            if q >= 1:
                s.연출[i] = None; s.표시분 = None if i == 2 else s.표시분
                if not 빛만:
                    s.각[i] = None

    def 빛세기(s, i, 지금):
        상태 = s.상태빛 if i == 2 else s.백빛 if i == 1 else 0.0
        r = s.연출[i]
        if r:
            t = 지금 - r["t0"]
            return max(상태, 0.0 if t < .24 else 1.0 if t < 1.02 else max(0.0, 1 - (t - 1.02) / 1.5) ** 1.7)
        return max([s.빛값[i], 상태] + [.7 * (1 - ((지금 - t0) / 1.2)) ** 2 for j, t0 in s.번쩍 if j == i])

    def 휠돌림(s, i, 쪽, 지금):
        # 휠 한 칸마다 그 시계 바늘에 태엽 같은 힘을 건다. 같은 쪽은 점점 빨라지고, 반대쪽은 저항하며 깎이다 이기면 거꾸로 빨라진다
        if s.누름 or s.연출[i] or (s.회전[i] and s.회전[i].get("풀림")):
            return False
        r = s.회전[i]
        if r and r.get("휠"):
            휠적분(r, 지금)
        else:
            if r:
                a, w, _ = 어디(r, 지금)
            else:
                a, w = (s.각[i] if s.각[i] is not None else s.목표(i)), 0.0
            r = s.회전[i] = dict(휠=True, 각=a, w=w, 앞=지금, 힘=[])
        반대 = r["w"] and math.copysign(1, r["w"]) != 쪽
        양 = 휠힘 * (1 - 역저항 * min(1.0, abs(r["w"]) / 휠상한)) if 반대 else 휠힘
        r["힘"].append((지금, 쪽 * 양, 역힘시간 if 반대 else 힘시간))
        s.각[i] = r["각"]
        return True

    def 활동중(s):
        return bool(s.누름 or s.공전회전 or any(s.회전) or any(s.연출) or s.용두진행 or s.용두취소 or s.파동 or s.번쩍 or s.흔들 is not None or s.붉음 > 0 or s.용두x > .05
                    or abs(s.액정 - s.액정목표) > 0 or any(x is not None for x in s.각) or any(v > 0 for v in s.빛값))
