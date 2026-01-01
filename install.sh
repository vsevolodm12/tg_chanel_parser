#!/bin/bash

# Скрипт установки TG Channel Parser
# Использование: curl -sSL https://raw.githubusercontent.com/vsevolodm12/tg_chanel_parser/main/install.sh | bash

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

INSTALL_DIR="${INSTALL_DIR:-$HOME/tg_chanel_parser}"
REPO_URL="https://github.com/vsevolodm12/tg_chanel_parser.git"

echo -e "${GREEN}🚀 Установка TG Channel Parser${NC}"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 не установлен. Установите Python 3.10+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓ Python версия: $PYTHON_VERSION${NC}"

# Проверка git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git не установлен${NC}"
    exit 1
fi

# Клонируем или обновляем репозиторий
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}📁 Папка $INSTALL_DIR уже существует, обновляю...${NC}"
    cd "$INSTALL_DIR"
    git pull origin main || true
else
    echo -e "${YELLOW}📥 Клонирую репозиторий...${NC}"
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Создаем виртуальное окружение
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🔧 Создаю виртуальное окружение...${NC}"
    python3 -m venv venv
fi

# Активируем и устанавливаем зависимости
echo -e "${YELLOW}📦 Устанавливаю зависимости...${NC}"
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Делаем скрипты исполняемыми
chmod +x start_service.sh stop_service.sh status_service.sh auth.py 2>/dev/null || true

# Создаем .env если его нет
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📝 Создаю .env из шаблона...${NC}"
    cp env.sample .env
    echo -e "${RED}⚠️  ВАЖНО: Заполните .env файл своими данными!${NC}"
fi

echo ""
echo -e "${GREEN}✅ Установка завершена!${NC}"
echo ""
echo -e "${YELLOW}📍 Проект установлен в: $INSTALL_DIR${NC}"
echo ""
echo -e "${YELLOW}Следующие шаги:${NC}"
echo ""
echo "1. Перейдите в папку проекта:"
echo -e "   ${GREEN}cd $INSTALL_DIR${NC}"
echo ""
echo "2. Отредактируйте .env файл (заполните API ключи):"
echo -e "   ${GREEN}nano .env${NC}"
echo ""
echo "3. Скопируйте сессию Telethon с локальной машины (если есть):"
echo -e "   ${GREEN}# На локальной машине выполните:${NC}"
echo -e "   ${GREEN}scp tg_session.session user@server:$INSTALL_DIR/${NC}"
echo ""
echo "   Или авторизуйтесь заново:"
echo -e "   ${GREEN}source venv/bin/activate && python3 auth.py${NC}"
echo ""
echo "4. Запустите сервис:"
echo -e "   ${GREEN}bash start_service.sh${NC}"
echo ""
echo "5. Проверьте статус:"
echo -e "   ${GREEN}bash status_service.sh${NC}"
echo ""
echo "6. Логи:"
echo -e "   ${GREEN}tail -f service.log${NC}"

