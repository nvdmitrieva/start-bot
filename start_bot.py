"""
Telegram-бот «СТАРТ — Моя игра, мой старт»
Для команды PM-International.

Установка:
    pip install python-telegram-bot==20.7

Запуск:
    1. Создай бота через @BotFather → получи TOKEN
    2. Вставь токен в переменную BOT_TOKEN ниже
    3. python start_bot.py

Бесплатный хостинг: https://railway.app или https://render.com
"""

import json
import os
import logging
import urllib.request
import urllib.error
from datetime import date, datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ── 30 заданий дня ────────────────────────────────────────────────────────────
DAILY_TASKS = {
    1:  ("📋 Запиши 20 имён — всех, кого знаешь. Мамы из школы, коллеги, подруги, соседки. Без оценки «подойдёт / не подойдёт». Просто имена.",
         "📸 Instagram: Сделай фото «Начинаю игру» — стакан воды + Optimal Set. Подпись: «День 1. Я начала.»"),
    2:  ("📋 Изучи Optimal Set: состав, как принимать, зачем нужен каждый продукт. Запиши 3 факта, которые тебя удивили.",
         "📸 Stories: «Попробовала [название] — вот что заметила за первые два дня...» Честно, без рекламы."),
    3:  ("📋 Прочитай свою историю: почему ты пришла в PM. Запиши в 3 предложения. Это будет твой главный инструмент в разговорах.",
         "📸 Пост или Stories: твоя история в 3 предложениях. Почему ты здесь."),
    4:  ("📋 Выбери 5 имён из списка 20. Это люди, которым ты напишешь на этой неделе. Не пиши ещё — только выбери и запиши.",
         "📸 Фото: что у тебя на рабочем столе / в сумке / на кухне. Твой обычный день. Без постановки."),
    5:  ("📋 Напиши первое сообщение одному человеку из пяти. Просто поздоровайся и спроси, как дела. Никакого предложения пока.",
         "📸 Stories: «Что меня держит в тонусе — покажу сегодня вечером». Открытая петля."),
    6:  ("📋 Напиши второму и третьему. Тот же подход — без предложения. Просто восстанови контакт.",
         "📸 Stories вечером: «Вот моё утро без кофе». Покажи Activize или ритуал."),
    7:  ("📋 ДЕНЬ ИТОГОВ. Заполни мини-таблицу: сколько написала / сколько ответили / как себя чувствую. Это твоя точка А.",
         "📸 Пост итогов недели: «7 дней назад я начала. Вот что изменилось...» 3–5 строк честно."),
    8:  ("📋 Напиши четвёртому и пятому из списка. По-прежнему без предложения — спроси про здоровье, усталость, образ жизни.",
         "📸 Stories: «Один вопрос, который я задала себе на старте» — и ответ."),
    9:  ("📋 Выбери ещё 5 имён из списка. Итого у тебя уже 10 активных контактов.",
         "📸 Пост: «Что я пью каждое утро и зачем». Без продажи — просто личный опыт."),
    10: ("📋 Из тех, кто ответил — найди одного, кому можно рассказать про продукт. Задай вопрос: «Тебя бесит усталость / плохой сон?»",
         "📸 Stories-опрос: «Что тебя больше беспокоит прямо сейчас?» + варианты ответов."),
    11: ("📋 Проведи первый короткий разговор — 10 минут. Не презентация. Расскажи историю и спроси: «Хочешь, расскажу подробнее?»",
         "📸 Stories: «Провела первый разговор. Вот что почувствовала». Эмоция, не результат."),
    12: ("📋 Если сказали «да» — отправь ссылку на продукт. Если «нет» — запиши в список и вернись через 2–3 недели.",
         "📸 Пост: «Три вещи, которые изменились за 12 дней». Честно и конкретно."),
    13: ("📋 Отправь первый Follow-Up тому, кому отправила информацию. «Посмотрела? Есть вопросы?» — и больше ничего.",
         "📸 Stories: лайфстайл. Ты — обычный день. Не про бизнес. Просто жизнь."),
    14: ("📋 ДЕНЬ ИТОГОВ. Сколько разговоров? Сколько отправила информацию? Сколько ждут ответа? Таблица в блокноте.",
         "📸 Пост итогов второй недели. Что далось легко, что — сложно."),
    15: ("📋 Составь список 5 новых имён — люди, с которыми давно не общалась. Напиши первому.",
         "📸 Первый Reels или короткое видео. Тема: «Почему я выбрала этот продукт». До 60 секунд."),
    16: ("📋 Спроси у тех, кто уже пробовал продукт: «Как твои ощущения?» — и собери мини-отзыв.",
         "📸 Stories: «Что говорят те, кто попробовал». Репост или цитата с разрешения."),
    17: ("📋 Попробуй рассказать о бизнес-возможности одной женщине. Напиши: «Могу поделиться кое-чем интересным?»",
         "📸 Пост: «Что такое мой бизнес на самом деле». Без громких слов — просто как ты это видишь."),
    18: ("📋 Проведи второй разговор о бизнесе. Используй свою историю + вопрос: «Тебе актуально дополнительное?»",
         "📸 Stories: «Сегодня был сложный разговор. Вот что я из него взяла»."),
    19: ("📋 Выпиши всех, кто сейчас «думает» или «не ответил». Сделай Follow-Up — просто напиши: «Привет, как ты?»",
         "📸 Пост: твоя динамика за 19 дней. Что изменилось."),
    20: ("📋 Пригласи одного человека на встречу или Zoom — не обязательно купить, просто посмотреть.",
         "📸 Stories-вопрос: «Если бы у тебя был дополнительный час в день — на что бы потратила?»"),
    21: ("📋 ДЕНЬ ИТОГОВ. Считаем: контакты / разговоры / отправленные материалы / «да» / «нет» / «думаю».",
         "📸 Пост итогов третьей недели. Самое неожиданное открытие."),
    22: ("📋 Напиши спонсору: «Вот мои цифры за 3 недели» — и поделись статистикой. Это запрос на обратную связь.",
         "📸 Пост или Reels: «3 недели в бизнесе — вот что я узнала о себе». Личное."),
    23: ("📋 Составь список тех, кого хочешь пригласить на презентацию. Минимум 5 имён.",
         "📸 Stories: анонс. «Скоро расскажу кое-что важное — следи». Без деталей."),
    24: ("📋 Разошли личные приглашения на презентацию — персонально каждой: «Я подумала о тебе, потому что...»",
         "📸 Пост: «Почему я приглашаю именно тебя». Обращение к подписчикам."),
    25: ("📋 Проведи Follow-Up по тем, кто «думает» с первой недели.",
         "📸 Stories: прогрев перед презентацией. «Покажу, как это устроено изнутри»."),
    26: ("📋 Подготовься к презентации: прочитай материалы, освежи цифры маркетинг-плана.",
         "📸 Reels или пост: твоя история от дня 1 до дня 26. Было / стало."),
    27: ("📋 Повтори утренний ритуал осознанно: Optimal Set + намерение + правило дня. Это теперь твоя система навсегда.",
         "📸 Stories: «День 27. Я всё ещё здесь». Просто факт. Это мощно."),
    28: ("📋 Напиши одному человеку, который отказал в начале. Не с предложением — просто: «Привет, как ты?»",
         "📸 Пост: «Что изменилось во мне за 28 дней». Не в бизнесе — в тебе."),
    29: ("📋 Пройди мини-тест: могу ли я рассказать о продукте за 2 минуты? О бизнесе за 2 минуты? Запиши голосом — послушай.",
         "📸 Stories: «Завтра — финал. Покажу итоги 30 дней»."),
    30: ("📋 ДЕНЬ ИТОГОВ ИГРЫ. Заполни итоговую таблицу. Сравни с точкой А на день 7.",
         "📸 Пост итогов 30 дней. Честно, с цифрами. Это твой самый сильный контент."),
}

BOT_TOKEN   = os.environ.get("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")
JSONBIN_KEY = os.environ.get("JSONBIN_KEY", "")   # X-Master-Key от jsonbin.io
JSONBIN_BIN = os.environ.get("JSONBIN_BIN", "")   # ID созданного бина
DATA_FILE   = "data.json"                          # локальный fallback
ADMIN_ID    = int(os.environ.get("ADMIN_ID", "180068454"))

logging.basicConfig(level=logging.INFO)


# ── Хранилище данных (JSONBin.io или локальный файл) ─────────────────────────

EMPTY_DATA = {"members": {}, "knowledge_base": [], "tasks": []}


def load_data() -> dict:
    # Пробуем JSONBin
    if JSONBIN_KEY and JSONBIN_BIN:
        try:
            req = urllib.request.Request(
                f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN}/latest",
                headers={"X-Master-Key": JSONBIN_KEY}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())["record"]
        except Exception as e:
            logging.warning(f"JSONBin load error: {e}")
    # Fallback — локальный файл
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return dict(EMPTY_DATA)


def save_data(data: dict):
    # Сохраняем в JSONBin
    if JSONBIN_KEY and JSONBIN_BIN:
        try:
            payload = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(
                f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN}",
                data=payload,
                headers={
                    "X-Master-Key": JSONBIN_KEY,
                    "Content-Type": "application/json"
                },
                method="PUT"
            )
            urllib.request.urlopen(req, timeout=10)
            return
        except Exception as e:
            logging.warning(f"JSONBin save error: {e}")
    # Fallback — локальный файл
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_member(data: dict, user_id: int, name: str) -> dict:
    uid = str(user_id)
    if uid not in data["members"]:
        data["members"][uid] = {
            "name": name,
            "start_date": str(date.today()),
            "completed_days": [],
            "posts_count": 0,
            "streak": 0,
            "diary": [],
        }
        save_data(data)
    return data["members"][uid]


# ── Состояния ConversationHandler ─────────────────────────────────────────────
DIARY_WAITING, KB_WAITING, TASK_WAITING, REPORT_WAITING, STAT_WAITING = range(5)


# ── /myid — показать свой Telegram ID ────────────────────────────────────────

async def cmd_myid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(
        f"Твой Telegram ID: `{uid}`\n\nЕсли /admin не работает — пришли этот ID мне.",
        parse_mode="Markdown"
    )


# ── /start ────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # Сбрасываем любой активный диалог
    ctx.user_data.clear()
    data = load_data()
    user = update.effective_user
    member = get_member(data, user.id, user.first_name)

    start_dt = datetime.strptime(member["start_date"], "%Y-%m-%d").date()
    current_day = (date.today() - start_dt).days + 1
    current_day = min(current_day, 30)

    text = (
        f"🎮 *СТАРТ — Моя игра, мой старт*\n\n"
        f"Привет, {member['name']}! Сегодня *день {current_day} из 30*.\n\n"
        f"Выбери действие:"
    )

    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )


# ── Прогресс ──────────────────────────────────────────────────────────────────

async def show_progress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    member = get_member(data, query.from_user.id, query.from_user.first_name)

    start_dt = datetime.strptime(member["start_date"], "%Y-%m-%d").date()
    current_day = min((date.today() - start_dt).days + 1, 30)
    done_days = len(member["completed_days"])
    posts = member["posts_count"]
    streak = member["streak"]

    activators = member.get("activators", 0)
    contacts = member.get("contacts", 0)
    meet1 = member.get("meet1", 0)
    meet2 = member.get("meet2", 0)
    invites = member.get("invites", 0)
    came = member.get("came", 0)
    partners = member.get("partners", 0)
    clients = member.get("clients", 0)
    bar_done = "🟩" * done_days + "⬜" * (30 - done_days)

    text = (
        f"📊 *Твой прогресс*\n\n"
        f"День: {current_day}/30\n"
        f"Микрошаги: {done_days}/30\n"
        f"Серия дней: {streak} 🔥\n"
        f"Активаторы: {activators} 🏆\n\n"
        f"*Воронка:*\n"
        f"📞 Контакты: {contacts}\n"
        f"🤝 Встречи 1:1: {meet1}\n"
        f"👥 Встречи 2:1: {meet2}\n"
        f"📨 Приглашения: {invites}\n"
        f"🎤 Пришло: {came}\n"
        f"🤝 Партнёры: {partners}\n"
        f"🛍 Клиенты: {clients}\n\n"
        f"*30 дней:*\n{bar_done}"
    )
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=back_keyboard())


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Задание дня", callback_data="zadanie")],
        [InlineKeyboardButton("✅ Отметить микрошаг дня", callback_data="check_step")],
        [InlineKeyboardButton("📞 Контакты в день", callback_data="stat_contacts"),
         InlineKeyboardButton("🤝 Встреча 1:1", callback_data="stat_meet1")],
        [InlineKeyboardButton("👥 Встреча 2:1", callback_data="stat_meet2"),
         InlineKeyboardButton("📨 Приглашение на презентацию", callback_data="stat_invite")],
        [InlineKeyboardButton("🎤 Пришло на презентацию", callback_data="stat_came")],
        [InlineKeyboardButton("🤝 Регистрация партнёр", callback_data="stat_partner"),
         InlineKeyboardButton("🛍 Регистрация клиент", callback_data="stat_client")],
        [InlineKeyboardButton("📓 Записать победу дня", callback_data="diary")],
        [InlineKeyboardButton("🧠 ИИ-Коуч", url="https://chatgpt.com/g/g-6a16e919103c819194d07d642d4897b0-ii-kouch"),
         InlineKeyboardButton("🤖 Помощник партнёра", url="https://chatgpt.com/g/g-68752fa0d6e08191a9a82c4506f374f5-pomoshchnik-partneru-pm")],
        [InlineKeyboardButton("📚 База знаний", callback_data="kb_menu"),
         InlineKeyboardButton("📊 Мой прогресс", callback_data="progress")],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="back")]])


# ── Отметить микрошаг ─────────────────────────────────────────────────────────

async def check_step(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    member = get_member(data, query.from_user.id, query.from_user.first_name)

    today = str(date.today())
    if today in member["completed_days"]:
        text = "Ты уже отметила микрошаг сегодня! 🎉\nЗавтра снова здесь."
    else:
        member["completed_days"].append(today)
        member["streak"] = member.get("streak", 0) + 1
        save_data(data)
        done = len(member["completed_days"])
        text = (
            f"✅ *День отмечен!*\n\n"
            f"Выполнено {done} из 30 дней.\n"
            f"Серия: {member['streak']} дней подряд 🔥\n\n"
            f"Одна победа в день — и через 30 дней ты другой человек."
        )
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=back_keyboard())


# ── Статистика воронки ────────────────────────────────────────────────────────

STAT_CONFIG = {
    "stat_contacts": ("📞", "Контакт записан!", "contacts", "контактов сегодня"),
    "stat_meet1":    ("🤝", "Встреча 1:1 отмечена!", "meet1", "встреч 1:1"),
    "stat_meet2":    ("👥", "Встреча 2:1 отмечена!", "meet2", "встреч 2:1"),
    "stat_invite":   ("📨", "Приглашение отправлено!", "invites", "приглашений на презентацию"),
    "stat_came":     ("🎤", "Участник отмечен!", "came", "пришло на презентацию"),
    "stat_partner":  ("🤝", "Партнёр зарегистрирован! 🎉", "partners", "партнёров"),
    "stat_client":   ("🛍", "Клиент зарегистрирован! 🎉", "clients", "клиентов"),
}

async def add_stat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    emoji, title, key, label = STAT_CONFIG[action]

    ctx.user_data["stat_action"] = action
    await query.edit_message_text(
        f"{emoji} *{title}*\n\nСколько? Напиши цифру:",
        parse_mode="Markdown"
    )
    return STAT_WAITING


async def stat_save(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or int(text) < 1:
        await update.message.reply_text("Напиши число, например: 2")
        return STAT_WAITING

    count = int(text)
    action = ctx.user_data.get("stat_action")
    emoji, title, key, label = STAT_CONFIG[action]

    data = load_data()
    member = get_member(data, update.effective_user.id, update.effective_user.first_name)
    member[key] = member.get(key, 0) + count
    member["activators"] = member.get("activators", 0) + count
    save_data(data)

    total_key = member[key]
    total_act = member["activators"]

    await update.message.reply_text(
        f"{emoji} *+{count} {label}!*\n"
        f"Всего {label}: {total_key}\n\n"
        f"🏆 *+{count} активаторов!* Всего: {total_act}",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END


# ── Дневник победы ────────────────────────────────────────────────────────────

async def diary_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📓 *Дневник «Сегодня день успеха»*\n\n"
        "Напиши одну победу сегодняшнего дня — любую, маленькую или большую:",
        parse_mode="Markdown"
    )
    return DIARY_WAITING


async def diary_save(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    member = get_member(data, update.effective_user.id, update.effective_user.first_name)
    entry = {
        "date": str(date.today()),
        "text": update.message.text
    }
    member.setdefault("diary", []).append(entry)
    save_data(data)

    start_dt = datetime.strptime(member["start_date"], "%Y-%m-%d").date()
    current_day = min((date.today() - start_dt).days + 1, 30)

    keyboard = [
        [InlineKeyboardButton("🎯 Задание дня", callback_data="zadanie")],
        [InlineKeyboardButton("✅ Отметить микрошаг дня", callback_data="check_step")],
        [InlineKeyboardButton("📸 +1 Instagram-действие", callback_data="add_post")],
        [InlineKeyboardButton("📓 Записать победу дня", callback_data="diary")],
        [InlineKeyboardButton("📋 Мои задачи", callback_data="tasks")],
        [InlineKeyboardButton("📚 База знаний", callback_data="kb_menu")],
        [InlineKeyboardButton("📊 Мой прогресс", callback_data="progress")],
    ]
    await update.message.reply_text(
        f"✨ *Победа записана!*\n\n_{entry['text']}_\n\nУдачи завтра! 💪\n\n"
        f"*День {current_day} из 30* — выбери следующее действие:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


# ── Задачи ────────────────────────────────────────────────────────────────────

async def show_tasks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    tasks = data.get("tasks", [])
    open_tasks = [t for t in tasks if not t.get("done")]

    if not open_tasks:
        text = "📋 *Задачи команды*\n\nПока задач нет. Отлично!"
    else:
        lines = [f"📋 *Задачи команды*\n"]
        for i, t in enumerate(open_tasks[:10], 1):
            lines.append(f"{i}. {t['text']} _{t.get('author', '')}_ ")
        text = "\n".join(lines)

    keyboard = [
        [InlineKeyboardButton("+ Добавить задачу", callback_data="task_add")],
        [InlineKeyboardButton("← Назад", callback_data="back")],
    ]
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


async def task_add_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Напиши текст новой задачи:")
    return TASK_WAITING


async def task_add_save(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    task = {
        "text": update.message.text,
        "author": update.effective_user.first_name,
        "date": str(date.today()),
        "done": False
    }
    data.setdefault("tasks", []).append(task)
    save_data(data)
    keyboard = [[InlineKeyboardButton("← В главное меню", callback_data="back")]]
    await update.message.reply_text(
        f"✅ Задача добавлена:\n_{task['text']}_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


# ── База знаний ───────────────────────────────────────────────────────────────

async def kb_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    kb = data.get("knowledge_base", [])

    lines = ["📚 *База знаний команды*\n"]
    if not kb:
        lines.append("Пока пусто. Добавь первую запись!")
    else:
        for item in kb[-8:]:
            lines.append(f"• *{item['title']}* — _{item.get('tag', '')}_")

    keyboard = [
        [InlineKeyboardButton("+ Добавить запись", callback_data="kb_add")],
        [InlineKeyboardButton("← Назад", callback_data="back")],
    ]
    await query.edit_message_text(
        "\n".join(lines), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def kb_add_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Напиши запись в формате:\n\n*Название | Категория*\n\nПример:\n_Скрипт первого звонка | Скрипты_",
        parse_mode="Markdown"
    )
    return KB_WAITING


async def kb_add_save(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    text = update.message.text
    parts = text.split("|", 1)
    title = parts[0].strip()
    tag = parts[1].strip() if len(parts) > 1 else "Общее"

    entry = {
        "title": title,
        "tag": tag,
        "author": update.effective_user.first_name,
        "date": str(date.today())
    }
    data.setdefault("knowledge_base", []).append(entry)
    save_data(data)
    keyboard = [[InlineKeyboardButton("← В главное меню", callback_data="back")]]
    await update.message.reply_text(
        f"📚 Запись добавлена:\n*{title}* — _{tag}_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


# ── /team — общая статистика команды ─────────────────────────────────────────

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У тебя нет доступа к этой команде.")
        return

    data = load_data()
    members = data.get("members", {})
    if not members:
        await update.message.reply_text("Участников пока нет.")
        return

    for uid, m in members.items():
        start_dt = datetime.strptime(m["start_date"], "%Y-%m-%d").date()
        current_day = min((date.today() - start_dt).days + 1, 30)
        done = len(m.get("completed_days", []))
        streak = m.get("streak", 0)
        activators = m.get("activators", 0)
        contacts = m.get("contacts", 0)
        meet1 = m.get("meet1", 0)
        meet2 = m.get("meet2", 0)
        invites = m.get("invites", 0)
        came = m.get("came", 0)
        partners = m.get("partners", 0)
        clients = m.get("clients", 0)

        # Последняя активность
        last_day = max(m.get("completed_days", ["—"])) if m.get("completed_days") else "—"

        text = (
            f"👤 *{m['name']}*\n"
            f"Telegram ID: `{uid}`\n"
            f"Старт: {m['start_date']} · День {current_day}/30\n"
            f"Последняя активность: {last_day}\n\n"
            f"✅ Микрошаги: {done}/30\n"
            f"🔥 Серия: {streak} дней\n"
            f"🏆 Активаторы: {activators}\n\n"
            f"*Воронка:*\n"
            f"📞 Контакты: {contacts}\n"
            f"🤝 Встречи 1:1: {meet1} · 2:1: {meet2}\n"
            f"📨 Приглашения: {invites}\n"
            f"🎤 Пришло: {came}\n"
            f"🤝 Партнёры: {partners}\n"
            f"🛍 Клиенты: {clients}"
        )
        await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_team(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    members = data.get("members", {})
    if not members:
        await update.message.reply_text("В команде пока никого нет. Начните с /start!")
        return

    lines = ["👥 *Команда СТАРТ*\n"]
    for uid, m in members.items():
        done = len(m.get("completed_days", []))
        streak = m.get("streak", 0)
        activators = m.get("activators", 0)
        contacts = m.get("contacts", 0)
        invites = m.get("invites", 0)
        came = m.get("came", 0)
        partners = m.get("partners", 0)
        clients = m.get("clients", 0)
        lines.append(
            f"*{m['name']}* — {done}/30 · {streak}🔥 · {activators}🏆\n"
            f"  📞{contacts} · 📨{invites} · 🎤{came} · 🤝{partners} · 🛍{clients}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── Навигация «назад» ─────────────────────────────────────────────────────────

async def go_back(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = load_data()
    member = get_member(data, user.id, user.first_name)

    start_dt = datetime.strptime(member["start_date"], "%Y-%m-%d").date()
    current_day = min((date.today() - start_dt).days + 1, 30)

    await query.edit_message_text(
        f"🎮 *СТАРТ — Моя игра, мой старт*\n\nДень *{current_day} из 30*. Выбери действие:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено. Вернись через /start")
    return ConversationHandler.END


# ── /zadanie — задание текущего дня ──────────────────────────────────────────

async def cmd_zadanie(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    member = get_member(data, update.effective_user.id, update.effective_user.first_name)

    start_dt = datetime.strptime(member["start_date"], "%Y-%m-%d").date()
    current_day = min((date.today() - start_dt).days + 1, 30)

    pm_task, ig_task = DAILY_TASKS.get(current_day, ("Все 30 дней пройдены! 🎉", ""))

    text = (
        f"🎯 *День {current_day} из 30*\n\n"
        f"{pm_task}\n\n"
        f"{ig_task}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


def zadanie_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Отчитаться о выполнении", callback_data="report")],
        [InlineKeyboardButton("← Назад", callback_data="back")],
    ])


async def show_zadanie(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    member = get_member(data, query.from_user.id, query.from_user.first_name)

    start_dt = datetime.strptime(member["start_date"], "%Y-%m-%d").date()
    current_day = min((date.today() - start_dt).days + 1, 30)

    pm_task, ig_task = DAILY_TASKS.get(current_day, ("Все 30 дней пройдены! 🎉", ""))

    text = (
        f"🎯 *День {current_day} из 30*\n\n"
        f"{pm_task}\n\n"
        f"{ig_task}"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=zadanie_keyboard())


# ── Отчёт о выполнении ────────────────────────────────────────────────────────

ENCOURAGEMENTS = [
    "Ты сделала это! Один шаг — и ты уже не та, что вчера.",
    "Вот это движение! Именно так строится результат — день за днём.",
    "Гордись собой. Сегодня ты выбрала действие вместо откладывания.",
    "Это и есть настоящая игра. Ты в ней!",
    "Каждый шаг считается. Этот — тоже.",
    "Сделала — значит растёшь. Так и работает система.",
    "Один день — один шаг. И ты его сделала. Это всё, что нужно.",
]

import random

async def report_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📤 *Отчёт о выполнении*\n\n"
        "Пришли скрин выполненного задания или ссылку на пост в Instagram:",
        parse_mode="Markdown"
    )
    return REPORT_WAITING


async def report_save(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = update.effective_user
    member = get_member(data, user.id, user.first_name)

    start_dt = datetime.strptime(member["start_date"], "%Y-%m-%d").date()
    current_day = min((date.today() - start_dt).days + 1, 30)

    # Сохраняем отчёт
    report = {
        "date": str(date.today()),
        "day": current_day,
        "type": "photo" if update.message.photo else "text",
        "content": update.message.caption or update.message.text or "скрин"
    }
    member.setdefault("reports", []).append(report)

    # Начисляем активатор
    member["activators"] = member.get("activators", 0) + 1
    save_data(data)

    encouragement = random.choice(ENCOURAGEMENTS)
    total = member["activators"]


    await update.message.reply_text(
        f"🏆 *+1 Активатор!* Всего: {total} 🔥\n\n"
        f"_{encouragement}_\n\n"
        f"*День {current_day} из 30* — что дальше?",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END


# ── Утренняя рассылка в 9:00 ─────────────────────────────────────────────────

async def morning_broadcast(ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    for uid, member in data.get("members", {}).items():
        try:
            start_dt = datetime.strptime(member["start_date"], "%Y-%m-%d").date()
            current_day = min((date.today() - start_dt).days + 1, 30)
            pm_task, ig_task = DAILY_TASKS.get(current_day, ("Все 30 дней пройдены! 🎉", ""))

            text = (
                f"☀️ Доброе утро, {member['name']}!\n\n"
                f"*День {current_day} из 30*\n\n"
                f"{pm_task}\n\n"
                f"{ig_task}\n\n"
                f"Не забудь принять Optimal Set и записать намерение дня 💪"
            )
            await ctx.bot.send_message(chat_id=int(uid), text=text, parse_mode="Markdown")
        except Exception as e:
            logging.warning(f"Не удалось отправить рассылку {uid}: {e}")


# ── Запуск бота ───────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    stat_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_stat, pattern="^stat_")],
        states={STAT_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, stat_save)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    report_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(report_start, pattern="^report$")],
        states={REPORT_WAITING: [
            MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, report_save)
        ]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    diary_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(diary_start, pattern="^diary$")],
        states={DIARY_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, diary_save)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    kb_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(kb_add_start, pattern="^kb_add$")],
        states={KB_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, kb_add_save)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    task_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(task_add_start, pattern="^task_add$")],
        states={TASK_WAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_add_save)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("team", cmd_team))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("zadanie", cmd_zadanie))

    # Утренняя рассылка в 9:00 по Москве (UTC+3 = 06:00 UTC)
    app.job_queue.run_daily(morning_broadcast, time=time(6, 0))
    app.add_handler(stat_conv)
    app.add_handler(report_conv)
    app.add_handler(diary_conv)
    app.add_handler(kb_conv)
    app.add_handler(task_conv)
    app.add_handler(CallbackQueryHandler(show_zadanie, pattern="^zadanie$"))
    app.add_handler(CallbackQueryHandler(show_progress, pattern="^progress$"))
    app.add_handler(CallbackQueryHandler(check_step, pattern="^check_step$"))

    app.add_handler(CallbackQueryHandler(show_tasks, pattern="^tasks$"))
    app.add_handler(CallbackQueryHandler(kb_menu, pattern="^kb_menu$"))
    app.add_handler(CallbackQueryHandler(go_back, pattern="^back$"))

    print("Бот запущен. Нажми Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()
