# Energy-UA Power Off

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/pavlo-havrikov/energyua-poweroff)](https://github.com/pavlo-havrikov/energyua-poweroff/releases)

Компонент для Home Assistant, який показує графік погодинних відключень електроенергії (ГПВ) з підтримкою кількох обленерго.

## Підтримувані провайдери

| Провайдер | Область | Джерело даних |
|-----------|---------|---------------|
| **Запоріжжяобленерго** | Запорізька | [zoe.com.ua/outage](https://www.zoe.com.ua/outage/) |
| **Energy-UA** | Івано-Франківська, Львівська та ін. | [energy-ua.info](https://prykarpattya.energy-ua.info/) |

> Щоб додати підтримку нового обленерго — див. [Як додати провайдер](#як-додати-новий-провайдер).

## Можливості

- **Сенсор** — показує кількість запланованих відключень та повний розклад у атрибутах
- **Календар** — відображає графік відключень як події календаря в Home Assistant
- **Плагіни** — легке додавання нових обленерго через систему провайдерів

## Встановлення

### HACS (рекомендовано)

1. Відкрийте HACS у Home Assistant
2. Натисніть **Інтеграції** → меню ⋮ → **Користувацькі репозиторії**
3. Додайте URL репозиторію: `https://github.com/GrolGPA/ha-energyua-poweroff`
4. Категорія: **Integration**
5. Натисніть **Додати**, потім знайдіть "Energy-UA Power Off" та встановіть

### Вручну

1. Скопіюйте папку `custom_components/energyua_poweroff` до вашої директорії `config/custom_components/`
2. Перезапустіть Home Assistant

## Налаштування

1. Перейдіть до **Налаштування** → **Пристрої та служби** → **Додати інтеграцію**
2. Знайдіть **Energy-UA Power Off**
3. Оберіть вашого провайдера (обленерго)
4. Вкажіть вашу чергу (підчергу), наприклад: `1.1`, `2.2`, `3.1`

### Параметри

| Параметр | Обов'язковий | За замовчуванням | Опис |
|----------|:------------:|------------------|------|
| **Провайдер** | ✅ | Запоріжжяобленерго | Оператор системи розподілу (обленерго) |
| **Черга (підчерга)** | ✅ | — | Ваша черга у форматі `X.Y` (наприклад, `1.2`) |
| **URL джерела даних** | ❌ | *(з провайдера)* | Базова адреса сайту обленерго |

## Як дізнатися свою чергу

- **м. Запоріжжя**: [Перелік адрес для кожної з черг](https://www.zoe.com.ua/%d0%bf%d0%b5%d1%80%d0%b5%d0%bb%d1%96%d0%ba-%d0%b0%d0%b4%d1%80%d0%b5%d1%81-%d0%b4%d0%bb%d1%8f-%d0%ba%d0%be%d0%b6%d0%bd%d0%be%d1%97-%d0%b7-%d1%87%d0%b5%d1%80%d0%b3-%d0%b7-%d0%bf%d1%96%d0%b4%d1%87/)
- **Онлайн-пошук**: [Дізнатися свою чергу](https://script.google.com/macros/s/AKfycbzkN3KDDReQuxcjAHdkIpVoVwF2RKCSUnWlcwSPbipfMnxNWYuLF-BtZv2oHxk5FG_V/exec)

## Приклад автоматизації

```yaml
automation:
  - alias: "Сповіщення про відключення"
    trigger:
      - platform: calendar
        event: start
        entity_id: calendar.energy_ua_poweroff
        offset: "-00:30:00"
    action:
      - service: notify.mobile_app
        data:
          title: "⚡ Відключення електроенергії"
          message: "Через 30 хвилин буде відключення електроенергії"
```

## Як додати новий провайдер

1. Створіть файл `custom_components/energyua_poweroff/providers/my_provider.py`
2. Наслідуйте `BaseProvider` та реалізуйте `get_poweroff_schedule()`:

```python
from . import BaseProvider

class MyProvider(BaseProvider):
    key = "my_provider"                          # унікальний ключ
    name = "Моє Обленерго (example.com)"         # назва для UI
    default_base_url = "https://example.com"     # URL за замовчуванням

    def get_poweroff_schedule(self) -> list[dict[str, str]]:
        soup = self._fetch_soup(f"{self.base_url}/schedule")
        # ... парсинг HTML ...
        return [
            {"day": "2026-03-07", "hours": "08:00-12:00"},
        ]
```

3. Зареєструйте провайдер у `providers/__init__.py` → `_load_providers()`
4. Дані повинні відповідати контракту: `list[dict]` з ключами `"day"` (YYYY-MM-DD) та `"hours"` (HH:MM-HH:MM)

## Ліцензія

MIT
