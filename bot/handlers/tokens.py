from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.client import APIClient
from bot.keyboards.inline import tokens_menu

router = Router()

RANKS = [
    (18000, "👑 CEO нужника"),
    (9000,  "🏆 Президент фаянса"),
    (4500,  "🤝 Вице-президент ВК"),
    (2000,  "🎯 Босс смывания"),
    (900,   "🏢 Директор слива"),
    (400,   "💼 Менеджер кабинки"),
    (150,   "📋 Стажёр унитаза"),
    (0,     "🧹 Уборщик сортира"),
]

MECHANICS_TEXT = (
    "💰 <b>Как работают токены</b>\n\n"
    "<b>Начисление:</b>\n"
    "• Написал отзыв — <b>+100</b>\n"
    "• Добавил фото (за каждое) — <b>+30</b>\n"
    "• Написал комментарий — <b>+20</b>\n"
    "• Первый отзыв на новый туалет — <b>+50</b>\n"
    "• Ежедневный вход — <b>+10</b>\n"
    "• Туалет месяца (твой отзыв) — <b>+500</b>\n"
    "• Туалет в топ-10 (твой отзыв) — <b>+200</b>\n\n"
    "<b>Штрафы:</b>\n"
    "• Отзыв удалён модератором — <b>−100</b>\n\n"
    "<b>При листинге:</b>\n"
    "• Все токены конвертируются <b>1:1</b>\n"
    "• Топ-50 по балансу получают <b>×2</b>\n"
    "• Чем раньше начал — тем больше накопил\n\n"
    "🚀 Листинг объявим когда наберём аудиторию."
)


def _get_rank(balance: int) -> str:
    for threshold, title in RANKS:
        if balance >= threshold:
            return title
    return RANKS[-1][1]


def _next_rank(balance: int) -> tuple[str, int] | None:
    for i, (threshold, title) in enumerate(RANKS):
        if balance < threshold:
            return title, threshold - balance
    return None


@router.callback_query(F.data == "tokens_balance")
async def show_balance(callback: CallbackQuery):
    client = APIClient(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
    )
    try:
        user = await client.get_me()
    except RuntimeError:
        await callback.answer("⚠️ Ошибка подключения", show_alert=True)
        return

    balance = user.get("balance", 0)
    rank = _get_rank(balance)
    next_info = _next_rank(balance)
    nickname = user.get("nickname") or callback.from_user.first_name or "Аноним"

    text = (
        f"💰 <b>Мои токены</b>\n\n"
        f"👤 {nickname}\n"
        f"🏅 Звание: {rank}\n"
        f"💰 Баланс: <b>{balance}</b> токенов\n"
    )
    if next_info:
        next_rank_name, diff = next_info
        text += f"\nДо звания <b>{next_rank_name}</b>: ещё {diff} токенов"
    else:
        text += "\n🏆 Ты достиг высшего звания!"

    try:
        await callback.message.edit_text(text, reply_markup=tokens_menu("balance"), parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "tokens_top")
async def show_top(callback: CallbackQuery):
    client = APIClient(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
    )
    try:
        top = await client.get_token_top(limit=10)
    except RuntimeError:
        await callback.answer("⚠️ Ошибка подключения", show_alert=True)
        return

    if not top:
        text = "🏆 <b>Топ по токенам</b>\n\nПока никто не набрал токенов. Будь первым!"
    else:
        lines = ["🏆 <b>Топ по токенам</b>\n"]
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        for entry in top:
            rank = entry["rank"]
            medal = medals.get(rank, f"{rank}.")
            name = entry.get("nickname") or entry.get("username") or "Аноним"
            balance = entry["balance"]
            title = _get_rank(balance)
            lines.append(f"{medal} <b>{name}</b> — {balance} токенов\n   {title}")
        text = "\n".join(lines)

    try:
        await callback.message.edit_text(text, reply_markup=tokens_menu("top"), parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "tokens_info")
async def show_info(callback: CallbackQuery):
    try:
        await callback.message.edit_text(MECHANICS_TEXT, reply_markup=tokens_menu("info"), parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()
