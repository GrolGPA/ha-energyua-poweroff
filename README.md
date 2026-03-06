# Energy-UA Power Off

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/pavlo-havrikov/energyua-poweroff)](https://github.com/pavlo-havrikov/energyua-poweroff/releases)

Компонент для Home Assistant, який показує графік погодинних відключень електроенергії (ГПВ) на основі даних з сайту [zoe.com.ua](https://www.zoe.com.ua/outage/).

## Можливості

- **Сенсор** — показує кількість запланованих відключень та повний розклад у атрибутах
- **Календар** — відображає графік відключень як події календаря в Home Assistant

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
3. Вкажіть вашу чергу (підчергу), наприклад: `1.1`, `2.2`, `3.1`

### Параметри

| Параметр | Обов'язковий | За замовчуванням | Опис |
|----------|:------------:|------------------|------|
| **Черга (підчерга)** | ✅ | — | Ваша черга у форматі `X.Y` (наприклад, `1.2`) |
| **URL джерела даних** | ❌ | `https://www.zoe.com.ua` | Базова адреса сайту обленерго |

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

## Ліцензія

MIT
