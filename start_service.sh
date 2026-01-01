#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ -f service.pid ] && ps -p "$(cat service.pid)" > /dev/null 2>&1; then
  echo "Уже запущено, PID=$(cat service.pid)"
  exit 0
fi

# Используем venv, если есть
if [ -d "venv" ]; then
  source venv/bin/activate
  PYTHON=python
else
  PYTHON=python3
fi

nohup "$PYTHON" main.py > service.log 2>&1 &
echo $! > service.pid
echo "Сервис запущен, PID=$(cat service.pid)"

