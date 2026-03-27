#!/bin/bash
# Stop hook: 오늘 history 파일 존재 여부 확인 후 미기록 시 알림

INPUT=$(cat)

# stop_hook_active이면 즉시 종료 (무한루프 방지)
if [ "$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d.get('stop_hook_active', False)).lower())")" = "true" ]; then
  exit 0
fi

HISTORY_FILE="$CLAUDE_PROJECT_DIR/history/$(date +%Y-%m-%d).md"

if [ ! -f "$HISTORY_FILE" ]; then
  echo "⚠️  오늘 history 파일이 없습니다. 작업이 있었다면 /record-history 를 실행하세요." >&2
fi

exit 0
