# Деплой на сервер

## Быстрый деплой

1. **Настройте переменные:**
   ```bash
   export SERVER="user@your-server.com"
   export DEPLOY_PATH="/opt/tgchanelparser"
   ```

2. **Запустите деплой:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh $SERVER:$DEPLOY_PATH
   ```

3. **Скопируйте .env файл:**
   ```bash
   scp .env $SERVER:$DEPLOY_PATH/.env
   ```

4. **Скопируйте сессию Telethon (если есть):**
   ```bash
   scp tg_session.session $SERVER:$DEPLOY_PATH/tg_session.session
   ```
   
   Если сессии нет, авторизуйтесь один раз:
   ```bash
   ssh $SERVER "cd $DEPLOY_PATH && source venv/bin/activate && python3 auth.py"
   ```

5. **Запустите сервис:**
   ```bash
   ssh $SERVER "cd $DEPLOY_PATH && bash start_service.sh"
   ```

## Деплой через systemd (автозапуск)

1. **Скопируйте service файл на сервер:**
   ```bash
   scp tgchanelparser.service $SERVER:/tmp/
   ```

2. **На сервере:**
   ```bash
   # Отредактируйте файл: замените YOUR_USER на вашего пользователя
   sudo nano /tmp/tgchanelparser.service
   
   # Укажите правильный путь к проекту
   # Замените /opt/tgchanelparser на ваш путь
   
   # Установите service
   sudo mv /tmp/tgchanelparser.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable tgchanelparser
   sudo systemctl start tgchanelparser
   ```

3. **Управление сервисом:**
   ```bash
   sudo systemctl status tgchanelparser  # статус
   sudo systemctl stop tgchanelparser    # остановить
   sudo systemctl start tgchanelparser   # запустить
   sudo systemctl restart tgchanelparser # перезапустить
   sudo journalctl -u tgchanelparser -f  # логи
   ```

## Ручной деплой

Если скрипт не работает, можно сделать вручную:

1. **Создайте директорию на сервере:**
   ```bash
   ssh user@server "mkdir -p /opt/tgchanelparser"
   ```

2. **Скопируйте файлы:**
   ```bash
   rsync -avz --exclude='venv' --exclude='*.db' --exclude='*.log' \
     --exclude='.env' --exclude='*.session' ./ user@server:/opt/tgchanelparser/
   ```

3. **На сервере установите зависимости:**
   ```bash
   ssh user@server
   cd /opt/tgchanelparser
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Скопируйте .env и сессию:**
   ```bash
   scp .env user@server:/opt/tgchanelparser/.env
   scp tg_session.session user@server:/opt/tgchanelparser/tg_session.session
   ```
   
   Если сессии нет, авторизуйтесь:
   ```bash
   ssh user@server "cd /opt/tgchanelparser && source venv/bin/activate && python3 auth.py"
   ```

5. **Запустите:**
   ```bash
   ssh user@server "cd /opt/tgchanelparser && bash start_service.sh"
   ```

## Проверка работы

```bash
# Статус сервиса
ssh $SERVER "cd $DEPLOY_PATH && bash status_service.sh"

# Логи
ssh $SERVER "tail -f $DEPLOY_PATH/service.log"
```

