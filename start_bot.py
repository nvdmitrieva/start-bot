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
from datetime import date, datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")
DATA_FILE = "data.json"

logging.basicConfig(level=logging.INFO)


# ── Хранилище данных (файл JSON) ──────────────────────────────────────────────

def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"members": {}, "knowledge_base": [], "tasks": []}


def save_data(data: dict):
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
DIARY_WAITING, KB_WAITING, TASK_WAITING = range(3)


# ── /start ────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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

    keyboard = [
        [InlineKeyboardButton("✅ Отметить микрошаг дня", callback_data="check_step")],
        [InlineKeyboardButton("📸 +1 Instagram-действие", callback_data="add_post")],
        [InlineKeyboardButton("📓 Записать победу дня", callback_data="diary")],
        [InlineKeyboardButton("📋 Мои задачи", callback_data="tasks")],
        [InlineKeyboardButton("📚 База знаний", callback_data="kb_menu")],
        [InlineKeyboardButton("📊 Мой прогресс", callback_data="progress")],
    ]
    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
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

    bar_done = "🟩" * done_days + "⬜" * (30 - done_days)

    text = (
        f"📊 *Твой прогресс*\n\n"
        f"День: {current_day}/30\n"
        f"Микрошаги: {done_days}/30\n"
        f"Instagram-действия: {posts}\n"
        f"Серия дней: {streak} 🔥\n\n"
        f"*30 дней:*\n{bar_done[:30]}"
    )
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=back_keyboard())


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


# ── Instagram +1 ──────────────────────────────────────────────────────────────

async def add_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    member = get_member(data, query.from_user.id, query.from_user.first_name)
    member["posts_count"] = member.get("posts_count", 0) + 1
    save_data(data)
    text = (
        f"📸 *+1 Instagram-действие!*\n\n"
        f"Всего публикаций: {member['posts_count']}\n\n"
        f"Помни принцип: показываешь путь, не результат."
    )
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=back_keyboard())


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
    await update.message.reply_text(
        f"✨ *Победа записана!*\n\n_{entry['text']}_\n\nУдачи завтра!",
        parse_mode="Markdown"
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
    await update.message.reply_text(
        f"✅ Задача добавлена:\n_{task['text']}_",
        parse_mode="Markdown"
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
    await update.message.reply_text(
        f"📚 Запись добавлена:\n*{title}* — _{tag}_",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ── /team — общая статистика команды ─────────────────────────────────────────

async def cmd_team(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    members = data.get("members", {})
    if not members:
        await update.message.reply_text("В команде пока никого нет. Начните с /start!")
        return

    lines = ["👥 *Команда СТАРТ*\n"]
    for uid, m in members.items():
        done = len(m.get("completed_days", []))
        posts = m.get("posts_count", 0)
        streak = m.get("streak", 0)
        lines.append(f"*{m['name']}* — {done}/30 шагов · {posts} постов · {streak}🔥")

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

    keyboard = [
        [InlineKeyboardButton("✅ Отметить микрошаг дня", callback_data="check_step")],
        [InlineKeyboardButton("📸 +1 Instagram-действие", callback_data="add_post")],
        [InlineKeyboardButton("📓 Записать победу дня", callback_data="diary")],
        [InlineKeyboardButton("📋 Мои задачи", callback_data="tasks")],
        [InlineKeyboardButton("📚 База знаний", callback_data="kb_menu")],
        [InlineKeyboardButton("📊 Мой прогресс", callback_data="progress")],
    ]
    await query.edit_message_text(
        f"🎮 *СТАРТ — Моя игра, мой старт*\n\nДень *{current_day} из 30*. Выбери действие:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено. Вернись через /start")
    return ConversationHandler.END


# ── Запуск бота ───────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

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
    app.add_handler(CommandHandler("team", cmd_team))
    app.add_handler(diary_conv)
    app.add_handler(kb_conv)
    app.add_handler(task_conv)
    app.add_handler(CallbackQueryHandler(show_progress, pattern="^progress$"))
    app.add_handler(CallbackQueryHandler(check_step, pattern="^check_step$"))
    app.add_handler(CallbackQueryHandler(add_post, pattern="^add_post$"))
    app.add_handler(CallbackQueryHandler(show_tasks, pattern="^tasks$"))
    app.add_handler(CallbackQueryHandler(kb_menu, pattern="^kb_menu$"))
    app.add_handler(CallbackQueryHandler(go_back, pattern="^back$"))

    print("Бот запущен. Нажми Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()
