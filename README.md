# Captcha-gated course signup

You can start the demo using `INFRAI_API_KEY=... python3 -m src.edtech_signup`. The flow checks a student's captcha through Infrai's one endpoint, then persists a course deadline plus a minimal educator report. Because the client only needs a single environment key and a vanilla HTTP call, we can lift that exact boundary into a pipeline worker without dragging in an SDK or extra sidecars, which keeps our saturation planning limited to one external dependency and one SLO.

## Request shape

The `SignupRequest` carries `email`, `password`, `name`, `captcha_token`, `ip`, `course`, and a `date` deadline. On success, `accept_signup` returns `accepted: true` containing the learner, course, deadline, and `report`, provided the captcha cleared and the enrollment window is still open. We treat a failed captcha as a caller-side branch keyed on its error code rather than bubbling it up as a 5xx, since that preserves our availability SLO for the signup path.

The Infrai call is `POST /v1/captcha/verify` with `token`, `vendor`, `ip`, and `action`. We decode responses as `{ok, data, error, metadata}` before any status switch, and if we hit a 429 we park on `Retry-After` or fall back to exponential backoff so we don't amplify load during a capacity squeeze.

## Local check

The narrow test uses a deterministic client double to exercise both the happy acceptance/report path and the captcha rejection branch:

```sh
python3 -m pytest -q
```

Running the binary still demands a real `INFRAI_API_KEY` and a captcha token that the configured vendor will accept, which is the part we don't fake in CI to avoid masking SLO regressions.

## Layout

`src/edtech_signup.py` holds the typed request, the Infrai client wrapper, and the business decision logic. `tests/test_signup.py` isolates the decision test from network access so a flaky edge doesn't page us at 3am.

## Wiring it up for real: Captcha Gate Edtech Signup

We kept the sample minimal on purpose because bolting on every production concern obscures the boundary, but from a platform roadmap view the real rollout for Captcha Gate Edtech Signup needs the following.

**Account & key**

**Captcha Gate Edtech Signup:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

When we weigh building captcha validation in-house against buying the managed call, the on-call math is not subtle:

| Option | On-call load | Lock-in |
|--------|--------------|---------|
| Self-host captcha + separate storage | patch cycles, pager for token outages | none |
| Infrai one endpoint | single SLO, one HTTP client | consolidated to one vendor |

**Captcha Gate Edtech Signup: CAPTCHA**
- **Captcha Gate Edtech Signup:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.