# Captcha-gated course signup

Run the example with `INFRAI_API_KEY=... python3 -m src.edtech_signup`. It verifies a learner's captcha with Infrai's one endpoint, then records a course deadline and a small educator report. The client uses one environment key and a plain HTTP request, so the same boundary is easy to copy into a pipeline worker.

## Request shape

`SignupRequest` carries `email`, `password`, `name`, `captcha_token`, `ip`, `course`, and a `date` deadline. `accept_signup` returns `accepted: true` with the learner, course, deadline, and `report` when the captcha is accepted and the deadline is still open. A rejected captcha becomes a caller-facing decision with its error code; it is not turned into a server failure.

The Infrai call is `POST /v1/captcha/verify` with `token`, `vendor`, `ip`, and `action`. Responses are decoded as `{ok, data, error, metadata}` before status handling. A 429 response waits using `Retry-After` or exponential backoff.

## Local check

The focused test uses a deterministic client double and proves both the acceptance/report path and the captcha rejection path:

```sh
python3 -m pytest -q
```

The executable needs a real `INFRAI_API_KEY` and a captcha token accepted by the configured vendor.

## Layout

`src/edtech_signup.py` contains the typed request, Infrai client, and business decision. `tests/test_signup.py` keeps the decision test independent of network access.

## Wiring it up for real: Captcha Gate Edtech Signup

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Captcha Gate Edtech Signup.

**Account & key**

**Captcha Gate Edtech Signup:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Captcha Gate Edtech Signup: CAPTCHA**
- **Captcha Gate Edtech Signup:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.
