import datetime
import os

import pytz
import configparser
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


# Caricamento token Telegram
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Lista compleanni (Giorno, Mese, Nome)
BIRTHDAYS = [
    {"day": 26, "month": 1, "name": "Antonio"},
    {"day": 12, "month": 2, "name": "Raissa"},
    {"day": 21, "month": 4, "name": "Lucia"},
    {"day": 11, "month": 5, "name": "Lola"},
    {"day": 23, "month": 6, "name": "Sofia"},
    {"day": 5, "month": 7, "name": "Daniela"},
    {"day": 11, "month": 7, "name": "Dario"},
    {"day": 21, "month": 7, "name": "Sergio"},
    {"day": 22, "month": 7, "name": "Caterina"},
    {"day": 15, "month": 9, "name": "Mario"},
    {"day": 20, "month": 9, "name": "Bianca"},
    {"day": 10, "month": 10, "name": "Nadin"},
    {"day": 7, "month": 11, "name": "Rino"},
    {"day": 19, "month": 11, "name": "Simona"},
]

MONTH_NAMES = {
    1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
    5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
    9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
}

ROME_TZ = pytz.timezone("Europe/Rome")


def get_birthday_dates(today):
    """Calcola le date effettive per l'anno corrente o successivo/precedente per ogni compleanno."""
    dated_birthdays = []
    for b in BIRTHDAYS:
        # Prova anno corrente, poi anno prossimo o precedente
        for year_offset in [-1, 0, 1]:
            try:
                date_val = datetime.date(today.year + year_offset, b["month"], b["day"])
                dated_birthdays.append({"name": b["name"], "date": date_val, "day": b["day"], "month": b["month"]})
            except ValueError:
                pass
    return dated_birthdays


# Comando /nextbday
async def next_bday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(ROME_TZ).date()
    all_bdays = get_birthday_dates(today)

    # Filtra i compleanni da oggi in poi
    upcoming = [b for b in all_bdays if b["date"] >= today]
    upcoming.sort(key=lambda x: x["date"])

    next_person = upcoming[0]
    date_str = f"{next_person['day']} {MONTH_NAMES[next_person['month']]}"
    await update.message.reply_text(f"Il prossimo compleanno è di {next_person['name']} il {date_str}!")


# Comando /latestbday
async def latest_bday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(ROME_TZ).date()
    all_bdays = get_birthday_dates(today)

    # Filtra i compleanni passati fino ad oggi
    past = [b for b in all_bdays if b["date"] <= today]
    past.sort(key=lambda x: x["date"], reverse=True)

    latest_person = past[0]
    date_str = f"{latest_person['day']} {MONTH_NAMES[latest_person['month']]}"
    await update.message.reply_text(f"Il compleanno più recente è stato di {latest_person['name']} il {date_str}!")


# Controllo giornaliero a mezzanotte
async def check_birthdays(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    today = datetime.datetime.now(ROME_TZ).date()

    for b in BIRTHDAYS:
        if b["day"] == today.day and b["month"] == today.month:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Hey, è il compleanno di {b['name']}! Auguriiii!"
            )


# Registrazione automatica del gruppo al primo comando inviato
async def register_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    job_name = f"birthday_job_{chat_id}"

    # Controlla se il job è già presente
    current_jobs = context.job_queue.get_jobs_by_name(job_name)
    if not current_jobs:
        # Schedula il controllo ogni giorno a mezzanotte (ora italiana)
        midnight = datetime.time(hour=0, minute=0, second=0, tzinfo=ROME_TZ)
        context.job_queue.run_daily(
            check_birthdays,
            time=midnight,
            chat_id=chat_id,
            name=job_name
        )


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Middleware rapido per assicurarsi che il job automatico sia registrato
    app.add_handler(CommandHandler("nextbday", next_bday))
    app.add_handler(CommandHandler("latestbday", latest_bday))

    print("Bot avviato...")
    app.run_polling()