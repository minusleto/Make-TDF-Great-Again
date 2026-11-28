# Скиллы TDF / MDC

Проектные скиллы репозитория Make-TDF-Great-Again. Для задач этого репозитория применяются только правила TDF/MDC.

**Точка входа для агентов и людей — [`tdf-country-content/SKILL.md`](tdf-country-content/SKILL.md).** В нём контракт, маршрутизация к справочникам с оценкой их размера и правила экономии токенов. Эта таблица здесь намеренно не дублируется.

## Состав

- `tdf-country-content/` — основной скилл: `SKILL.md`, справочники `references/`, статический аудитор и тесты в `scripts/` и `tests/`.
- `hoi4-nested-national-spirits/` — узкий дополнительный скилл для составных национальных духов (подключается из маршрутизации `SKILL.md`).
- [`../docs/research/`](../docs/research/README.md) — проектные аудиты и фактчеки.

## Роли файлов навигации

| Файл | Роль | Когда читать |
|---|---|---|
| `../AGENTS.md` | Правила работы с репозиторием | Всегда |
| `tdf-country-content/SKILL.md` | Контракт + маршрутизация | При любой задаче с контентом страны |
| `tdf-country-content/references/README.md` | Карта источников правды, статусы положений, граница ERROR/WARN | Только при конфликте правил |

## Устройство аудитора

`tdf-country-content/scripts/tdf_audit.py` это тонкая точка входа (запуск и совместимые имена для тестов и `tdf_inventory.py`); код лежит в пакете `scripts/tdf_audit_lib/`. Зависимости идут только вниз по таблице:

| Модуль | Что делает | Зависит от |
|---|---|---|
| `core` | типы, токенайзер и парсер HOI-скриптов, обход файлов, общие константы | ничего |
| `indexes` | поиск тегов, индексы идей, локализации и глобальные индексы | core |
| `decisions` | аудит решений | core, indexes |
| `state_flow` | поток флагов, переменных, массивов, scripted effects | core, decisions |
| `events` | аудит событий | core, indexes |
| `ideas` | жизненный цикл нацдухов и идей | core, indexes |
| `industry` | MIO, техника, модули, технологии | core, decisions |
| `external_dependencies` | внешние зависимости и реестр | core |
| `connectivity` | связность веток фокусов | core, indexes, state_flow |
| `country` | результат аудита одной страны | core, events, indexes |
| `cli` | классификация ERROR/WARN/INFO и командная строка | все остальные |

Новый аудит: отдельный модуль в `tdf_audit_lib/`, подключить его в `cli.py` и добавить в список импорта в `tdf_audit.py`. Циклы запрещены, `core` ни от кого не зависит, модуль не длиннее 1200 строк: это проверяют тесты (`test_tdf_audit_layout.py`).

## Проверка после правок

Из корня репозитория, после связанной серии изменений:

```bash
python3 -I skills/tdf-country-content/scripts/tdf_inventory.py .
python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --require-external-registry
python3 -I skills/tdf-country-content/scripts/tdf_baseline.py check   # только новые находки относительно baseline
python3 -I skills/tdf-country-content/scripts/tdf_ship.py --dry-run   # проверить условия отправки через PR
python3 -I skills/tdf-country-content/scripts/tdf_registry_import.py --target-dir <каталог> --build-label "..."   # подтвердить внешние ID по целевой сборке (пробный прогон)
python3 -I -m unittest discover -s skills/tdf-country-content/tests -v
```

Подробности по флагам аудитора (`--tags`, `--details`) и границам проверки — в `tdf-country-content/SKILL.md`.
