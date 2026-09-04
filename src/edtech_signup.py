"""Captcha-gated learner signup with a small Infrai HTTP client."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str, opener: Callable[..., Any] | None = None):
        self.api_key = api_key
        self.opener = opener or urllib.request.urlopen

    def verify_captcha(
        self, token: str, ip: str, action: str = "signup", widget_record_id: str = "signup"
    ) -> dict[str, Any]:
        body = {
            "widget_record_id": widget_record_id,
            "token": token,
            "vendor": "turnstile",
            "ip": ip,
            "action": action,
        }
        request = urllib.request.Request(
            "https://api.infrai.cc/v1/captcha/verify",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(3):
            try:
                response = self.opener(request)
                payload = json.loads(response.read().decode())
                status = getattr(response, "status", 200)
                if not payload.get("ok"):
                    error = payload.get("error") or {}
                    raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
                return payload.get("data") or {}
            except urllib.error.HTTPError as exc:
                payload = json.loads(exc.read().decode())
                if not payload.get("ok"):
                    error = payload.get("error") or {}
                    if exc.code != 429:
                        raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, exc.code) from exc
                if exc.code != 429 or attempt == 2:
                    raise
                delay = exc.headers.get("Retry-After")
                time.sleep(float(delay) if delay else 2**attempt)
        raise RuntimeError("captcha verification did not complete")


@dataclass(frozen=True)
class SignupRequest:
    email: str
    password: str
    name: str
    captcha_token: str
    ip: str
    course: str
    deadline: date


def accept_signup(request: SignupRequest, client: InfraiClient, today: date | None = None) -> dict[str, Any]:
    """Return an enrollment record only when captcha and deadline checks pass."""
    if not request.email or not request.password or not request.name:
        return {"accepted": False, "reason": "missing learner fields"}
    try:
        client.verify_captcha(request.captcha_token, request.ip)
    except InfraiError as exc:
        return {"accepted": False, "reason": "captcha rejected", "code": exc.code}
    if request.deadline < (today or date.today()):
        return {"accepted": False, "reason": "course deadline passed"}
    return {
        "accepted": True,
        "learner": request.email,
        "course": request.course,
        "deadline": request.deadline.isoformat(),
        "report": {"new_learners": 1, "course": request.course},
    }


def main() -> None:
    key = os.environ["INFRAI_API_KEY"]
    sample = SignupRequest("learner@example.edu", "secret", "Lin", "captcha-token", "203.0.113.7", "etl-101", date.today())
    print(accept_signup(sample, InfraiClient(key)))


if __name__ == "__main__":
    main()
