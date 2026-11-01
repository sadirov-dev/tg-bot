
import asyncio
import logging
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.enums import ChatAction

from dify import ask_dify
from storage import (
    load_data,
    save_data,
    get_user,
    add_message,
    get_conversation_id,
    reset_conversation,
    get_history,
    get_message_count,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в файле .env")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Клавиатура
def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Меню",
                    callback_data="menu"
                )
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ Помощь",
                    callback_data="help"
                )
            ]
        ]
    )


@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "дос"

    get_user(user_id)
    reset_conversation(user_id)

    await message.answer(
        f"Саламатсызбы, {name}! 😊\n"
        "Рестораныбызга кош келиңиз!\n\n"
        "Меню, баалар жана тамактардын курамы боюнча "
        "суроолоруңузга жооп берем.",
        reply_markup=main_keyboard()
    )


@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "🤖 Боттун командалары:\n\n"
        "/start — ботту баштоо\n"
        "/help — жардам\n"
        "/new — жаңы диалог\n"
        "/history — акыркы 6 билдирүү\n"
        "/stats — билдирүүлөрдүн саны",
        reply_markup=main_keyboard()
    )


@dp.message(Command("new"))
async def new_handler(message: Message):
    reset_conversation(message.from_user.id)

    await message.answer(
        "✅ Жаңы диалог башталды! Эми сурооңузду берсеңиз болот."
    )


@dp.message(Command("history"))
async def history_handler(message: Message):
    messages = get_history(message.from_user.id, limit=6)

    if not messages:
        await message.answer("Азырынча билдирүүлөр жок.")
        return

    lines = ["📜 Акыркы билдирүүлөр:\n"]

    for item in messages:
        role = "👤 Сиз" if item["role"] == "user" else "🤖 Бот"
        lines.append(f"{role}:\n{item['content']}")

    await message.answer("\n\n".join(lines))


@dp.message(Command("stats"))
async def stats_handler(message: Message):
    count = get_message_count(message.from_user.id)

    await message.answer(
        f"📊 Сиздин сакталган билдирүүлөрүңүздүн саны: {count}"
    )


@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    await callback.message.answer(
        "/start — баштоо\n"
        "/help — жардам\n"
        "/new — жаңы диалог\n"
        "/history — тарых\n"
        "/stats — статистика"
    )
    await callback.answer()



@dp.callback_query(F.data == "menu")
async def menu_callback(callback: CallbackQuery):
    menu_text = (
        "🍽️ **РЕСТОРАНЫБЫЗДЫН МЕНЮСУ**\n\n"
        "🥩 **1. Бешбармак + шорпо**\n"
        "💰 Баасы: 600 сом\n"
        "⚖️ Болжолдуу порция: 600–650 г\n\n"
        "🥟 **2. Манты**\n"
        "💰 Баасы: 340 сом\n"
        "⚖️ Болжолдуу порция: 300–350 г\n"
        "📌 Курамы: камыр, уй эти, пияз, картошка\n\n"
        "🍜 **3. Лагман**\n"
        "💰 Баасы: 340 сом\n"
        "⚖️ Болжолдуу порция: 400–450 г\n\n"
        "🍚 **4. Аш (плов)**\n"
        "💰 Баасы: 340 сом\n"
        "⚖️ Болжолдуу порция: 350–400 г\n\n"
        "😊 Тамактар боюнча кошумча маалымат алуу "
        "үчүн сурооңузду жазыңыз!"
    )

    await callback.message.answer(
        menu_text,
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.message(F.photo)
async def photo_handler(message: Message):
    await message.answer(
        "Кечиресиз, азырынча сүрөттөрдү окуй албайм. "
        "Тамак боюнча сурооңузду текст менен жазыңыз. 😊"
    )


@dp.message(F.text)
async def text_handler(message: Message):
    user_id = message.from_user.id
    question = message.text

    add_message(user_id, "user", question)

    conversation_id = get_conversation_id(user_id)

    try:
        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )

        result = await asyncio.to_thread(
            ask_dify,
            question,
            user_id,
            conversation_id
        )

        answer = result["text"]
        new_conversation_id = result["conversation_id"]

        if not answer:
            answer = "Кечиресиз, жооп ала алган жокмун."

        # Жоопту жана conversation_id сактоо
        add_message(
            user_id,
            "assistant",
            answer,
            new_conversation_id
        )

        await message.answer(answer)

    except Exception:
        logging.exception("Dify bilan байланыш катасы")

        await message.answer(
            "Кечиресиз, азыр жооп берүүдө ката кетти. "
            "Бир аздан кийин кайра аракет кылыңыз."
        )


async def main():
    load_data()

    logging.info("Restaurant bot ишке кирди!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
