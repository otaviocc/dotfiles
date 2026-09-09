---
name: brrr
description: Send a push notification to the user's devices via the Brrr API. Use when asked to send a push notification, ping me, notify when something finishes, or any similar request. Accepts a title and message; optional thread_id, sound, and interruption_level.
---

# Send a Brrr Push Notification

Posts a JSON payload to the Brrr API. The `BRRR_SECRET` environment variable must be set in the shell (e.g. via `export BRRR_SECRET=...` or a shell profile).

## Usage

Build a JSON payload and POST it:

```bash
curl -sS -X POST https://api.brrr.now/v1/send \
    -H "Authorization: Bearer $BRRR_SECRET" \
    -H 'Content-Type: application/json' \
    -d '{"title":"<title>","message":"<message>","thread_id":"<optional>","interruption_level":"passive","sound":"<optional>"}'
```

A successful response looks like `{"success":true,...}`. Anything else is a failure — surface it to the user.

## Payload fields

- `title` (required): Short headline, e.g. `"Build finished"`.
- `message` (required): Body text.
- `thread_id` (optional): Groups related notifications on the device. Use a stable slug per topic (e.g. `obsidian-sync`, `ci`, `opencode-task`).
- `interruption_level` (optional): `passive` for non-urgent updates, `active` (default), `time-sensitive`, or `critical`.
- `sound` (optional): e.g. `warm_soft_error` for failures.

## Steps

1. Derive `title` and `message` from the user's request. If they only gave one string, use it as the message and synthesise a short title.
2. Pick a sensible `thread_id` and `interruption_level` from context (default `passive` unless the user implies urgency).
3. Run the `curl` above and check the JSON response.
4. Report success (one line) or the error body if it failed.

## Notes

- Escape quotes properly when building the payload — prefer a heredoc or `jq -n` for anything with user-supplied text containing quotes or newlines.
- Never log or echo `$BRRR_SECRET`.
