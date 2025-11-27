# main code placeholder
import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .config import BOT_TOKEN, ADMIN_IDS, KASPI_NUMBER
from .database import (
    init_db, ensure_user, get_gifts, get_gift,
    create_order, get_last_open_order, set_order_check
)
from .gifts_data import seed_gifts
from .keyboards import main_menu, gifts_keyboard, gift_actions_keyboard


bot = Bot(BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
router = Router()
dp.include_router(router)


class BuyGiftStates(StatesGroup):
    waiting_recipient = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    ensure_user(message.from_user.id, message.from_user.username)

    await message.answer(
        "Привет! 🎁 Добро пожаловать в renzo shops by @aqrxrx.",
        reply_markup=main_menu()
    )


@router.message(F.text == "🎁 Подарки")
async def show_gifts(message: Message):
    gifts = get_gifts()
    gifts = [dict(g) for g in gifts]
    await message.answer(
        "Выберите подарок:",
        reply_markup=gifts_keyboard(gifts)
    )


@router.callback_query(F.data == "gifts:list")
async def cb_gifts_list(callback: CallbackQuery):
    gifts = [dict(g) for g in get_gifts()]
    await callback.message.edit_text(
        "Выберите подарок:",
        reply_markup=gifts_keyboard(gifts)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("gift:"))
async def cb_gift_info(callback: CallbackQuery):
    gift_id = int(callback.data.split(":")[1])
    gift = get_gift(gift_id)
    if not gift:
        await callback.answer("Подарок не найден", show_alert=True)
        return

    text = (
        f"{gift['emoji']} <b>{gift['name']}</b>\n"
        f"Цена: <b>{gift['price']}₸</b>\n\n"
        f"Куда отправить подарок?"
    )
    await callback.message.edit_text(
        text,
        reply_markup=gift_actions_keyboard(gift_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:self:"))
async def cb_buy_self(callback: CallbackQuery):
    gift_id = int(callback.data.split(":")[2])
    gift = get_gift(gift_id)
    if not gift:
        await callback.answer("Подарок не найден", show_alert=True)
        return

    user_id = callback.from_user.id
    recipient_id = user_id
    order_id = create_order(user_id, recipient_id, gift_id, gift["price"])

    text = (
        f"Счёт №{order_id} создан.\n\n"
        f"Подарок: {gift['emoji']} {gift['name']}\n"
        f"Получатель: <b>Вы</b>\n"
        f"Сумма к оплате: <b>{gift['price']}₸</b>\n\n"
        f"Оплатите на Kaspi номер: <code>{KASPI_NUMBER}</code>\n"
        f"После оплаты отправьте сюда чек (фото или PDF)."
    )
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data.startswith("buy:friend:"))
async def cb_buy_friend(callback: CallbackQuery, state: FSMContext):
    gift_id = int(callback.data.split(":")[2])
    gift = get_gift(gift_id)
    if not gift:
        await callback.answer("Подарок не найден", show_alert=True)
        return

    await state.set_state(BuyGiftStates.waiting_recipient)
    await state.update_data(gift_id=gift_id)

    await callback.message.edit_text(
        f"{gift['emoji']} {gift['name']} за {gift['price']}₸\n\n"
        f"Отправить другу.\n"
        f"Пришлите @username или числовой ID получателя."
    )
    await callback.answer()


@router.message(BuyGiftStates.waiting_recipient)
async def process_recipient(message: Message, state: FSMContext):
    data = await state.get_data()
    gift_id = data["gift_id"]
    gift = get_gift(gift_id)

    text_id = message.text.strip()
    if text_id.startswith("@"):
        # отправка по username: userbot затем должен сам резолвить
        # здесь мы временно сохраняем как -1, а username логируем
        # но проще ожидать числовой ID
        await message.answer(
            "Пока лучше использовать числовой ID (forward от пользователя), "
            "иначе userbot'у будет сложнее. Для простоты сейчас используем ваш ID."
        )
        recipient_id = message.from_user.id
    else:
        try:
            recipient_id = int(text_id)
        except ValueError:
            await message.answer("Это не похоже на ID. Пришлите ID числом или @username.")
            return

    user_id = message.from_user.id
    order_id = create_order(user_id, recipient_id, gift_id, gift["price"])

    await state.clear()

    await message.answer(
        f"Счёт №{order_id} создан.\n\n"
        f"Подарок: {gift['emoji']} {gift['name']}\n"
        f"Получатель ID: <code>{recipient_id}</code>\n"
        f"Сумма к оплате: <b>{gift['price']}₸</b>\n\n"
        f"Оплатите на Kaspi номер: <code>{KASPI_NUMBER}</code>\n"
        f"После оплаты отправьте сюда чек (фото или PDF)."
    )


@router.message(F.photo | F.document)
async def handle_check(message: Message):
    # берём последний незакрытый заказ пользователя
    order = get_last_open_order(message.from_user.id)
    if not order:
        await message.answer("У вас нет активных счетов. Сначала оформите покупку подарка.")
        return

    if message.photo:
        file_id = message.photo[-1].file_id
    else:
        file_id = message.document.file_id

    # Тут по-хорошему должна быть проверка суммы/времени через OCR или Kaspi-API.
    # Сейчас просто принимаем чек и передаём заказ userbot'у.
    set_order_check(order["id"], file_id)

    await message.answer(
        f"Чек по счёту №{order['id']} принят ✅\n"
        "Подарок будет отправлен в ближайшие секунды."
    )


@router.message(F.text == "👤 Профиль")
async def profile(message: Message):
    from .database import get_conn
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT g.emoji, g.name, COUNT(*) as cnt
        FROM orders o
        JOIN gifts g ON g.id = o.gift_id
        WHERE o.user_id = ? AND o.status='sent'
        GROUP BY g.id
    """, (message.from_user.id,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await message.answer("У вас пока нет отправленных подарков.", reply_markup=main_menu())
        return

    lines = ["👤 Ваш профиль\n", "Отправленные подарки:"]
    for r in rows:
        lines.append(f"{r['emoji']} {r['name']} — {r['cnt']} шт.")
    await message.answer("\n".join(lines), reply_markup=main_menu())


async def main():
    init_db()
    seed_gifts()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
