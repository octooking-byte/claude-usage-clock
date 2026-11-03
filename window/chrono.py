# 크로노그래프 시계의 동작 규칙. 바늘·태엽·연출은 세 시계(계기)를 그대로 쓰고, 자리와 손짓이 다른 곳만 여기 둔다.
# 손짓: 안쪽 돌리기=태엽, 작은 다이얼 테=공전, 은색 테 위쪽=창 이동, 은색 테 중간과 아래=전체 스핀, 용두 끌기=대화 초기화, 초승달=액정
# 좌표는 세 시계와 같다. 가운데 시계의 중심(277, 139)이 양쪽에서 같은 자리다
import math

from gauge import 계기, 공전감속, 공전상한, 밀기게인, 액정길이, 어디, 잘라, 착지, 짧게

가x, 가y = 277, 139
판표 = ((222, 130, 44, -135, 270), (332, 130, 44, -135, 270), (가x, 가y, 170, -135, 270))
용두끝 = 14


def 돌려재기(각도, x, y):
    if not 각도:
        return x, y
    r = -math.radians(각도); dx = x - 가x; dy = y - 가y
    return 가x + dx * math.cos(r) - dy * math.sin(r), 가y + dx * math.sin(r) + dy * math.cos(r)


class 크로노(계기):
    판 = 판표

    def __init__(s, 요청=None):
        super().__init__(요청)
        s.전체각 = 0.0; s.전체속 = 0.0; s.전체회전 = None; s.용두목표 = 0.0; s.끈x = 0.0; s.끈v = 0.0

    def 제자리(s, i, x, y):
        a, b = 돌려재기(s.전체각, x, y)
        return (a, b) if i == 2 else 돌려재기(s.공전각, a, b)

    def 액정안(s, x, y):
        dx = x - 가x
        if abs(dx) > 85:
            return False
        아래 = 312 + 액정길이 * s.액정 - 23 + 23 * math.sqrt(1 - dx * dx / 7225)
        return y < 아래 + 10 and math.hypot(dx, y - 가y) >= 170

    def 큰바늘위(s, x, y):
        # 큰 바늘은 작은 다이얼 위를 지나간다. 맨 위에 보이는 것이 먼저 잡혀야 한다
        px, py = s.제자리(2, x, y); a = math.radians(s.각[2] if s.각[2] is not None else s.목표(2)); dx = px - 가x; dy = py - 가y
        길이 = dx * math.sin(a) - dy * math.cos(a); 옆 = dx * math.cos(a) + dy * math.sin(a)
        return -45 < 길이 < 150 and abs(옆) < 9

    def 찾기(s, x, y):
        중심 = math.hypot(x - 가x, y - 가y)
        if s.전체회전 and abs(s.전체속) > 200 and 중심 < 172:
            return "전체", 2
        if 439 < x < 485 and abs(y - 가y) < 18 and 중심 >= 166:
            return "용두", 1
        if s.공전회전 and abs(s.공전속) > 200 and 중심 < 112:
            return "공전", 0
        if s.액정안(x, y):
            return "액정", 2
        if 중심 >= 172:
            return None
        if s.큰바늘위(x, y):
            return "바늘", 2
        for i in (0, 1):
            px, py = s.제자리(i, x, y); cx, cy, r = s.판[i][:3]; d = math.hypot(px - cx, py - cy)
            if d < r * .7:
                return "바늘", i
            if d < r * 1.08:
                return "공전", i
        if 중심 < 155:
            return "바늘", 2
        # 은색 테는 눈금 40~60 사이만 창을 옮기고 나머지 둘레는 스피너다
        return ("창", 2) if abs(math.degrees(math.atan2(x - 가x, 가y - y))) <= 27 else ("전체", 2)

    def 눌림(s, x, y, 지금):
        곳 = s.찾기(x, y)
        if 곳 and 곳[0] == "전체":
            밀기 = bool(s.전체회전) and abs(s.전체속) > 200; s.전체회전 = None
            if not 밀기:
                s.전체속 = 0.0
            s.누름 = dict(종류="전체", i=2, t0=지금, 전각=s.공전재기(x, y), 전시=지금, 속도=0.0, 밀기=밀기, 민시각=-1e9)
            return "전체"
        return super().눌림(x, y, 지금)

    def 끌림(s, x, y, 지금):
        n = s.누름
        if n and n["종류"] == "용두":
            # 용두는 손을 따라 빠지되 끝으로 갈수록 뻑뻑해진다
            s.용두목표 = 용두끝 * (1 - math.exp(-max(0, x - n["x"]) / 20))
            return
        if n and n["종류"] == "전체":
            dt = max(.004, 지금 - n["전시"]); 새 = s.공전재기(x, y); 차 = 짧게(새 - n["전각"]); n["전각"] = 새; n["전시"] = 지금
            if n["밀기"]:
                s.전체속 = 잘라(s.전체속 + 차 * 밀기게인, -공전상한, 공전상한); n["민시각"] = 지금
            else:
                s.전체각 += 차; n["속도"] = n["속도"] * .6 + 차 / dt * .4; s.전체속 = n["속도"]
            return
        super().끌림(x, y, 지금)

    def 놓임(s, 지금):
        n = s.누름
        if n and n["종류"] == "용두":
            s.용두목표 = 0.0
        if n and n["종류"] == "전체":
            s.누름 = None; v = s.전체속 if n["밀기"] else 잘라(n["속도"] * 3.2, -공전상한, 공전상한)
            s.전체회전 = 착지(s.전체각, 0, v, 공전감속, 지금)
            if not s.전체회전:
                s.전체각 = 0.0; s.전체속 = 0.0
            return
        super().놓임(지금)

    def 틱(s, 지금):
        dt = 잘라(지금 - s.앞시각, 0, .05) if s.앞시각 is not None else .016; n = s.누름
        if n and n["종류"] == "용두":
            n["당김"] = s.끈x >= 9
        super().틱(지금)
        if n and n["종류"] == "용두" and s.용두진행 and s.용두목표 < 6:
            s.용두진행 = False; s.용두취소 = True; n["끝"] = False
        # 용두 스프링: 놓으면 튕겨 들어와 케이스에 부딪혀 살짝 되튄다
        for _ in range(4):
            h = dt / 4; s.끈v += (900 * (s.용두목표 - s.끈x) - 30 * s.끈v) * h; s.끈x += s.끈v * h
            if s.끈x < 0:
                s.끈x = 0.0; s.끈v = -s.끈v * .35
        s.용두x = s.끈x
        if n and n["종류"] == "전체" and s.누름:
            if n["밀기"]:
                쓰는중 = 지금 - n["민시각"] < .09
                s.전체속 *= math.exp(-공전감속[1] * dt) if 쓰는중 else math.exp(-dt / .09); s.전체각 += s.전체속 * dt
                if not 쓰는중 and abs(s.전체속) < 30:
                    s.전체속 = 0.0; n["밀기"] = False; n["속도"] = 0.0
            else:
                s.전체속 = n["속도"]
        if s.전체회전:
            a, w, 끝 = 어디(s.전체회전, 지금); s.전체각 = a; s.전체속 = w
            if 끝:
                s.전체회전 = None; s.전체각 = 0.0; s.전체속 = 0.0

    def 활동중(s):
        return super().활동중() or bool(s.전체회전 or s.전체각) or s.끈x > .05 or abs(s.끈v) > .5
