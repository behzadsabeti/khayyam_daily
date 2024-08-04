import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler
from api_service import get_random_poem, get_random_poem_recitation, get_random_poem_eng
import schedule
import time
import random
from datetime import datetime, timedelta
import threading
import asyncio
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    filename="newfile.log",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filemode='w'
)
logger = logging.getLogger(__name__)

# Set logging level for httpx to WARNING to reduce verbosity
logging.getLogger("httpx").setLevel(logging.WARNING)

ASK_FOR_LAN, PERSIAN, ENGLISH, NEW_POEM_PER, NEW_POEM_ENG = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info('Received /start command from user: %s', update.effective_user.id)
    reply_keyboard = [["Persian", "English"]]

    await update.message.reply_text(
        """Welcome! Please choose your language:
        لطفا زبان مورد نظر خود را انتخاب کنید:""",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )

    return ASK_FOR_LAN

async def ask_for_lan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info("Language that %s selected: %s", user.first_name, update.message.text)
    language = update.message.text
    if language == "Persian":
        schedule_thread = threading.Thread(target=run_scheduler, args=(update, context, "per"))
        schedule_thread.start()
        logger.info("scheduled to send persian poem")
        reply_keyboard = [["رباعی جدید", "بازگشت به انتخاب زبان"]]

        await update.message.reply_text(
            """
            به ربات <b>هر روز با خیام</b> خوش آمدید. 🌸
این ربات هر روز برای شما (در زمان تصادفی) یک رباعی از خیام به همراه خوانش آن ارسال میکند.
در صورت علاقه میتوانید همین حالا یک رباعی دریافت کنید!

            """,
            parse_mode='HTML',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, resize_keyboard=True
            ),
            )

        return NEW_POEM_PER

    else:
        schedule_thread = threading.Thread(target=run_scheduler, args=(update, context, "eng"))
        schedule_thread.start()
        logger.info("scheduled to send english poem")
        reply_keyboard = [["new poem", "back to choose language"]]

        await update.message.reply_text(
            """
            Welcome to <b>Khayyam Daily</b>🌸
Every day, you'll receive a beautiful poem by Omar Khayyam along with its recitation, immersing you in the timeless wisdom and serene reflections of this great Persian poet.
            """,
            parse_mode='HTML',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, resize_keyboard=True
            ),
            )

        return NEW_POEM_ENG


async def new_poem_per(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logger.info(" %s selected: %s", user.first_name, update.message.text)
    command = update.message.text
    if command == "رباعی جدید":
        poem = get_random_poem()
        logger.info('Sending poem to user: %s', user.first_name)
        reply_keyboard = [["رباعی جدید", "بازگشت به انتخاب زبان"]]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=poem["plain_text"])
        await context.bot.send_voice(chat_id=update.effective_chat.id, voice=get_random_poem_recitation(poem["id"]),
        reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, resize_keyboard=True
            ),
            )
        return NEW_POEM_PER

    else:
        reply_keyboard = [["Persian", "English"]]

        await update.message.reply_text(
            """Welcome! Please choose your language:
            لطفا زبان مورد نظر خود را انتخاب کنید:""",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, resize_keyboard=True
            ),
        )

        return ASK_FOR_LAN


async def new_poem_eng(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user
    logger.info(" %s selected: %s", user.first_name, update.message.text)

    command = update.message.text
    if command == "new poem":
        poem = get_random_poem_eng()
        logger.info('Sending poem to user: %s', user.first_name)
        reply_keyboard = [["new poem", "back to choose language"]]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=poem,
        reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, resize_keyboard=True
            ),
            )
        return NEW_POEM_ENG

    else:
        reply_keyboard = [["Persian", "English"]]

        await update.message.reply_text(
            """Welcome! Please choose your language:
            لطفا زبان مورد نظر خود را انتخاب کنید:""",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, resize_keyboard=True
            ),
        )

        return ASK_FOR_LAN


async def send_poem(update: Update, context: ContextTypes.DEFAULT_TYPE, lang):
    if lang == "per":
        poem = get_random_poem()
        await context.bot.send_message(chat_id=update.effective_chat.id, text="<b> رباعی امروز: </b>", parse_mode='HTML')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=poem["plain_text"])
        await context.bot.send_voice(chat_id=update.effective_chat.id, voice=get_random_poem_recitation(poem["id"]))
    else:
        poem = get_random_poem_eng()
        await context.bot.send_message(chat_id=update.effective_chat.id, text="<b>Today's poem:</b>", parse_mode='HTML')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=poem)

def send_periodic_message(update, context, lang):
    # Run the async function within the current event loop
    asyncio.run(send_poem(update, context, lang))

def schedule_random_time(update, context, chosen_lang):
    # Randomly generate an hour and minute
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)

    # Format the time
    random_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    logger.info("schedule to send {} poem in {}".format(chosen_lang, random_time))
    # Schedule the job at the random time with parameters
    schedule.every().day.at(random_time.strftime("%H:%M")).do(send_periodic_message, update=update, context=context, lang=chosen_lang)

    print(f"Job scheduled for: {random_time.strftime('%H:%M')}")

def run_scheduler(update, context, chosen_lang):
    while True:

        # Schedule the job for a random time
        schedule_random_time(update, context, chosen_lang)

        # Wait until the next day to reschedule
        while True:
            schedule.run_pending()
            time.sleep(1)
            if datetime.now().hour == 0 and datetime.now().minute == 0:
                break

        # Cancel all jobs after a day
        for job in schedule.jobs:
            schedule.cancel_job(job)


if __name__ == '__main__':
    load_dotenv()
    bot_token = os.getenv("TOKEN")
    application = ApplicationBuilder().token(bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_FOR_LAN: [MessageHandler(filters.Regex("^(Persian|English)$"), ask_for_lan)],
            NEW_POEM_PER: [MessageHandler(filters.Regex("^(رباعی جدید|بازگشت به انتخاب زبان)$"), new_poem_per)],
            NEW_POEM_ENG: [MessageHandler(filters.Regex("^(new poem|back to choose language)$"), new_poem_eng)],

        },
        fallbacks=[CommandHandler("cancel", start), CommandHandler("start", start),],
    )

    application.add_handler(conv_handler)


    logger.info('Bot started')
    application.run_polling()


