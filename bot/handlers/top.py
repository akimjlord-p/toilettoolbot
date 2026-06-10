from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.client import APIClient
from bot.keyboards.inline import back_button, top_menu

router = Router()

MONTH_NAMES = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}

CRITERION_NAMES = {
    "total":       ("общему баллу",   "📊"),
    "cleanliness": ("чистоте",        "🧹"),
    "supplies":    ("расходникам",    "🧴"),
    "smell":       ("запаху",         "💨"),
    "equipment":   ("оборудованию",   "🔧"),
    "privacy":     ("приватности",    "🚪"),
    "vibe":        ("вайбу",          "✨"),
}


# ── Меню топов ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "top_menu")
async def show_top_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "📊 <b>Топы туалетов</b>\n\n"
        "Выбери критерий по которому хочешь посмотреть рейтинг:",
        reply_markup=top_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Показать топ по критерию ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("top:"))
async def show_top(callback: CallbackQuery) -> None:
    criterion = callback.data.split(":")[1]
    label, emoji = CRITERION_NAMES.get(criterion, ("общему баллу", "📊"))

    client = APIClient(callback.from_user.id, callback.from_user.username)
    try:
        top = await client.get_top(criterion=criterion, limit=10)
    except RuntimeError as e:
        await callback.answer(f"⚠️ {e}", show_alert=True)
        return

    if not top:
        await callback.message.edit_text(
            f"{emoji} <b>Топ по {label}</b>\n\n"
            f"Пока нет ни одного отзыва. Будь первым! 🚽",
            reply_markup=back_button("top_menu"),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = [f"{emoji} <b>Топ по {label}</b>\n"]

    for i, entry in enumerate(top):
        toilet = entry["toilet"]
        name = toilet.get("name") or toilet["address"]
        if len(name) > 35:
            name = name[:32] + "..."
        medal = medals[i] if i < 3 else f"  {i + 1}."
        score = entry["avg_score"]
        count = entry["review_count"]
        lines.append(f"{medal} {name}\n      <b>{score}/90</b> · {count} отз.")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_button("top_menu"),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Туалет месяца ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "toilet_of_month")
async def show_toilet_of_month(callback: CallbackQuery) -> None:
    client = APIClient(callback.from_user.id, callback.from_user.username)
    try:
        record = await client.get_toilet_of_month()
    except RuntimeError as e:
        await callback.answer(f"⚠️ {e}", show_alert=True)
        return

    if not record:
        await callback.message.edit_text(
            "🏆 <b>Туалет месяца</b>\n\n"
            "В этом месяце победитель ещё не определён.\n"
            "Возвращайся позже! 👀",
            reply_markup=back_button("main_menu"),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        _format_toilet_of_month(record),
        reply_markup=back_button("main_menu"),
        parse_mode="HTML",
    )
    await callback.answer()


# ── История туалетов месяца ───────────────────────────────────────────────────

@router.callback_query(F.data == "tom_history")
async def show_tom_history(callback: CallbackQuery) -> None:
    client = APIClient(callback.from_user.id, callback.from_user.username)
    try:
        history = await client.get_month_history(limit=6)
    except RuntimeError as e:
        await callback.answer(f"⚠️ {e}", show_alert=True)
        return

    if not history:
        await callback.message.edit_text(
            "📅 <b>История туалетов месяца</b>\n\n"
            "История пока пуста.",
            reply_markup=back_button("main_menu"),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    lines = ["📅 <b>Туалеты месяца — история</b>\n"]
    for record in history:
        toilet = record["toilet"]
        name = toilet.get("name") or toilet["address"]
        if len(name) > 30:
            name = name[:27] + "..."
        month_name = MONTH_NAMES.get(record["month"], str(record["month"]))
        lines.append(f"🏆 <b>{month_name} {record['year']}</b>\n   📍 {name} · {record['avg_score']}/90")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_button("main_menu"),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Вспомогательные функции ───────────────────────────────────────────────────

def _format_toilet_of_month(record: dict) -> str:
    toilet = record["toilet"]
    title = toilet.get("name") or toilet["address"]
    month_name = MONTH_NAMES.get(record["month"], str(record["month"]))
    ai_comment = record.get("ai_comment", "")

    text = (
        f"🏆 <b>Туалет месяца</b>\n"
        f"<i>{month_name} {record['year']}</i>\n\n"
        f"📍 <b>{title}</b>\n"
        f"📊 Средний балл: <b>{record['avg_score']} / 90</b>\n"
    )
    if ai_comment:
        text += f"\n💬 {ai_comment}"

    return text
