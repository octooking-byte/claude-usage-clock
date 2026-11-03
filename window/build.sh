# 크롬으로 원판(base.png)과 바늘(hand.png)을 뽑는다. --photo를 주면 시계 사진(watch.png)부터 다시 만든다.
cd "$(dirname "$0")"
P="python"
C="/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
D="$(pwd -W)"
U="file:///$D/dial_base.html"
OPTS="--headless=new --disable-gpu --hide-scrollbars --default-background-color=00000000 --force-device-scale-factor=3 --virtual-time-budget=9000 --allow-file-access-from-files --user-data-dir=$TEMP/tp_chrome"
if [ "$1" = "--photo" ]; then
  PYTHONIOENCODING=utf-8 "$P" photo_dial.py "${PHOTO:?시계 사진 경로를 PHOTO에 넣으세요}" watch.png
fi
"$C" $OPTS --window-size=554,296 --screenshot="$D/base.png" "$U" 2>/dev/null
"$C" $OPTS --window-size=270,270 --screenshot="$D/hand.png" "$U#hand" 2>/dev/null
"$C" $OPTS --window-size=554,296 --screenshot="$D/glow.png" "$U#glow" 2>/dev/null
for i in 0 1 2; do
  "$C" $OPTS --window-size=554,296 --screenshot="$D/base$i.png" "$U#s$i" 2>/dev/null
  "$C" $OPTS --window-size=554,296 --screenshot="$D/glow$i.png" "$U#glow-s$i" 2>/dev/null
done
P2="file:///$D/parts.html"
"$C" $OPTS --window-size=178,208 --screenshot="$D/panel.png" "$P2#panel" 2>/dev/null
"$C" $OPTS --window-size=30,22 --screenshot="$D/crown.png" "$P2#crown" 2>/dev/null
"$C" $OPTS --window-size=178,208 --screenshot="$D/panelc.png" "$P2#panelc" 2>/dev/null
for n in 0 1 2 3 4; do "$C" $OPTS --window-size=27,40 --screenshot="$D/crownc$n.png" "$P2#crownc-$n" 2>/dev/null; done
for i in 0 1 2; do "$C" $OPTS --window-size=554,296 --screenshot="$D/base${i}_lt.png" "$U#s$i-lt" 2>/dev/null; done
"$C" $OPTS --window-size=27,38 --screenshot="$D/pusher.png" "$P2#pusher" 2>/dev/null
