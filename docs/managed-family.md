# Managed family inventory

The governor exposes a credential-free family inventory for the two approved group-backup identities. Every enrollment is verified through the parent's getManagedBotToken permission. Tokens are encrypted with the existing token manager and stored separately from the active bot store; no plugin workers, polling sessions or automatic failover are started for these children.

The inventory refreshes every two minutes. It checks at most eight known negative chat IDs per parent per cycle. A group counts as permission-ready only when the child is an administrator with delete_messages and restrict_members. This is a progressive, cached inventory (30-minute expiry), not authorization to execute moderation. A future task handoff must check rights live and establish exclusive group/task ownership before any child executes plugins.

The web shows the parent relationship, enrollment status and verified permission counts, with a Telegram add-to-group link requesting only moderation rights. It explicitly states that failover is pending. No test sends messages or grants rights.

Managed bot updates are now requested in allowed_updates; managed_bot_created service messages are also recorded. Historical missed updates cannot be recovered merely by changing allowed_updates, so these two approved identities are resolved by username and their parent relationship is proved via token export.
