#!/bin/bash

# Скрипт деплоя на сервер
# Использование: ./deploy.sh user@server:/path/to/deploy

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка аргументов
if [ -z "$1" ]; then
    echo -e "${RED}Ошибка: укажите адрес сервера${NC}"
    echo "Использование: ./deploy.sh user@server:/path/to/deploy"
    echo "Пример: ./deploy.sh root@192.168.1.100:/opt/tgchanelparser"
    exit 1
fi

SERVER_PATH="$1"
SERVER_USER=$(echo "$SERVER_PATH" | cut -d@ -f1)
SERVER_HOST=$(echo "$SERVER_PATH" | cut -d@ -f2 | cut -d: -f1)
SERVER_DIR=$(echo "$SERVER_PATH" | cut -d: -f2)

echo -e "${GREEN}🚀 Начинаю деплой на ${SERVER_HOST}${NC}"

# Проверка наличия rsync
if ! command -v rsync &> /dev/null; then
    echo -e "${RED}Ошибка: rsync не установлен${NC}"
    exit 1
fi

# Список файлов для исключения
EXCLUDE_FILE=$(mktemp)
cat > "$EXCLUDE_FILE" <<EOF
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
.venv
*.session-journal
database.db
*.log
service.pid
.env
.git/
.gitignore
*.md
send_code.py
auth_telegram.py
EOF

echo -e "${YELLOW}📦 Копирую файлы на сервер...${NC}"
rsync -avz --exclude-from="$EXCLUDE_FILE" \
    --exclude='*.db' \
    --exclude='*.log' \
    --exclude='*.pid' \
    --exclude='.env' \
    ./ "$SERVER_PATH/"

rm "$EXCLUDE_FILE"

echo -e "${YELLOW}🔧 Настраиваю окружение на сервере...${NC}"

# Команды для выполнения на сервере
ssh "$SERVER_USER@$SERVER_HOST" <<EOF
set -e

cd $SERVER_DIR

# Создаем виртуальное окружение если его нет
if [ ! -d "venv" ]; then
    echo "Создаю виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем и обновляем зависимости
echo "Устанавливаю зависимости..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Проверяем наличие .env
if [ ! -f ".env" ]; then
    echo "⚠️  ВНИМАНИЕ: .env файл не найден!"
    echo "Скопируйте .env файл вручную на сервер"
    echo "Или создайте его из env.sample"
fi

# Делаем скрипты исполняемыми
chmod +x start_service.sh
chmod +x stop_service.sh
chmod +x status_service.sh

echo "✅ Деплой завершен!"
echo ""
echo "Следующие шаги:"
echo "1. Скопируйте .env файл на сервер: scp .env $SERVER_PATH/.env"
echo "2. Скопируйте сессию Telethon (если есть): scp tg_session.session $SERVER_PATH/tg_session.session"
echo "   Если сессии нет, авторизуйтесь:"
echo "   ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_DIR && source venv/bin/activate && python3 auth.py'"
echo "3. Запустите сервис:"
echo "   ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_DIR && bash start_service.sh'"
EOF

echo -e "${GREEN}✅ Деплой завершен!${NC}"
echo ""
echo -e "${YELLOW}Следующие шаги:${NC}"
echo "1. Скопируйте .env: scp .env $SERVER_PATH/.env"
if [ -f "tg_session.session" ]; then
    echo -e "${GREEN}2. Копирую сессию Telethon...${NC}"
    scp tg_session.session "$SERVER_PATH/tg_session.session"
    echo -e "${GREEN}   ✅ Сессия скопирована!${NC}"
else
    echo -e "${YELLOW}2. Сессия не найдена. Авторизуйтесь в Telethon:${NC}"
    echo "   ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_DIR && source venv/bin/activate && python3 auth.py'"
fi
echo "3. Запустите сервис: ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_DIR && bash start_service.sh'"

