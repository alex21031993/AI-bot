# 🚀 УСТАНОВКА И ЗАПУСК CRYPTO INTELLIGENCE BOT

## 📋 СОДЕРЖАНИЕ

1. [Системные требования](#системные-требования)
2. [Установка Python](#установка-python)
3. [Клонирование репозитория](#клонирование-репозитория)
4. [Установка зависимостей](#установка-зависимостей)
5. [Настройка .env](#настройка-env)
6. [Создание Telegram бота](#создание-telegram-бота)
7. [Запуск бота](#запуск-бота)
8. [Проверка работы](#проверка-работы)
9. [Возможные проблемы](#возможные-проблемы)

---

## 🖥️ СИСТЕМНЫЕ ТРЕБОВАНИЯ

| Компонент | Минимум | Рекомендуется |
|-----------|---------|---------------|
| CPU | 1 ядро | 2+ ядра |
| RAM | 1 GB | 2+ GB |
| Диск | 500 MB | 1 GB |
| OS | Linux/macOS/Windows | Linux (Ubuntu 20.04+) |

---

## 🐍 УСТАНОВКА PYTHON

### Windows

1. Скачайте Python 3.10+ с [python.org](https://www.python.org/downloads/)
2. Запустите установщик
3. **ВАЖНО:** Поставьте галочку "Add Python to PATH"
4. Нажмите "Install Now"

### macOS

```bash
# Через Homebrew
brew install python@3.10

# Или скачайте с python.org
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Проверка:**
```bash
python3 --version
# Должно показать: Python 3.10.x или выше
```

---

## 📁 КЛОНИРОВАНИЕ РЕПОЗИТОРИЯ

### Вариант 1: Git

```bash
# Установите git если нет
sudo apt install git  # Linux
brew install git      # macOS

# Клонируйте репозиторий
git clone https://github.com/alex21031993/AI-bot.git
cd AI-bot
```

### Вариант 2: Скачать ZIP

1. Перейдите на https://github.com/alex21031993/AI-bot
2. Нажмите зелёную кнопку "Code"
3. Выберите "Download ZIP"
4. Распакуйте архив
5. Откройте терминал в папке с проектом

---

## 📦 УСТАНОВКА ЗАВИСИМОСТЕЙ

```bash
# Перейдите в папку проекта
cd AI-bot

# Создайте виртуальное окружение (рекомендуется)
python3 -m venv venv

# Активируйте виртуальное окружение
# Linux/macOS:
source venv/bin/activate

# Windows (PowerShell):
venv\Scripts\activate

# Или Windows (CMD):
venv\Scripts\activate.bat

# Установите зависимости
pip install -r requirements.txt
```

**Важно:** Всегда используйте виртуальное окружение!

---

## ⚙️ НАСТРОЙКА .ENV

Создайте файл `.env` в корневой папке проекта:

```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Или создайте вручную
nano .env  # Linux/macOS
notepad .env  # Windows
```

### ЗАПОЛНИТЕ .ENV:

```env
# ============================================
# TELEGRAM CONFIGURATION
# ============================================

# Токен бота от @BotFather (ОБЯЗАТЕЛЬНО!)
TELEGRAM_BOT_TOKEN=123456789:ABCDefGhiJKlmNoPQRsTUVwxYZ

# Ваш Telegram ID (для доступа к админке)
# Узнать ID: https://t.me/userinfobot
ADMIN_USER_IDS=123456789

# Пароль администратора
ADMIN_PASSWORD=your_secure_password_here


# ============================================
# USDT PAYMENT CONFIGURATION (TRC20)
# ============================================

# Контракт USDT (не менять!)
USDT_CONTRACT_TRC20=TR7NHqjeKQxGTCi8q8REbdNKR2AfZ7Tn7

# ВАШ TRON АДРЕС для приёма платежей
# Получите в кошельке TronLink/Exodus и т.д.
TRON_DEPOSIT_ADDRESS=TCSYEiTBp67GvUk3f2f1foL1jdRKu6upD8

# Минимум подтверждений
MIN_CONFIRMATIONS=6
```

### ПОЛУЧИТЬ TELEGRAM BOT TOKEN:

1. Откройте Telegram
2. Найдите **@BotFather**
3. Отправьте `/newbot`
4. Следуйте инструкциям
5. **Скопируйте токен** (выглядит как `123456789:ABCDefGhiJKlm...`)

### ПОЛУЧИТЬ ВАШ TELEGRAM ID:

1. Откройте Telegram
2. Найдите **@userinfobot**
3. Отправьте `/start`
4. **Скопируйте "Id"** (число)

---

## 🤖 СОЗДАНИЕ TELEGRAM БОТА (ПОДРОБНО)

### Шаг 1: Регистрация

```
1. Откройте Telegram
2. Введите в поиске: @BotFather
3. Нажмите Start
```

### Шаг 2: Создание бота

```
Отправьте сообщение:
/newbot

BotFather ответит:
Alright, a new bot. How are we going to call it? Please choose a name for your bot.

Введите имя (например):
Crypto Intelligence Bot

BotFather:
Good. Now let's give it a username. Username must end in `bot`.

Введите username (должен заканчиваться на bot):
cryptointelligence_bot

✅ Готово! Bot created!
Copy this access token and start chatting:
123456789:ABCDefGhiJKlmNoPQRsTUVwxYZ123456789
```

### Шаг 3: Настройка бота

```
/setname Crypto Intelligence Bot          # Имя бота
/setdescription Бот для анализа криптовалют  # Описание
/setabouttext Анализ криптовалют с ИИ      # О боте
/setuserpic                              # Установить фото
```

---

## 🚀 ЗАПУСК БОТА

### Подготовка

```bash
# Перейдите в папку проекта
cd AI-bot

# Активируйте виртуальное окружение
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows
```

### Запуск

```bash
# Простой запуск
python main.py

# Или с логированием
python main.py 2>&1 | tee bot.log
```

### Ожидаемый вывод:

```
2026-06-27 19:00:00 | INFO     | __main__:main - 🚀 Starting Crypto Intelligence Bot
2026-06-27 19:00:00 | INFO     | __main__:main - 📱 100% Button-Only Interface
2026-06-27 19:00:00 | INFO     | database.manager - Database initialized: crypto_bot.db
2026-06-27 19:00:00 | INFO     | tron_tracker - TRON payment tracker started
2026-06-27 19:00:00 | INFO     | __main__:main - ✅ Database initialized
2026-06-27 19:00:00 | INFO     | __main__:main - ✅ Background monitor ready
2026-06-27 19:00:00 | INFO     | __main__:main - 📱 Starting button-only bot...
```

**Бот запущен!** 🎉

---

## ✅ ПРОВЕРКА РАБОТЫ

### Через браузер (опционально)

```bash
# Установите ngrok для доступа извне
# Скачайте с ngrok.com

# В отдельном терминале:
ngrok http 5000
```

### Тестирование функций

1. **Откройте Telegram**
2. **Найдите своего бота** (по username)
3. **Нажмите Start**
4. **Видите приветствие с кнопками?**

```
👋 Привет, [Имя]!

🐋 Crypto Intelligence Bot
Твой персональный AI-аналитик

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 Что я умею:

📊 АВТОМАТИЧЕСКИ нахожу лучшие монеты
🟢🟡🔴 Сигналы на покупку/продажу
🔔 Уведомления в реальном времени

👇 Выберите действие:
[🔍 НАЙТИ МОНЕТЫ]
[📊 ТОП-10]
[📈 СИГНАЛЫ]
...
```

---

## 🔧 ВОЗМОЖНЫЕ ПРОБЛЕМЫ

### ❌ Ошибка "Module not found"

```bash
# Переустановите зависимости
pip install -r requirements.txt --force-reinstall
```

### ❌ Ошибка "No module named 'dotenv'"

```bash
pip install python-dotenv
```

### ❌ Бот не отвечает

1. Проверьте токен в `.env`
2. Перезапустите бота
3. Проверьте логи

### ❌ Ошибка базы данных

```bash
# Удалите старую базу
rm crypto_bot.db

# Или создайте заново
python -c "from crypto_intelligence_agent.database.manager import DatabaseManager; import asyncio; asyncio.run(DatabaseManager().initialize())"
```

### ❌ API ошибки

```bash
# Проверьте интернет-соединение
ping api.coingecko.com

# Или подождите - возможно лимит API
```

### ❌ Port already in use

```bash
# Найдите процесс
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# Убейте процесс
kill -9 [PID]
```

---

## 📊 ЗАПУСК В ФОНОВОМ РЕЖИМЕ

### Linux (systemd)

```bash
# Создайте файл сервиса
sudo nano /etc/systemd/system/crypto-bot.service
```

```ini
[Unit]
Description=Crypto Intelligence Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/AI-bot
ExecStart=/path/to/AI-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Активируйте
sudo systemctl daemon-reload
sudo systemctl enable crypto-bot
sudo systemctl start crypto-bot

# Проверка статуса
sudo systemctl status crypto-bot
```

### Linux (screen)

```bash
# Установите screen
sudo apt install screen

# Создайте сессию
screen -S crypto-bot

# Запустите бота
python main.py

# Отключитесь (Ctrl+A, D)

# Вернуться:
screen -r crypto-bot
```

### Windows (как служба)

Используйте **NSSM** (Non-Sucking Service Manager):
```powershell
nssm install CryptoBot "C:\path\to\venv\Scripts\python.exe" "C:\path\to\main.py"
nssm start CryptoBot
```

---

## 🔐 БЕЗОПАСНОСТЬ

### Защита .env

```bash
# Добавьте в .gitignore
echo ".env" >> .gitignore
echo "*.db" >> .gitignore
```

### Firewall

```bash
# Откройте только Telegram порт (бот сам подключается)
sudo ufw allow 443  # HTTPS
```

---

## 📞 ПОДДЕРЖКА

- **GitHub Issues:** https://github.com/alex21031993/AI-bot/issues
- **Telegram:** Напишите разработчику

---

## 📝 БЫСТРАЯ ШПАРГАЛКА

```bash
# 1. Клонировать
git clone https://github.com/alex21031993/AI-bot.git
cd AI-bot

# 2. Виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить
cp .env.example .env
nano .env  # Заполните токен и ID

# 5. Запустить
python main.py
```

---

**Удачи! 🚀**
