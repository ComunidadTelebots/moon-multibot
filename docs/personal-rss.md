# Personal RSS (beta)

The stable service exposes personal subscriptions in the Telegram Hub and the web dashboard. A shared manager stores compatible `GROUP_RSS_<chat>` records. Personal scheduling accepts only positive private chat IDs known to a running bot. It never changes group delivery. The engine is adapted from the development branch group RSS implementation, with DNS-pinned public-address fetching and no group-policy dependencies.

New subscriptions start paused. The first poll primes the cursor instead of sending historical entries. Limits: 20 sources per user, polling every 15 minutes by default, 3 new entries per source/cycle, bounded response size and failure backoff. Feed statistics count successful Telegram deliveries, not readership.

Every private user gets 50 daily RSS slots across all feeds and bots, reset at UTC midnight. Above the allowance, membership of @TodoSobreAllTech must be verified using an administrator bot. API failures and nonmembers remain blocked above the quota. Positive checks are cached for at most 5 minutes; explicit rechecks have a 15-second cooldown. Successful slots and uncertain send reservations survive process restart. An ambiguous delivery is quarantined by the `PERSONAL_RSS_INFLIGHT_<uid>` record and requires operator reconciliation; automatic replay is intentionally disabled.

The process uses a single scheduler guarded by a file lock on the same local persistent data directory as the governor. It is single-host coordination, not distributed high availability. Do not run the development group scheduler over personal chat IDs at the same time: integrate the quota policy there before promoting both schedulers together.

Web API destinations derive exclusively from the authenticated account telegram_id. Master activity requires creator role. Hub actions derive the user from signed Telegram initData. Internal endpoints require the admin key and never take credentials from the browser. New subscriptions and activation require explicit user actions; deployment creates no subscriptions and sends no Telegram messages.

Source and recipient rankings use accumulated available counters (which operators may reset), rather than claiming time-window or click analytics. The news catalog offers the verified TodoSobreAllTech RSS endpoint; users may supply another public RSS/Atom URL.

## Channels and catalog

The Hub and web expose a category catalog and private/channel destination selector. Channel subscriptions require live Telegram administrator rights and can_post_messages for both the actor and the bot; a cached admin list is only used for discovery. Scheduled channel delivery revalidates the last responsible administrator. Channel deliveries do not consume a private user's 50-item quota. Existing development group schedulers must not concurrently process these channel targets. No subscription is created by installing this release.

Nine initial RSS/Atom sources were validated from the VPS, spanning technology, news, international affairs, sports, science, culture, economics, weather and space. Sources: https://www.rtve.es/rss/ and https://cneos.jpl.nasa.gov/feed/ plus TodoSobreAllTech's own RSS. Only the original headline and link are sent. Shared feed reads are cached for 5 minutes with a bounded cache.

RSS.app expansion: seven existing public project feeds were validated from Hostinger and added, bringing the catalog to 16 sources. The reader supports RSS/Atom XML and JSON Feed 1/1.1 with bounded items and original links. Known self-channel mirrors are rejected for that destination on add/enable, including TodoSobreAllTech news to its own Telegram channel. This is not a claim to detect every possible indirect syndication loop. The Hub styling inherits --bg/--ink/--teal/--cyan instead of assuming a white Telegram background.
