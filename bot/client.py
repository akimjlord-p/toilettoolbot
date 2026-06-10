from typing import Any

import aiohttp

from config import settings


class APIClient:
    """
    Обёртка над HTTP запросами к ToiletTool API.
    Все методы возвращают dict/list или кидают RuntimeError при ошибке.
    """

    def __init__(self, telegram_id: int, username: str | None = None):
        self.base_url = settings.api_url.rstrip("/")
        self.headers = {
            "x-telegram-id": str(telegram_id),
            "x-bot-secret": settings.bot_secret,
        }
        if username:
            self.headers["x-username"] = username

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> Any:
        url = f"{self.base_url}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=self.headers, **kwargs) as resp:
                data = await resp.json()
                if resp.status >= 400:
                    detail = data.get("detail", "Неизвестная ошибка")
                    raise RuntimeError(detail)
                return data

    # ── Users ──────────────────────────────────────────────────────────────

    async def get_me(self) -> dict:
        return await self._request("GET", "/api/v1/users/me")

    async def assign_nickname(self, target_telegram_id: int, nickname: str) -> dict:
        return await self._request(
            "POST", "/api/v1/users/nickname",
            json={"target_telegram_id": target_telegram_id, "nickname": nickname},
        )

    async def set_moderator(self, target_telegram_id: int, is_moderator: bool) -> dict:
        return await self._request(
            "POST", "/api/v1/users/set-moderator",
            json={"target_telegram_id": target_telegram_id, "is_moderator": is_moderator},
        )

    # ── Toilets ────────────────────────────────────────────────────────────

    async def search_toilets(self, query: str) -> dict:
        return await self._request("GET", f"/api/v1/toilets/search?q={query}")

    async def create_toilet(
        self,
        address: str,
        name: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> dict:
        return await self._request(
            "POST", "/api/v1/toilets",
            json={"address": address, "name": name, "lat": lat, "lon": lon},
        )

    async def get_toilet(self, toilet_id: str) -> dict:
        return await self._request("GET", f"/api/v1/toilets/{toilet_id}")

    # ── Reviews ────────────────────────────────────────────────────────────

    async def create_review(
        self,
        toilet_id: str,
        score_cleanliness: int,
        score_supplies: int,
        score_smell: int,
        score_equipment: int,
        score_privacy: int,
        score_vibe: int,
        comment: str | None = None,
        photos: list[str] | None = None,
    ) -> dict:
        return await self._request(
            "POST", "/api/v1/reviews",
            json={
                "toilet_id": toilet_id,
                "score_cleanliness": score_cleanliness,
                "score_supplies": score_supplies,
                "score_smell": score_smell,
                "score_equipment": score_equipment,
                "score_privacy": score_privacy,
                "score_vibe": score_vibe,
                "comment": comment,
                "photos": photos or [],
            },
        )

    async def delete_review(self, review_id: str, reason: str) -> dict:
        return await self._request(
            "DELETE", f"/api/v1/reviews/{review_id}",
            json={"reason": reason},
        )

    async def get_toilet_reviews(self, toilet_id: str) -> list:
        return await self._request("GET", f"/api/v1/reviews/toilet/{toilet_id}")

    # ── Top ────────────────────────────────────────────────────────────────

    async def get_top(self, criterion: str = "total", limit: int = 10) -> list:
        return await self._request("GET", f"/api/v1/top?criterion={criterion}&limit={limit}")

    async def get_toilet_of_month(self, year: int | None = None, month: int | None = None) -> dict | None:
        params = ""
        if year and month:
            params = f"?year={year}&month={month}"
        return await self._request("GET", f"/api/v1/top/month{params}")

    async def get_month_history(self, limit: int = 12) -> list:
        return await self._request("GET", f"/api/v1/top/month/history?limit={limit}")

    async def assign_toilet_of_month(
        self,
        year: int | None = None,
        month: int | None = None,
        generate_ai_comment: bool = True,
    ) -> dict:
        params = f"?generate_ai_comment={str(generate_ai_comment).lower()}"
        if year and month:
            params += f"&year={year}&month={month}"
        return await self._request("POST", f"/api/v1/top/month/assign{params}")
