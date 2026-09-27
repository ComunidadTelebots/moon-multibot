# Shared plugin review — 2026-09-27

25 existing plugin modules were inventoried. New modules bring the shared catalog to 28.

| Area | Existing modules |
| --- | --- |
| Administration / security | admin, backup_utils, moderation_advanced, security_advanced |
| AI / media | ai_enhancer, image_analysis, inline_guest_ai_settings, learning_booster, voice_transcription |
| Community | social, social_polls, quick_polls, welcome_pack |
| Utilities | calculator, fun_random, help_extra, id_lookup, notes, password_tools, reminder_local, telegram_tools, text_tools, todo_manager, tutorial, url_tools |

## Added

- unit_converter: `/convertir 10 km m`, `/unidades`; length, mass, volume, time and temperature. Rejects nonfinite numbers, mismatched dimensions and temperatures below absolute zero.
- date_tools: `/diasentre 2024-02-28 2024-03-01`, `/sumardias 2024-03-01 -1`; ISO calendar dates, bounded offsets.
- data_utilities: `/jsonvalidar`, `/hashtexto`, `/utilidades`; bounded local processing. Submitted JSON is not echoed in the validation response.
- Calculator now parses a bounded arithmetic AST, replacing eval and limiting powers, input size, expression complexity and result magnitude.
- `/helpplus` links to `/utilidades`.

New plugins use the existing handle_command/send_msg contract, no external APIs or background threads, and no per-user mutable state. They are shared by bots loading this plugin directory; they do not provision child bots or alter bot permissions. Default command normalization handles @botname before plugin dispatch.

## Follow-up findings (not fixed by this patch)

- reminder_local starts a daemon thread per reminder; schedules do not survive restart.
- voice_transcription uses a shared temporary audio filename, risking concurrent collisions.
- notes and todo_manager use database keys without explicit bot identity; review tenant isolation before shared database scaling.
- backup and security commands warrant a separate permission and restoration audit.

## Validation scope

10 focused unit tests cover utilities, independent bot instances, calculator abuse limits and existing gateway media contracts. No real Telegram messages were sent for this patch. This inventory is not a full security audit or certification that all legacy plugins work through TDLib.
