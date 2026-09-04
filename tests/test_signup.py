from datetime import date

from src.edtech_signup import InfraiClient, InfraiError, SignupRequest, accept_signup


class GoodClient:
    def verify_captcha(self, token: str, ip: str):
        return {"score": 0.99}


class RejectingClient:
    def verify_captcha(self, token: str, ip: str):
        raise InfraiError("CAPTCHA_SCORE_TOO_LOW", {}, 422)


def request(deadline=date(2030, 1, 1)):
    return SignupRequest("a@b.edu", "pw", "A", "token", "127.0.0.1", "etl-101", deadline)


def test_signup_accepts_verified_learner_and_reports_course():
    result = accept_signup(request(), GoodClient(), today=date(2029, 1, 1))
    assert result["accepted"] is True
    assert result["report"] == {"new_learners": 1, "course": "etl-101"}


def test_signup_rejects_captcha_without_server_error():
    result = accept_signup(request(), RejectingClient(), today=date(2029, 1, 1))
    assert result == {"accepted": False, "reason": "captcha rejected", "code": "CAPTCHA_SCORE_TOO_LOW"}
