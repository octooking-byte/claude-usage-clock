# 세 시계와 한 시계 사이의 곧장 도킹. 양 끝은 각자의 시계가 그대로 그리고, 여기는 그 사이의 시간만 계산한다.
# p는 시간(0~1)이고 합치는 곡선과 나누는 곡선을 따로 둔다. 곡선을 뒤집으면 끝이 뚝 끊기기 때문이다
import math

from gauge import 잘라, 짧게

옛곁 = (173, 15); 바깥 = (203, 18); 도킹 = (55, -9)
길이 = (.95, .85)   # 합치기, 나누기


def 이음(a, b, t):
    return a + (b - a) * t


def 사이(a, b, v):
    t = 잘라((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def 안착(t, z=5.5, w=4.5):
    q = 잘라(t, 0, 1) ** 1.6
    return (1 - math.exp(-z * q) * math.cos(w * q)) / (1 - math.exp(-z) * math.cos(w))


def 곁상태(합, p, sg):
    뜸 = 0.0
    if 합:
        a = 1 - (1 - 잘라(p / .3, 0, 1)) ** 3; t = 잘라((p - .3) / .7, 0, 1); e = 안착(t); 위 = p >= .3; 뜸 = math.sin(math.pi * t); 섞 = 사이(.2, .62, t)
        if p < .3:
            x, y, R = 이음(옛곁[0], 바깥[0], a), 이음(옛곁[1], 바깥[1], a), 이음(86, 72, a)
        else:
            x, y, R = 이음(바깥[0], 도킹[0], e), 이음(바깥[1], 도킹[1], e), 이음(72, 44, e)
    else:
        준 = 사이(0, .1, p); t = 잘라((p - .1) / .52, 0, 1); e = 1 - (1 - t) ** 2.5; b = 잘라((p - .62) / .38, 0, 1); f = 안착(b, 6, 5); 위 = p < .62; 뜸 = math.sin(math.pi * t); 섞 = 1 - 사이(.05, .5, t)
        if p < .62:
            x, y, R = 이음(도킹[0], 바깥[0], e) - 4 * 준 * (1 - t), 이음(도킹[1], 바깥[1], e), 이음(44 - 1.5 * 준, 72, e)
        else:
            x, y, R = 이음(바깥[0], 옛곁[0], f), 이음(바깥[1], 옛곁[1], f), 이음(72, 86, f)
    return dict(x=sg * x, y=y, R=R, 섞=섞, 위=위, 뜸=뜸)


def 상태(합, p, 회, 공):
    if 합:
        a = 1 - (1 - 잘라(p / .3, 0, 1)) ** 3; t = 잘라((p - .3) / .7, 0, 1)
        k = 이음(130, 126, a) if p < .3 else 이음(126, 170, 안착((t - .1) / .9)); 섞 = 사이(.25, .6, t); 용 = 사이(.72, 1, t)
    else:
        t = 잘라((p - .1) / .52, 0, 1); b = 잘라((p - .62) / .38, 0, 1)
        k = 이음(170, 126, 1 - (1 - t) ** 2.5) if p < .62 else 이음(126, 130, 안착(b, 6, 5)); 섞 = 1 - 사이(.05, .45, t); 용 = 1 - 사이(0, .16, p)
    풂 = 1 - 사이(0, .35, p)
    return dict(k=k, 섞=섞, 용=용, 회=회 * 풂, 공=공 * 풂, 곁=(곁상태(합, p, -1), 곁상태(합, p, 1)))


def 섞기(a, b, t):
    def 숫자(o, q):
        r = dict(q)
        for n, v in q.items():
            if isinstance(v, float) and not isinstance(v, bool):
                r[n] = 이음(o[n], v, t)
        return r
    r = 숫자(a, b); r["곁"] = (숫자(a["곁"][0], b["곁"][0]), 숫자(a["곁"][1], b["곁"][1]))
    return r


def 멈추기(g):
    # 바뀌기 직전에 진행 중인 손짓을 정리한다. 바늘 연출과 값은 그대로 둔다
    g.누름 = None; g.공전회전 = None; g.공전각 = 0.0; g.공전속 = 0.0; g.용두진행 = False; g.용두취소 = False; g.용두표시 = 0.0; g.액정목표 = 0.0; g.액정끌기 = False
    for i in range(3):
        g.빛목표[i] = 0.0
    if hasattr(g, "전체각"):
        g.전체각 = 0.0; g.전체속 = 0.0; g.전체회전 = None; g.용두목표 = 0.0


class 변신:
    def __init__(s, 모양="큰"):
        s.모양 = 모양; s.합 = 모양 == "큰"; s.p = 1.0; s.진행 = False; s.잡은 = None; s.회 = 0.0; s.공 = 0.0; s.최근 = None; s.쿵 = None; s.울림 = False

    def 시작(s, 세, 크):
        합 = (not s.합) if s.진행 else s.모양 == "셋"
        if s.진행:
            s.잡은 = s.최근
        else:
            s.잡은 = None
            if s.모양 == "큰":
                s.회 = 짧게(크.전체각); s.공 = 짧게(크.공전각)
            else:
                s.회 = 0.0; s.공 = 짧게(세.공전각)
            멈추기(세); 멈추기(크)
        s.합 = 합; s.p = 0.0; s.진행 = True; s.울림 = False

    def 틱(s, dt, 지금):
        if not s.진행:
            return None
        s.p = min(1.0, s.p + dt / 길이[0 if s.합 else 1])
        # 작은 다이얼이 판에 닿는 순간 케이스가 한 번 울린다
        if s.합 and not s.울림 and s.p > .68:
            s.울림 = True; s.쿵 = 지금
        q = 상태(s.합, s.p, s.회, s.공)
        if s.잡은:
            q = 섞기(s.잡은, q, 사이(0, .35, s.p))
        s.최근 = q
        if s.p >= 1:
            s.진행 = False; s.모양 = "큰" if s.합 else "셋"; s.잡은 = None
        return q

    def 흔들림(s, 지금):
        if s.쿵 is None:
            return 0
        q = (지금 - s.쿵) / .22
        if q >= 1:
            s.쿵 = None
            return 0
        return round(1.6 * math.sin(q * 6.3) * (1 - q))
