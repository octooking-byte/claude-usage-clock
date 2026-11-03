# 크로노그래프 배치 시안의 원판을 층별로 뽑는다
cd "$(dirname "$0")"
C="/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
D="$(pwd -W)"
U="file:///$D/center_base.html"
OPTS="--headless=new --disable-gpu --hide-scrollbars --default-background-color=00000000 --force-device-scale-factor=3 --virtual-time-budget=9000 --allow-file-access-from-files --user-data-dir=$TEMP/tp_chrome"
"$C" $OPTS --window-size=420,470 --screenshot="$D/base.png" "$U#m" 2>/dev/null
"$C" $OPTS --window-size=420,470 --screenshot="$D/sub0.png" "$U#m0" 2>/dev/null
"$C" $OPTS --window-size=420,470 --screenshot="$D/sub1.png" "$U#m1" 2>/dev/null
"$C" $OPTS --window-size=420,470 --screenshot="$D/glow.png" "$U#m-glow" 2>/dev/null
"$C" $OPTS --window-size=420,470 --screenshot="$D/gsub0.png" "$U#m0-glow" 2>/dev/null
"$C" $OPTS --window-size=420,470 --screenshot="$D/gsub1.png" "$U#m1-glow" 2>/dev/null
"$C" $OPTS --window-size=420,470 --screenshot="$D/all.png" "$U" 2>/dev/null
# 흰 시계. 빛 층은 검은 시계와 같이 쓴다
"$C" $OPTS --window-size=420,470 --screenshot="$D/base_lt.png" "$U#m-lt" 2>/dev/null
"$C" $OPTS --window-size=420,470 --screenshot="$D/sub0_lt.png" "$U#m0-lt" 2>/dev/null
"$C" $OPTS --window-size=420,470 --screenshot="$D/sub1_lt.png" "$U#m1-lt" 2>/dev/null
# 용두로 색을 고르는 동안만 켜지는 오른쪽 빛
"$C" $OPTS --window-size=420,470 --screenshot="$D/base_ring.png" "$U#m-ring" 2>/dev/null
"$C" $OPTS --window-size=420,470 --screenshot="$D/base_lt_ring.png" "$U#m-lt-ring" 2>/dev/null
