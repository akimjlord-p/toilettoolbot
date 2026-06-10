from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu(is_moderator: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚽 Оценить туалет", callback_data="review_start")
    builder.button(text="🏆 Топ туалетов", callback_data="top_menu")
    builder.button(text="📅 Туалет месяца", callback_data="toilet_of_month")
    if is_moderator:
        builder.button(text="⚙️ Модератор", callback_data="admin_menu")
    builder.adjust(1)
    return builder.as_markup()


def toilet_list(toilets: list[dict]) -> InlineKeyboardMarkup:
    """Список найденных туалетов для выбора."""
    builder = InlineKeyboardBuilder()
    for t in toilets:
        label = t.get("name") or t["address"]
        if len(label) > 40:
            label = label[:37] + "..."
        builder.button(text=f"📍 {label}", callback_data=f"toilet_select:{t['id']}")
    builder.button(text="➕ Добавить новый", callback_data="toilet_create_new")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def score_keyboard(max_score: int, step: int = 1) -> InlineKeyboardMarkup:
    """Кнопки для выставления оценки."""
    builder = InlineKeyboardBuilder()
    scores = list(range(0, max_score + 1, step))
    for score in scores:
        pct = score / max_score
        if pct >= 0.8:
            emoji = "🟢"
        elif pct >= 0.5:
            emoji = "🟡"
        else:
            emoji = "🔴"
        builder.button(text=f"{emoji} {score}", callback_data=f"score:{score}")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(4)
    return builder.as_markup()


def confirm_keyboard(yes_data: str, no_data: str = "cancel") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data=yes_data)
    builder.button(text="❌ Нет", callback_data=no_data)
    builder.adjust(2)
    return builder.as_markup()


def skip_keyboard(callback_data: str = "skip_comment") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Пропустить", callback_data=callback_data)
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()


def done_photos_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Готово", callback_data="photos_done")
    builder.button(text="⏭ Без фото", callback_data="photos_done")
    builder.adjust(2)
    return builder.as_markup()


def top_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏅 Общий топ", callback_data="top:total")
    builder.button(text="🧹 По чистоте", callback_data="top:cleanliness")
    builder.button(text="🧴 По расходникам", callback_data="top:supplies")
    builder.button(text="💨 По запаху", callback_data="top:smell")
    builder.button(text="🔧 По оборудованию", callback_data="top:equipment")
    builder.button(text="🚪 По приватности", callback_data="top:privacy")
    builder.button(text="✨ По вайбу", callback_data="top:vibe")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👑 Назначить прозвище", callback_data="admin_nickname")
    builder.button(text="🗑 Удалить отзыв", callback_data="admin_delete_review")
    builder.button(text="📢 Рассылка в канал", callback_data="admin_broadcast")
    builder.button(text="🏆 Назначить туалет месяца", callback_data="admin_assign_tom")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def back_button(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data=callback_data)
    return builder.as_markup()
