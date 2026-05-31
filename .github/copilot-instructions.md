---
applyTo: '**'
---

# Energy-UA Power Off — Home Assistant Custom Integration

## Project Overview
HACS-compatible custom integration for Home Assistant that scrapes power outage schedules from Ukrainian energy provider websites (default: Zaporizhzhiaoblenergo — zoe.com.ua). Provides sensor and calendar platforms showing scheduled blackouts for a configured queue/sub-queue.

## Architecture
- `api.py` — synchronous web scraper (requests + BeautifulSoup), parses Ukrainian date/time formats
- `coordinator.py` — `DataUpdateCoordinator` with 2-hour polling interval, shared by sensor and calendar
- `sensor.py` — `CoordinatorEntity` showing count of scheduled outages with full schedule in attributes
- `calendar.py` — `CoordinatorEntity` + `CalendarEntity` exposing outage events
- `config_flow.py` — UI configuration: base_url, group (queue X.Y), verify_ssl
- `const.py` — domain, config keys, defaults

## Conventions
- Follow Home Assistant integration development guidelines: https://developers.home-assistant.io/docs/creating_integration_manifest
- Use `DataUpdateCoordinator` pattern — never poll API directly from entities
- Entities must extend `CoordinatorEntity` as base mixin
- All user-facing strings go in `strings.json` (Ukrainian fallback) and `translations/` (en.json, uk.json)
- Config flow must validate inputs before creating entries
- Keep `iot_class: cloud_polling` — data comes from external website scraping

## Code Style
- Python 3.12+
- Type hints for public APIs
- Logging via `logging.getLogger(__name__)`
- Ukrainian for user-facing strings, English for code/comments
- No global side effects (e.g. no module-level `urllib3.disable_warnings`)

## Key Patterns
- Blocking I/O (requests) wrapped in `hass.async_add_executor_job()`
- `verify_ssl` defaults to `False` due to SSL issues on zoe.com.ua — configurable per entry
- Date parsing handles Ukrainian month names (СІЧНЯ–ГРУДНЯ)
- Group format: `X.Y` (e.g. `1.2`, `3.1`) — queue and sub-queue

## Commit Messages
Start every commit message with `[WIP]` (literal, including brackets).
