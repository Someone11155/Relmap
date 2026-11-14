#!/usr/bin/env bash
# 사용법:  dev/run.sh                  전체 테스트
#          dev/run.sh collab panel     일부만 (tests/t_<이름>.py)
# 준비물은 dev/README.md 의 '필요한 것' 참고.
cd "$(dirname "$0")"
NAMES=("$@"); [ ${#NAMES[@]} -eq 0 ] && NAMES=(panel overlap mode phys works watch collab captcha reconnect race json)
expect(){ case "$1" in panel) echo 13;; overlap) echo 7;; mode) echo 29;; phys) echo 14;; works) echo 17;; watch) echo 21;; collab) echo 16;; captcha) echo 10;; reconnect) echo 12;; json) echo 23;; *) echo "?";; esac; }
bash setup_db.sh >/dev/null || { echo "DB 준비 실패 — dev/README.md 의 '필요한 것'을 확인하세요"; exit 2; }
python3 -m http.server 8765 --directory .. >/dev/null 2>&1 &
HTTP=$!
node fakesb.mjs >fakesb.log 2>&1 &
FAKE=$!
trap 'kill $HTTP $FAKE 2>/dev/null' EXIT
sleep 2
rc=0
for n in "${NAMES[@]}"; do
  out=$(python3 tests/t_$n.py 2>&1)
  pass=$(printf '%s\n' "$out" | grep -c '^PASS'); fail=$(printf '%s\n' "$out" | grep -c '^FAIL')
  if [ "$n" = race ] || [ "$n" = stress ]; then
    line=$(printf '%s\n' "$out" | grep 'diverged' | tail -1); echo "$n: ${line:-(결과 없음 — 오류 확인)}"; printf '%s\n' "$line" | grep -q 'diverged 0' || { rc=1; printf '%s\n' "$out" | tail -5; }
  else
    exp=$(expect "$n"); echo "$n: PASS $pass / FAIL $fail (기대 PASS $exp)"
    [ "$fail" -gt 0 ] && { printf '%s\n' "$out" | grep '^FAIL'; rc=1; }
    [ "$exp" != "?" ] && [ "$pass" -ne "$exp" ] && { rc=1; [ "$fail" -eq 0 ] && printf '%s\n' "$out" | tail -5; }
  fi
done
exit $rc
