#!/usr/bin/env bash
# 사용법:  dev/run.sh                  전체 테스트
#          dev/run.sh collab panel     일부만 (tests/t_<이름>.py)
# 준비물은 dev/README.md 의 '필요한 것' 참고.
cd "$(dirname "$0")"
NAMES=("$@"); [ ${#NAMES[@]} -eq 0 ] && NAMES=(panel overlap mode phys works watch auth collab captcha reconnect race json backup multi profile nest cat dark tune icon search conn cache photo rt)
expect(){ case "$1" in panel) echo 16;; overlap) echo 10;; mode) echo 33;; phys) echo 14;; works) echo 20;; watch) echo 29;; auth) echo 31;; collab) echo 16;; captcha) echo 10;; reconnect) echo 12;; json) echo 23;; backup) echo 13;; multi) echo 13;; profile) echo 31;; nest) echo 14;; cat) echo 12;; dark) echo 20;; tune) echo 26;; icon) echo 11;; conn) echo 16;; cache) echo 11;; photo) echo 16;; rt) echo 18;; search) echo 29;; *) echo "?";; esac; }
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
