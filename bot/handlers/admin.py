from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.broadcaster import broadcast, broadcast_toilet_of_month, broadcast_top
from bot.client import APIClient
from bot.keyboards.inline import admin_menu, back_button, confirm_keyboard, main_menu, top_menu
from bot.states.admin import BroadcastStates, DeleteReviewStates, NicknameStates

router = Router()


# ── Меню модератора ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_menu")
async def show_admin_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        await callback.message.edit_text(
            "⚙️ <b>Панель модератора</b>\n\n"
            "Выбери действие:",
            reply_markup=admin_menu(),
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer()


# ══════════════════════════════════════════════════════════════════════════════
# ПРОЗВИЩА
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_nickname")
async def nickname_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(NicknameStates.waiting_target_id)
    await callback.message.edit_text(
        "👑 <b>Назначить прозвище</b>\n\n"
        "Введи Telegram ID пользователя которому хочешь дать прозвище.\n\n"
        "<i>Узнать ID можно у @userinfobot</i>",
        reply_markup=back_button("admin_menu"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(NicknameStates.waiting_target_id)
async def nickname_got_target(message: Message, state: FSMContext) -> None:
    if not message.text.strip().lstrip("-").isdigit():
        await message.answer(
            "⚠️ Telegram ID должен быть числом.\n"
            "Попробуй ещё раз:"
        )
        return

    await state.update_data(target_id=int(message.text.strip()))
    await state.set_state(NicknameStates.waiting_nickname)
    await message.answer(
        "✏️ Теперь введи прозвище для этого пользователя:\n\n"
        "<i>Прозвища уникальны — два юзера не могут иметь одинаковое</i>",
        reply_markup=back_button("admin_menu"),
        parse_mode="HTML",
    )


@router.message(NicknameStates.waiting_nickname)
async def nickname_got_name(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    nickname = message.text.strip()
    target_id = data["target_id"]

    client = APIClient(message.from_user.id, message.from_user.username)
    try:
        updated = await client.assign_nickname(target_id, nickname)
    except RuntimeError as e:
        await message.answer(f"⚠️ Ошибка: {e}", reply_markup=back_button("admin_menu"))
        await state.clear()
        return

    await state.clear()

    # Выдаём титул в канале если канал настроен
    channel_status = await _set_channel_title(bot, target_id, nickname)

    status_text = ""
    if channel_status == "ok":
        status_text = "\n📢 Титул в канале выдан"
    elif channel_status == "not_member":
        status_text = "\n⚠️ Пользователь не состоит в канале — титул не выдан"
    elif channel_status == "no_channel":
        pass  # канал не настроен — молчим
    elif channel_status == "error":
        status_text = "\n⚠️ Не удалось выдать титул в канале (нет прав?)"

    await message.answer(
        f"✅ Готово!\n\n"
        f"Пользователь <b>{target_id}</b> теперь известен как «<b>{updated['nickname']}</b>» 👑"
        f"{status_text}",
        reply_markup=admin_menu(),
        parse_mode="HTML",
    )


async def _set_channel_title(bot: Bot, user_id: int, title: str) -> str:
    """
    Выдаёт кастомный титул администратора в канале и в чате обсуждений.
    Возвращает статус: ok / not_member / no_channel / error
    """
    from config import settings
    from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

    if not settings.chat_id:
        return "no_channel"

    short_title = title[:16]  # Telegram ограничивает 16 символами
    results = []

    for chat_id in [settings.chat_id]:
        try:
            await bot.promote_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                can_manage_chat=False,
                can_post_messages=False,
                can_edit_messages=False,
                can_delete_messages=False,
                can_restrict_members=False,
                can_promote_members=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
                is_anonymous=False,
            )
            await bot.set_chat_administrator_custom_title(
                chat_id=chat_id,
                user_id=user_id,
                custom_title=short_title,
            )
            results.append("ok")
        except TelegramBadRequest as e:
            err = str(e).lower()
            if "user not found" in err or "not a member" in err or "user is not a member" in err:
                results.append("not_member")
            else:
                results.append("error")
        except TelegramForbiddenError:
            results.append("error")
        except Exception:
            results.append("error")

    if all(r == "ok" for r in results):
        return "ok"
    if all(r == "not_member" for r in results):
        return "not_member"
    if "ok" in results:
        return "ok"  # хотя бы в одном месте выдали
    return "error"


# ══════════════════════════════════════════════════════════════════════════════
# УДАЛЕНИЕ ОТЗЫВА
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_delete_review")
async def delete_review_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(DeleteReviewStates.waiting_review_id)
    await callback.message.edit_text(
        "🗑 <b>Удалить отзыв</b>\n\n"
        "Введи ID отзыва который нужно удалить.\n\n"
        "<i>ID отзыва можно найти в деталях туалета через API или Swagger</i>",
        reply_markup=back_button("admin_menu"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(DeleteReviewStates.waiting_review_id)
async def delete_review_got_id(message: Message, state: FSMContext) -> None:
    review_id = message.text.strip()
    await state.update_data(review_id=review_id)
    await state.set_state(DeleteReviewStates.waiting_reason)
    await message.answer(
        f"📝 Укажи причину удаления отзыва <code>{review_id[:8]}...</code>:",
        reply_markup=back_button("admin_menu"),
        parse_mode="HTML",
    )


@router.message(DeleteReviewStates.waiting_reason)
async def delete_review_got_reason(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    review_id = data["review_id"]
    reason = message.text.strip()

    client = APIClient(message.from_user.id, message.from_user.username)
    try:
        await client.delete_review(review_id, reason)
    except RuntimeError as e:
        await message.answer(f"⚠️ Ошибка: {e}", reply_markup=back_button("admin_menu"))
        await state.clear()
        return

    await state.clear()
    await message.answer(
        f"✅ Отзыв скрыт.\n\n"
        f"📝 Причина: «{reason}»\n"
        f"<i>Данные сохранены в базе</i>",
        reply_markup=admin_menu(),
        parse_mode="HTML",
    )


# ══════════════════════════════════════════════════════════════════════════════
# ТУАЛЕТ МЕСЯЦА
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_assign_tom")
async def assign_tom_confirm(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🏆 <b>Назначить туалет месяца</b>\n\n"
        "Система автоматически выберет туалет с наивысшим средним баллом за текущий месяц "
        "и сгенерирует шуточный комментарий через AI.\n\n"
        "Результат будет опубликован в канале. Продолжить?",
        reply_markup=confirm_keyboard(yes_data="admin_assign_tom_confirm", no_data="admin_menu"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_assign_tom_confirm")
async def assign_tom_execute(callback: CallbackQuery, bot: Bot) -> None:
    await callback.message.edit_text("⏳ Определяю победителя и генерирую комментарий...")

    client = APIClient(callback.from_user.id, callback.from_user.username)
    try:
        record = await client.assign_toilet_of_month(generate_ai_comment=True)
    except RuntimeError as e:
        await callback.message.edit_text(
            f"⚠️ Не удалось назначить туалет месяца: {e}",
            reply_markup=back_button("admin_menu"),
        )
        await callback.answer()
        return

    toilet = record["toilet"]
    title = toilet.get("name") or toilet["address"]

    # Публикуем в канал
    await broadcast_toilet_of_month(bot, record)

    await callback.message.edit_text(
        f"✅ <b>Туалет месяца назначен!</b>\n\n"
        f"🏆 <b>{title}</b>\n"
        f"📊 Средний балл: {record['avg_score']} / 90\n\n"
        f"Пост опубликован в канале 📢",
        reply_markup=admin_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


# ══════════════════════════════════════════════════════════════════════════════
# РАССЫЛКА В КАНАЛ
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_menu(callback: CallbackQuery, state: FSMContext) -> None:
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Написать текст", callback_data="broadcast_custom")
    builder.button(text="📊 Опубликовать топ", callback_data="broadcast_top_menu")
    builder.button(text="◀️ Назад", callback_data="admin_menu")
    builder.adjust(1)

    await callback.message.edit_text(
        "📢 <b>Рассылка в канал</b>\n\n"
        "Что публикуем?",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "broadcast_custom")
async def broadcast_custom_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BroadcastStates.waiting_message)
    await callback.message.edit_text(
        "✏️ <b>Рассылка</b>\n\n"
        "Напиши текст для публикации в канале.\n"
        "Поддерживается HTML-разметка: <b>жирный</b>, <i>курсив</i>",
        reply_markup=back_button("admin_broadcast"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_message)
async def broadcast_custom_send(message: Message, state: FSMContext, bot: Bot) -> None:
    await broadcast(bot, message.text)
    await state.clear()
    await message.answer(
        "✅ Сообщение опубликовано в канале 📢",
        reply_markup=admin_menu(),
    )


@router.callback_query(F.data == "broadcast_top_menu")
async def broadcast_top_select(callback: CallbackQuery) -> None:
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for key, (label, emoji) in {
        "total": ("общему баллу", "📊"),
        "cleanliness": ("чистоте", "🧹"),
        "supplies": ("расходникам", "🧴"),
        "smell": ("запаху", "💨"),
        "equipment": ("оборудованию", "🔧"),
        "privacy": ("приватности", "🚪"),
        "vibe": ("вайбу", "✨"),
    }.items():
        builder.button(text=f"{emoji} По {label}", callback_data=f"broadcast_top:{key}")
    builder.button(text="◀️ Назад", callback_data="admin_broadcast")
    builder.adjust(1)

    await callback.message.edit_text(
        "📊 Выбери критерий для публикации топа:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("broadcast_top:"))
async def broadcast_top_send(callback: CallbackQuery, bot: Bot) -> None:
    criterion = callback.data.split(":")[1]
    await callback.message.edit_text("⏳ Получаю данные и публикую...")

    client = APIClient(callback.from_user.id, callback.from_user.username)
    try:
        top = await client.get_top(criterion=criterion, limit=10)
    except RuntimeError as e:
        await callback.message.edit_text(
            f"⚠️ Ошибка: {e}", reply_markup=back_button("admin_broadcast")
        )
        await callback.answer()
        return

    await broadcast_top(bot, criterion, top)
    await callback.message.edit_text(
        "✅ Топ опубликован в канале 📢",
        reply_markup=admin_menu(),
    )
    await callback.answer()
