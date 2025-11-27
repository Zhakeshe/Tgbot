from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


def main_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎁 Подарки")],
            [KeyboardButton(text="👤 Профиль")],
        ],
        resize_keyboard=True
    )
    return kb


def gifts_keyboard(gifts):
    kb = InlineKeyboardMarkup()
    for g in gifts:
        text = f"{g['emoji']} {g['name']} — {g['price']}₸"
        kb.add(InlineKeyboardButton(text=text, callback_data=f"gift:{g['id']}"))
    return kb


def gift_actions_keyboard(gift_id: int):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(text="📥 Отправить себе", callback_data=f"buy:self:{gift_id}")
    )
    kb.add(
        InlineKeyboardButton(text="📤 Отправить другу", callback_data=f"buy:friend:{gift_id}")
    )
    kb.add(
        InlineKeyboardButton(text="◀️ Назад к списку", callback_data="gifts:list")
    )
    return kb
# kb placeholder
