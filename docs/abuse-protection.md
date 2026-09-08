# Abuse protection

The bot uses local, process-level protection against accidental repeated taps
and basic update floods. It does not require Redis, an extra database, or an
extra container.

## Telegram group setting

Repka is designed for personal chats. In `@BotFather`, disable **Allow Groups**
for the production bot so Telegram users cannot add it to groups. This setting
is managed by Telegram, not by the application code.

## Per-user rate limit

Before localization, handlers, and API requests, the bot accepts at most **4
updates from one Telegram user during a rolling 2-second window**. Further
updates in that window are silently ignored.

Messages and callback-button presses both count as updates. The limiter keeps
at most 10,000 recently seen user IDs in process memory; older IDs are evicted.
It resets whenever the bot process restarts.

## Global concurrency guard

The polling dispatcher processes at most **20 updates concurrently**. Under
ordinary use this limit is not reached. During a flood, excess updates remain
with Telegram until a processing slot is free, instead of creating unlimited
handler tasks and exhausting the VPS.

This is a capacity guard, not a per-chat queue: it only affects users while the
bot is already at its 20-update processing ceiling.

## Duplicate weekly-card prevention

Weekly PNG rendering is not queued and has no time-based cooldown. Instead, the
bot keeps an in-flight marker:

- for one exercise card: `(user, exercise, report)`;
- for a whole weekly report: `(user, report)`.

While that exact generation is running, repeated taps do nothing and cannot
produce duplicate images. The marker is removed immediately after the image is
sent or the attempt fails. A user can request the same card again as soon as
the prior attempt is finished, including one minute later.

## Current boundary

The API is bound to the VPS loopback interface and must remain private to the
bot/VPS network. Its identity fields identify a Telegram user but are not a
public-client authentication mechanism. If the API is ever exposed beyond that
private network, add a separate authentication layer before doing so.
