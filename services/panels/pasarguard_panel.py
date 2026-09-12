"""
آداپتور پنل PasarGuard.

PasarGuard یه فورک از Marzban هست، برای همین ساختار API‌ش خیلی نزدیک به
Marzban ـه (توکن گرفتن از /api/admin/token و بعد CRUD کاربر از /api/user).
با این‌حال چون فورک‌ها می‌تونن جاهایی فرق کنن، *قبل از استفاده‌ی واقعی*
حتما این آدرس‌ها رو با مستندات خودِ پنلت چک کن:

    https://<آدرس-پنل-تو>/docs   (یا /redoc)

هر جایی که فرق داشت، فقط همین فایل رو اصلاح کن — بقیه‌ی ربات دست نمی‌خوره،
چون همه از طریق BasePanel باهاش کار می‌کنن.
"""
from __future__ import annotations

import time

import httpx

from services.panels.base_panel import BasePanel, PanelUser


class PasarGuardPanel(BasePanel):
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._token: str | None = None
        self._token_obtained_at: float = 0
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=20)

    # ------------------------------------------------------------ احراز هویت
    async def _get_token(self) -> str:
        # توکن‌ها معمولا محدود به زمان‌ان؛ هر ۵۰ دقیقه یه‌بار تازه‌اش می‌کنیم
        if self._token and (time.time() - self._token_obtained_at) < 50 * 60:
            return self._token

        resp = await self._client.post(
            "/api/admin/token",
            data={"username": self.username, "password": self.password},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_obtained_at = time.time()
        return self._token

    async def _auth_headers(self) -> dict:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}"}

    # ------------------------------------------------------------ عملیات کاربر
    async def create_user(
        self,
        username: str,
        duration_days: int,
        data_limit_gb: int | None = None,
    ) -> PanelUser:
        headers = await self._auth_headers()
        expire_ts = int(time.time()) + duration_days * 86400

        payload = {
            "username": username,
            "expire": expire_ts,
            # 0 یعنی نامحدود؛ برای اشتراک حجمی مقدار واقعی رو می‌فرستیم
            "data_limit": (data_limit_gb * 1024 ** 3) if data_limit_gb else 0,
            "proxies": {
                "vless": {},
                "vmess": {},
            },
            # TODO: اینبوندهای واقعی پنلت رو اینجا بذار — از /api/inbounds بگیر
            "inbounds": {},
        }

        resp = await self._client.post("/api/user", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return self._to_panel_user(data)

    async def get_user(self, username: str) -> PanelUser | None:
        headers = await self._auth_headers()
        resp = await self._client.get(f"/api/user/{username}", headers=headers)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return self._to_panel_user(resp.json())

    async def extend_user(self, username: str, extra_days: int) -> PanelUser:
        current = await self.get_user(username)
        headers = await self._auth_headers()
        base_ts = current.expire_timestamp or int(time.time())
        new_expire = base_ts + extra_days * 86400

        resp = await self._client.put(
            f"/api/user/{username}",
            json={"expire": new_expire},
            headers=headers,
        )
        resp.raise_for_status()
        return self._to_panel_user(resp.json())

    async def disable_user(self, username: str) -> None:
        headers = await self._auth_headers()
        resp = await self._client.put(
            f"/api/user/{username}",
            json={"status": "disabled"},
            headers=headers,
        )
        resp.raise_for_status()

    # ------------------------------------------------------------ کمکی
    @staticmethod
    def _to_panel_user(data: dict) -> PanelUser:
        return PanelUser(
            username=data["username"],
            subscription_url=data.get("subscription_url", ""),
            expire_timestamp=data.get("expire"),
            data_limit_bytes=data.get("data_limit"),
        )

    async def close(self):
        await self._client.aclose()
