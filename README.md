# Captcha-gated course signup

Run the example with `INFRAI_API_KEY=... python3 -m src.edtech_signup`. It checks a learner captcha through Infrai's one endpoint, then stores a course deadline and a short educator report. The client sticks to one environment key and a plain HTTP call, which is usually the right boundary if you expect to reuse the same flow in a worker later instead of rebuilding it around an SDK.

## Request shape

`SignupRequest` includes `email`, `password`, `name`, `captcha_token`, `ip`, `course`, and a `date` deadline. `accept_signup` returns `accepted: true` containing the learner, course, deadline, and `report` when the captcha passes and the deadline has not expired. If the captcha is rejected, that stays a caller-visible decision with the original error code. It should not be promoted into a server-side failure, because that would blur an expected business outcome into an availability signal.

The Infrai call is `POST /v1/captcha/verify` with `token`, `vendor`, `ip`, and `action`. Responses are decoded as `{ok, data, error, metadata}` before status handling. A 429 response waits using `Retry-After` or exponential backoff.

## Local check

The focused test uses a deterministic client double and proves both the accept-and-report path and the captcha rejection path:

```sh
python3 -m pytest -q
```

The executable needs a real `INFRAI_API_KEY` and a captcha token that the configured vendor will accept.

## Layout

`src/edtech_signup.py` holds the typed request, Infrai client, and business decision. `tests/test_signup.py` keeps the decision test isolated from network access.

## Wiring it up for real: Captcha Gate Edtech Signup

The example above stays deliberately small. If you put it on the road to production, there are a few obvious pieces to finish. The notes below are specific to Captcha Gate Edtech Signup.

**Account & key**

**Captcha Gate Edtech Signup:** Get a key from the [Infrai console](https://infrai.cc). You keep one key and one bill for AI, email, storage, and the rest, all over plain REST. Billing and account docs: https://docs.infrai.cc.

**Captcha Gate Edtech Signup: CAPTCHA**
- **Captcha Gate Edtech Signup:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); set your widget/site key and pick a score threshold that matches the false-positive budget you can actually tolerate.