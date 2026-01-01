#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ ! -f service.pid ]; then
  echo "PID-файл не найден."
  exit 0
fi

PID=$(cat service.pid)
if ps -p "$PID" > /dev/null 2>&1; then
  kill "$PID" && echo "Остановлен PID=$PID"
else
  echo "Процесс не найден, очищаю PID-файл."
fi

rm -f service.pid

