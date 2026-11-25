# Скилы TDF / MDC

Это пакет скилов внутри репозитория Make-TDF-Great-Again. Пути ниже указаны относительно этой папки (`skills/`).

## Маршрутизация

Для работы над контентом стран в этом репозитории основной и единственный общий скил — `tdf-country-content`. Не загружай вместе с ним `md-hoi4-country-content`: это общий скил для других MD/HOI4-проектов, и его правила не должны конкурировать с проектными правилами TDF.

| Задача | Что читать |
|---|---|
| Любая работа с контентом страны TDF/MDC в этом репозитории | `tdf-country-content/SKILL.md` |
| Единственный источник правила / подробная маршрутизация по доменам | `tdf-country-content/references/README.md` |
| Формат `.txt`, focus-комментарии, YML BOM/CRLF и сохранение legacy | `tdf-country-content/references/file-formatting.md` |
| Контекст конкретной страны, уже использованные темы и примеры | Сначала `tdf-country-content/references/countries/README.md`, затем только карточку нужного тега |
| Проектирование или ревью целой ветки, выбор между фокусом, решением, событием и духом | Дополнительно `tdf-country-content/references/design-guide.md` |
| Структура страны и полный обзор её систем | `tdf-country-content/references/country-structure.md` |
| Код фокусов, prerequisite, `available`, `bypass`, структура дерева | `tdf-country-content/references/focus-design.md` |
| Описания и локализация фокусов | `tdf-country-content/references/focus-loc.md` |
| Решения: категории, стоимость, повторяемость, AI, география и связи | `tdf-country-content/references/decision-design.md` |
| Межфайловые связи: flags, variables, arrays, scripted effects/triggers, on_actions и history | `tdf-country-content/references/state-flow.md` |
| Внешние зависимости и проверка base-MD / HOI4 IDs | `../docs/research/external-dependencies.md` (реестр: `../docs/research/external-dependencies.json`) |
| События, цепочки и локализация событий | `tdf-country-content/references/event-loc.md` |
| Обычные национальные духи | `tdf-country-content/references/national-spirits.md` |
| Составной дух-хаб с несколькими скрытыми идеями-компонентами и общим tooltip | Дополнительно `hoi4-nested-national-spirits/SKILL.md` |
| Баланс, типовые ошибки и итоговый чек-лист | `tdf-country-content/references/balance-and-pitfalls.md` |
| Любая работа с Казахстаном (структура, код, локализация, исторические детали) | Дополнительно `tdf-country-content/references/kazakhstan-maintenance.md` |
| Разработка и QA механики Аральского моря | `aral-sea-mechanic/SKILL.md` вместе с основным TDF skill и карточкой KAZ |

Подробный source-of-truth map и область применения каждого справочника находятся в `tdf-country-content/references/README.md`; эта таблица — краткая стартовая маршрутизация. Читай только материалы, относящиеся к текущей задаче. Не загружай весь каталог `references/` по умолчанию. Для country style cards загружай одну карточку соответствующего тега, а не весь каталог стран. `design-guide.md` нужен для проектирования или содержательного ревью целой ветки; для точечной правки одного фокуса, события или ключа локализации не открывай его автоматически.

## Выборочные материалы общего MD Skill

`md-hoi4-country-content/SKILL.md` предназначен для других Millennium Dawn / HOI4-проектов и в этом репозитории не активируется. Если в TDF-задаче нужен отдельный технический шаблон, можно открыть только соответствующий файл из его `references/` — без загрузки самого generic Skill:

- `md-hoi4-country-content/references/balance.md` — числовые медианы и ориентиры;
- `md-hoi4-country-content/references/code-patterns.md` — отдельные шаблоны кода и дипломатических цепочек.

Оба файла — вспомогательные примеры, а не источник приоритета над TDF-правилами. Проверяй синтаксис и применимость по текущему репозиторию и wiki.

## Проверка после правок

Из корня репозитория, после связанной серии изменений (не после каждой мелкой правки):

```bash
python3 -I skills/tdf-country-content/scripts/tdf_inventory.py .
python3 -I skills/tdf-country-content/scripts/tdf_audit.py .
python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --tags KAZ
python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --details KAZ
```

`--tags` ограничивает сводку выбранными тегами; `--details` выводит подробные списки для одного тега. Ошибки (ERROR) требуют проверки, WARN — ручного разбора; статистика и DESIGN не равны багам. Скрипт проверяет текстовую структуру, но не запускает игру и не проверяет базовый мод.

## Состав пакета

- `tdf-country-content/` — основной скил проекта, проектные справочники и `tdf_audit.py`.
- `hoi4-nested-national-spirits/` — узкий дополнительный скил для составных национальных духов.
- `md-hoi4-country-content/` — общий скил для других MD/HOI4-проектов; в этом TDF-репозитории не активировать. `scripts/mdindex.py` нужен для больших наборов загруженных файлов, а не для поиска в checkout-репозитории.
- `../docs/research/` — проектные аудиты и фактчеки; текущая структурная инвентаризация на 2026-11-24: `2026-11-24-tdf-inventory.md`; аудит деревьев 2026-10 — исторический срез.

- `../md-hoi4-country-content.skill` — старый упакованный пакет, не синхронизируется с живыми файлами в `skills/`.
- `skills/tdf-country-content/references/mio-and-equipment.md` — MIO, equipment, variants, research technology and military industry QA.
