import html

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.client import APIClient
from bot.keyboards.inline import (
    back_button,
    confirm_keyboard,
    done_photos_keyboard,
    main_menu,
    score_keyboard,
    skip_keyboard,
    toilet_list,
)
from bot.states.review import ReviewStates

router = Router()

# ── Шаг 1: запуск флоу ────────────────────────────────────────────────────────

@router.callback_query(F.data == "review_start")
async def review_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.message:
        await callback.answer()
        return
    await state.set_state(ReviewStates.waiting_address)
    try:
        await callback.message.edit_text(
            "📍 <b>Шаг 1 из 3 — Найди туалет</b>\n\n"
            "Введи адрес туалета который хочешь оценить.\n"
            "Можно написать частично — например: <i>ул. Ленина</i> или <i>ТЦ Мега</i>",
            reply_markup=back_button("main_menu"),
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer()


# ── Шаг 2: поиск по адресу ────────────────────────────────────────────────────

@router.message(ReviewStates.waiting_address)
async def process_address(message: Message, state: FSMContext) -> None:
    query = message.text.strip()

    client = APIClient(message.from_user.id, message.from_user.username)
    try:
        result = await client.search_toilets(query)
    except RuntimeError as e:
        await message.answer(f"⚠️ Ошибка поиска: {e}")
        return

    found = result.get("found", [])
    needs_creation = result.get("needs_creation", True)

    normalized = result.get("normalized_address") or query
    lat = result.get("lat")
    lon = result.get("lon")

    if not needs_creation and found:
        await state.set_state(ReviewStates.waiting_toilet_confirm)
        await state.update_data(address=normalized, lat=lat, lon=lon, found_toilets=found)

        geo_hint = f"\n<i>📍 Геокодер: {html.escape(normalized)}</i>" if normalized != query else ""
        await message.answer(
            f"🔍 Нашёл <b>{len(found)}</b> совпадений.{geo_hint}\n\n"
            f"Выбери нужный туалет или добавь новый:",
            reply_markup=toilet_list(found),
            parse_mode="HTML",
        )
    else:
        await state.update_data(address=normalized, lat=lat, lon=lon)

        geo_hint = f"<i>📍 Геокодер определил: {html.escape(normalized)}</i>\n\n" if normalized != query else ""
        await message.answer(
            f"🆕 Туалетов рядом с этим адресом ещё нет в базе.\n\n"
            f"{geo_hint}"
            f"Добавить его?",
            reply_markup=confirm_keyboard(yes_data="toilet_create_new", no_data="cancel"),
            parse_mode="HTML",
        )


# ── Шаг 3: выбор туалета из списка ───────────────────────────────────────────

@router.callback_query(F.data.startswith("toilet_select:"), ReviewStates.waiting_toilet_confirm)
async def toilet_selected(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.message:
        await callback.answer()
        return

    toilet_id = callback.data.split(":")[1]
    client = APIClient(callback.from_user.id, callback.from_user.username)

    try:
        card = await client.get_toilet(toilet_id)
    except RuntimeError as e:
        await callback.answer(f"⚠️ {e}", show_alert=True)
        return

    toilet = card["toilet"]
    avg = card.get("avg_scores")
    title = toilet.get("name") or toilet["address"]

    if avg:
        score_text = (
            f"📊 Средний балл: <b>{avg['total']} / 90</b>\n"
            f"Отзывов: {avg['review_count']}"
        )
    else:
        score_text = "📊 Отзывов пока нет — будь первым!"

    await state.update_data(toilet_id=toilet_id, toilet_title=title)
    try:
        await callback.message.edit_text(
            f"🚽 <b>{html.escape(title)}</b>\n\n"
            f"{score_text}\n\n"
            f"Оценить этот туалет?",
            reply_markup=confirm_keyboard(yes_data="review_begin", no_data="main_menu"),
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer()


# ── Шаг 3а: создать новый туалет ─────────────────────────────────────────────

@router.callback_query(F.data == "toilet_create_new")
async def toilet_create_new(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.message:
        await callback.answer()
        return

    data = await state.get_data()
    address = data.get("address", "")

    client = APIClient(callback.from_user.id, callback.from_user.username)
    try:
        toilet = await client.create_toilet(
            address=address,
            lat=data.get("lat"),
            lon=data.get("lon"),
        )
    except RuntimeError as e:
        await callback.answer(f"⚠️ {e}", show_alert=True)
        return

    title = toilet.get("name") or toilet["address"]
    await state.update_data(toilet_id=toilet["id"], toilet_title=title)

    try:
        await callback.message.edit_text(
            f"✅ Туалет <b>«{html.escape(title)}»</b> добавлен в базу!\n\n"
            f"Теперь оцени его — начнём анкету?",
            reply_markup=confirm_keyboard(yes_data="review_begin", no_data="main_menu"),
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer()


# ── Шаг 4: начало анкеты ─────────────────────────────────────────────────────

@router.callback_query(F.data == "review_begin")
async def review_begin(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.message:
        await callback.answer()
        return
    await state.set_state(ReviewStates.score_cleanliness)
    try:
        await callback.message.edit_text(
            "📋 <b>Шаг 2 из 3 — Анкета</b>\n\n"
            "🧹 <b>Чистота</b> — пол, стены, раковины, зеркала, унитазы\n\n"
            "Оцени от 0 до 25:",
            reply_markup=score_keyboard(max_score=25, step=5),
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer()


# ── Критерий 1: чистота ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("score:"), ReviewStates.score_cleanliness)
async def score_cleanliness(callback: CallbackQuery, state: FSMContext) -> None:
    score = int(callback.data.split(":")[1])
    await state.update_data(score_cleanliness=score)
    await state.set_state(ReviewStates.score_supplies)
    try:
        await callback.message.edit_text(
            f"✅ Чистота: <b>{score}/25</b>\n\n"
            f"🧴 <b>Расходники</b> — туалетная бумага, мыло, сушилка или бумажные полотенца\n\n"
            f"Оцени от 0 до 20:",
            reply_markup=score_keyboard(max_score=20, step=4),
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer()


# ── Критерий 2: расходники ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("score:"), ReviewStates.score_supplies)
async def score_supplies(callback: CallbackQuery, state: FSMContext) -> None:
    score = int(callback.data.split(":")[1])
    await state.update_data(score_supplies=score)
    await state.set_state(ReviewStates.score_smell)
    try:
        await callback.message.edit_text(
            f"✅ Расходники: <b>{score}/20</b>\n\n"
            f"💨 <b>Запах</b> — отсутствие неприятного запаха, вентиляция\n\n"
            f"Оцени от 0 до 20:",
            reply_markup=score_keyboard(max_score=20, step=4),
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer()


# ── Критерий 3: запах ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("score:"), ReviewStates.score_smell)
async def score_smell(callback: CallbackQuery, state: FSMContext) -> None:
    score = int(callback.data.split(":")[1])
    await state.update_data(score_smell=score)
    await state.set_state(ReviewStates.score_equipment)
    try:
        await callback.message.edit_text(
            f"✅ Запах: <b>{score}/20</b>\n\n"
            f"🔧 <b>Оборудование</b> — работающий слив, краны, замки на кабинках, освещение\n\n"
            f"Оцени от 0 до 15:",
            reply_markup=score_keyboard(max_score=15, step=3),
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer()


# ── Критерий 4: оборудование ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("score:"), ReviewStates.score_equipment)
async def score_equipment(callback: CallbackQuery, state: FSMContext) -> None:
    score = int(callback.data.split(":")[1])
    await state.update_data(score_equipment=score)
    await state.set_state(ReviewStates.score_privacy)
    try:
        await callback.message.edit_text(
            f"✅ Оборудование: <b>{score}/15</b>\n\n"
            f"🚪 <b>Приватность</b> — целые двери, нормальные замки, перегородки\n\n"
            f"Оцени от 0 до 5:",
            reply_markup=score_keyboard(max_score=5, step=1),
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer()


# ── Критерий 5: приватность ───────────────────────────────────────────────────

@router.callback_query(F.data.startswith("score:"), ReviewStates.score_privacy)
async def score_privacy(callback: CallbackQuery, state: FSMContext) -> None:
    score = int(callback.data.split(":")[1])
    await state.update_data(score_privacy=score)
    await state.set_state(ReviewStates.score_vibe)
    try:
        await callback.message.edit_text(
            f"✅ Приватность: <b>{score}/5</b>\n\n"
            f"✨ <b>Общий вайб</b> — твоё субъективное впечатление. Хочется ли вернуться?\n\n"
            f"Оцени от 0 до 5:",
            reply_markup=score_keyboard(max_score=5, step=1),
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer()


# ── Критерий 6: вайб ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("score:"), ReviewStates.score_vibe)
async def score_vibe(callback: CallbackQuery, state: FSMContext) -> None:
    score = int(callback.data.split(":")[1])
    await state.update_data(score_vibe=score)
    await state.set_state(ReviewStates.comment)
    try:
        await callback.message.edit_text(
            f"✅ Вайб: <b>{score}/5</b>\n\n"
            f"💬 <b>Шаг 3 из 4 — Комментарий</b>\n\n"
            f"Напиши что-нибудь об этом туалете или пропусти:",
            reply_markup=skip_keyboard(),
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer()


# ── Шаг 5а: комментарий введён ───────────────────────────────────────────────

@router.message(ReviewStates.comment)
async def process_comment(message: Message, state: FSMContext) -> None:
    await state.update_data(comment=message.text.strip())
    await _ask_photos(message, state)


# ── Шаг 5б: комментарий пропущен ─────────────────────────────────────────────

@router.callback_query(F.data == "skip_comment", ReviewStates.comment)
async def skip_comment(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(comment=None)
    await _ask_photos(callback.message, state)
    await callback.answer()


# ── Шаг 6: запрос фото ───────────────────────────────────────────────────────

async def _ask_photos(message: Message, state: FSMContext) -> None:
    await state.set_state(ReviewStates.photos)
    await state.update_data(photos=[])
    await message.answer(
        "📸 <b>Шаг 4 из 4 — Фото</b> (необязательно)\n\n"
        "Прикрепи до 3 фотографий этого туалета.\n"
        "Отправляй по одному — когда закончишь, нажми <b>Готово</b>:",
        reply_markup=done_photos_keyboard(),
        parse_mode="HTML",
    )


@router.message(ReviewStates.photos, F.photo)
async def process_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    photos: list = data.get("photos", [])

    if len(photos) >= 3:
        await message.answer("⚠️ Максимум 3 фото. Нажми <b>Готово</b>.", parse_mode="HTML")
        return

    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(photos=photos)

    remaining = 3 - len(photos)
    if remaining > 0:
        await message.answer(
            f"✅ Фото {len(photos)}/3 добавлено. Можно ещё {remaining} или нажми <b>Готово</b>:",
            reply_markup=done_photos_keyboard(),
            parse_mode="HTML",
        )
    else:
        await message.answer("✅ 3/3 фото добавлено. Нажми <b>Готово</b>:", reply_markup=done_photos_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "photos_done", ReviewStates.photos)
async def photos_done(callback: CallbackQuery, state: FSMContext) -> None:
    await _submit_review(callback.message, state, user_id=callback.from_user.id, username=callback.from_user.username)
    await callback.answer()


# ── Отправка отзыва на бэк ───────────────────────────────────────────────────

async def _submit_review(
    message: Message,
    state: FSMContext,
    user_id: int | None = None,
    username: str | None = None,
) -> None:
    data = await state.get_data()
    uid = user_id or message.from_user.id
    uname = username or (message.from_user.username if message.from_user else None)

    client = APIClient(uid, uname)
    try:
        review = await client.create_review(
            toilet_id=data["toilet_id"],
            score_cleanliness=data["score_cleanliness"],
            score_supplies=data["score_supplies"],
            score_smell=data["score_smell"],
            score_equipment=data["score_equipment"],
            score_privacy=data["score_privacy"],
            score_vibe=data["score_vibe"],
            comment=data.get("comment"),
            photos=data.get("photos", []),
        )
    except RuntimeError as e:
        await message.answer(f"⚠️ Не удалось сохранить отзыв: {e}")
        await state.clear()
        return

    title = data.get("toilet_title", "туалет")
    total = review["total_score"]

    if total >= 75:
        grade = "🏆 Отличный туалет!"
    elif total >= 50:
        grade = "👍 Неплохое место"
    elif total >= 25:
        grade = "😐 Так себе"
    else:
        grade = "💀 Лучше потерпеть"

    scores = (
        f"🧹 Чистота: {data['score_cleanliness']}/25\n"
        f"🧴 Расходники: {data['score_supplies']}/20\n"
        f"💨 Запах: {data['score_smell']}/20\n"
        f"🔧 Оборудование: {data['score_equipment']}/15\n"
        f"🚪 Приватность: {data['score_privacy']}/5\n"
        f"✨ Вайб: {data['score_vibe']}/5"
    )

    text = (
        f"✅ <b>Отзыв сохранён!</b>\n\n"
        f"📍 {html.escape(title)}\n"
        f"━━━━━━━━━━━━━━\n"
        f"{scores}\n"
        f"━━━━━━━━━━━━━━\n"
        f"📊 Итого: <b>{total} / 90</b>\n"
        f"{grade}"
    )
    if data.get("comment"):
        text += f"\n\n💬 «{html.escape(data['comment'])}»"

    try:
        user = await client.get_me()
        is_moderator = user.get("is_moderator", False)
    except RuntimeError:
        is_moderator = False

    await state.clear()
    await message.answer(text, reply_markup=main_menu(is_moderator), parse_mode="HTML")
