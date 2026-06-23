import html

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.client import APIClient
from bot.keyboards.inline import main_menu

router = Router()
fallback_router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()

    client = APIClient(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )

    try:
        user = await client.get_me()
    except RuntimeError:
        await message.answer("⚠️ Не удалось подключиться к серверу. Попробуй позже.")
        return

    name = message.from_user.first_name or "друг"
    is_moderator = user.get("is_moderator", False)
    nickname = user.get("nickname")

    if nickname:
        display = f"<b>{html.escape(nickname)}</b>"
    else:
        display = f"<b>{html.escape(name)}</b>"

    text = (
        f"🚽 Привет, {display}!\n\n"
        f"Добро пожаловать в <b>ToiletTool</b> — сервис честных оценок общественных туалетов.\n\n"
        f"Здесь ты можешь:\n"
        f"• Оценить туалет по 6 критериям\n"
        f"• Посмотреть топы лучших мест\n"
        f"• Узнать туалет месяца 🏆\n\n"
        f"Выбирай:"
    )

    await message.answer(text, reply_markup=main_menu(is_moderator), parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.message:
        await callback.answer("Сообщение устарело. Отправь /start", show_alert=True)
        return

    await state.clear()

    client = APIClient(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
    )

    try:
        user = await client.get_me()
    except RuntimeError:
        await callback.answer("⚠️ Ошибка подключения", show_alert=True)
        return

    is_moderator = user.get("is_moderator", False)
    nickname = user.get("nickname")
    name = callback.from_user.first_name or "друг"
    display = f"<b>{html.escape(nickname)}</b>" if nickname else f"<b>{html.escape(name)}</b>"

    text = (
        f"🏠 Главное меню, {display}\n\n"
        f"Выбирай:"
    )

    try:
        await callback.message.edit_text(text, reply_markup=main_menu(is_moderator), parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.message:
        await callback.answer("Сообщение устарело. Отправь /start", show_alert=True)
        return

    await state.clear()

    client = APIClient(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
    )

    try:
        user = await client.get_me()
        is_moderator = user.get("is_moderator", False)
    except RuntimeError:
        is_moderator = False

    try:
        await callback.message.edit_text(
            "❌ Действие отменено.\n\nВыбирай:",
            reply_markup=main_menu(is_moderator),
        )
    except Exception:
        pass
    await callback.answer()


@fallback_router.callback_query()
async def stale_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Ловит все необработанные callback'и (устаревшие кнопки после рестарта)."""
    await state.clear()
    await callback.answer("Бот был перезапущен. Отправь /start чтобы продолжить", show_alert=True)
