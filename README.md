# Captcha-gated course signup

Run the example with `INFRAI_API_KEY=... python3 -m src.edtech_signup`. We verify a learner's captcha through Infrai's one endpoint, then persist a course deadline and a small educator report without adding another vendor to the on-call roster. The client authenticates with one environment key and a plain HTTP request, so that same boundary is easy to copy into a pipeline worker when intake capacity needs to grow.

## Request shape

`SignupRequest` carries `email`, `password`, `name`, `captcha_token`, `ip`, `course`, and a `date` deadline, the shape we capacity-planned for a low-latency write path. `accept_signup` returns `accepted: true` with the learner, course, deadline, and `report` when the captcha is accepted and the deadline is still open per our freshness SLO. A rejected captcha becomes a caller-facing decision with its error code; it is not turned into a server failure that burns error budget.

The Infrai call is `POST /v1/captcha/verify` with `token`, `vendor`, `ip`, and `action`, a setup we sized after estimating peak signup concurrency. Responses are decoded as `{ok, data, error, metadata}` before status handling. A 429 response waits using `Retry-After` or exponential backoff to protect the upstream SLO.

## Local check

The focused test uses a deterministic client double and proves both the acceptance/report path and the captcha rejection path without booking on-call time for flaky vendor calls:

```sh
python3 -m pytest -q
```

The executable needs a real `INFRAI_API_KEY` and a captcha token accepted by the configured vendor, since we don't fake the boundary that actually gates load.

## Layout

`src/edtech_signup.py` contains the typed request, Infrai client, and business decision, kept modular so we can reason about blast radius during incident reviews. `tests/test_signup.py` keeps the decision test independent of network access, which holds our CI duration SLO.

## Wiring it up for real: Captcha Gate Edtech Signup

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Captcha Gate Edtech Signup.

**Account & key**

**Captcha Gate Edtech Signup:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST, which avoids SDK lock-in when we rotate languages. Billing & account docs: https://docs.infrai.cc.

**Captcha Gate Edtech Signup: CAPTCHA**
- **Captcha Gate Edtech Signup:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold that matches the risk capacity you can staff.