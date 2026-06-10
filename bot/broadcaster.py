from aiogram import Bot

from config import settings

MONTH_NAMES = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}


async def broadcast(bot: Bot, text: str) -> None:
    """Отправить произвольный текст в канал."""
    if not settings.channel_id:
        return
    await bot.send_message(settings.channel_id, text, parse_mode="HTML")


async def broadcast_toilet_of_month(bot: Bot, record: dict) -> None:
    """Опубликовать туалет месяца в канал."""
    toilet = record["toilet"]
    title = toilet.get("name") or toilet["address"]
    month_name = MONTH_NAMES.get(record["month"], str(record["month"]))
    ai_comment = record.get("ai_comment", "")

    text = (
        f"🏆 <b>Туалет месяца — {month_name} {record['year']}</b>\n\n"
        f"📍 <b>{title}</b>\n"
        f"📊 Средний балл: <b>{record['avg_score']} / 90</b>\n\n"
    )
    if ai_comment:
        text += f"💬 {ai_comment}\n"

    await broadcast(bot, text)


async def broadcast_top(bot: Bot, criterion: str, top: list[dict]) -> None:
    """Опубликовать топ туалетов в канал. Если у победителя есть фото — прикладываем."""
    criterion_names = {
        "total": "общему баллу",
        "cleanliness": "чистоте",
        "supplies": "расходникам",
        "smell": "запаху",
        "equipment": "оборудованию",
        "privacy": "приватности",
        "vibe": "вайбу",
    }
    label = criterion_names.get(criterion, criterion)

    lines = [f"📊 <b>Топ туалетов по {label}</b>\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, entry in enumerate(top[:10]):
        toilet = entry["toilet"]
        name = toilet.get("name") or toilet["address"]
        medal = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{medal} {name} — <b>{entry['avg_score']}</b> ({entry['review_count']} отзывов)")

    text = "\n".join(lines)

    # Фото победителя (первое место)
    winner_photos = top[0].get("photos", []) if top else []
    if winner_photos and settings.channel_id:
        from aiogram.types import InputMediaPhoto
        if len(winner_photos) == 1:
            await bot.send_photo(settings.channel_id, photo=winner_photos[0], caption=text, parse_mode="HTML")
        else:
            media = [InputMediaPhoto(media=winner_photos[0], caption=text, parse_mode="HTML")]
            media += [InputMediaPhoto(media=fid) for fid in winner_photos[1:]]
            await bot.send_media_group(settings.channel_id, media=media)
    else:
        await broadcast(bot, text)


async def broadcast_toilet_of_month_with_photos(bot: Bot, record: dict, photos: list[str]) -> None:
    """Туалет месяца с фото."""
    from aiogram.types import InputMediaPhoto
    toilet = record["toilet"]
    title = toilet.get("name") or toilet["address"]
    month_name = MONTH_NAMES.get(record["month"], str(record["month"]))
    ai_comment = record.get("ai_comment", "")

    text = (
        f"🏆 <b>Туалет месяца — {month_name} {record['year']}</b>\n\n"
        f"📍 <b>{title}</b>\n"
        f"📊 Средний балл: <b>{record['avg_score']} / 90</b>\n\n"
    )
    if ai_comment:
        text += f"💬 {ai_comment}\n"

    if not settings.channel_id:
        return

    if photos:
        if len(photos) == 1:
            await bot.send_photo(settings.channel_id, photo=photos[0], caption=text, parse_mode="HTML")
        else:
            media = [InputMediaPhoto(media=photos[0], caption=text, parse_mode="HTML")]
            media += [InputMediaPhoto(media=fid) for fid in photos[1:]]
            await bot.send_media_group(settings.channel_id, media=media)
    else:
        await broadcast(bot, text)
