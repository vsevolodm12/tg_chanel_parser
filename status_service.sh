#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ ! -f service.pid ]; then
  echo "PID-файл не найден. Возможно, сервис не запущен."
  exit 1
fi

PID=$(cat service.pid)
if ps -p "$PID" > /dev/null 2>&1; then
  echo "Сервис работает, PID=$PID"
else
  echo "Сервис не работает, PID-файл устарел."
fi

