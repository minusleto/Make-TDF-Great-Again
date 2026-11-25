---
name: tdf-country-content
description: 'Required workflow and reference routing for designing, editing and reviewing country content (focus trees, events, decisions, national spirits, localisation, MIO and equipment) in Make-TDF-Great-Again (TDF/MDC). Use for any country-content task in this repository; open only the references the task needs.'
---

# TDF country content

Это обязательный контракт и единая точка входа: прочитай файл целиком, затем открывай **только** строки таблицы, относящиеся к задаче. Подробные правила живут в `references/`, у каждого один основной источник; не дублируй их в других местах.

## Маршрутизация

Пути относительно этого файла. «Размер» — примерная стоимость полного чтения в токенах.

| Задача | Файл | Размер | Примечание |
|---|---|---|---|
| Формат `.txt` и YML: табы, BOM, CRLF, legacy | `references/file-formatting.md` | ≈1.5k |  |
| Код фокуса: prerequisite, `available`, `bypass`, структура дерева | `references/focus-design.md` | ≈7.5k |  |
| Заголовок, описание и ключи локализации фокуса | `references/focus-loc.md` | ≈7.5k |  |
| Шаблоны кода: порядок полей, цепочка предложение→ответ, эффекты, техи, техника | `references/code-patterns.md` | ≈1.5k |  |
| Решения: категории, стоимость, повторяемость, AI | `references/decision-design.md` | ≈10k |  |
| События, цепочки, локализация событий | `references/event-loc.md` | ≈8.5k |  |
| Национальные духи (обычные) | `references/national-spirits.md` | ≈11k | большой: читать по разделам |
| Составной дух-хаб со скрытыми компонентами и общим tooltip | `../hoi4-nested-national-spirits/SKILL.md` | ≈6.5k | дополнительно к предыдущему |
| MIO, equipment, модули, технологии, варианты | `references/mio-and-equipment.md` | ≈4k |  |
| Flags, variables, arrays, scripted effects/triggers, on_actions, history | `references/state-flow.md` | ≈4k |  |
| Баланс, типовые ошибки, медианы, итоговый чек-лист | `references/balance-and-pitfalls.md` | ≈4.5k |  |
| Проектирование или ревью **целой ветки**, выбор focus/decision/event/idea | `references/design-guide.md` | ≈10k | для точечной правки не нужен |
| Структура страны и обзор её систем | `references/country-structure.md` | ≈5k | обзор, не для точечной правки |
| Контекст страны и уже использованные темы | `references/countries/README.md` | ≈1.5k | затем один `countries/<tag>.md` ≈1.5k |
| Любая работа с Казахстаном | `references/kazakhstan-maintenance.md` | ≈15k | большой: читать по разделам; дополнительно |
| Внешние и неразрешённые ID | `../../docs/research/external-dependencies.md` | ≈2k |  |
| Конфликт правил, статус положения ([REQUIRED]/[RECOMMENDED]/…), граница ERROR/WARN | `references/README.md` | ≈4k | только при конфликте |

## Экономия токенов

- Файл больше ~100 строк не читай целиком: `grep -n '^#' <файл>`, затем нужный диапазон (`sed -n 'A,Bp'` или `view_range`).
- Для точечной правки одного фокуса, события или ключа локализации не открывай `design-guide.md` и `country-structure.md`.
- Открывай одну карточку страны, а не весь `countries/`; карточка — контекст, а не шаблон.
- Деревья и локализация в `mdredux/` огромны: ищи по ID (`grep -n "<ID>"`), читай найденный блок, а не файл целиком.
- Перед правкой найди весь затрагиваемый контекст одним поиском по ID, а не открывай файлы подряд.

## Обязательный рабочий цикл

1. **Найти затрагиваемый контекст.** Focus, prerequisites, available/bypass, events, decisions, ideas, scripted localisation, flags/variables/arrays, MIO, equipment, technology и localisation: только то, на что реально ссылается задача.
2. **Проверить код, прежде чем писать обещание.** Текст должен соответствовать фактической награде и механике; ID, scope, источник и получатель должны быть понятны. Если следствие не подтверждено кодом, не выдавать его за факт.
3. **Разделять факты и сценарий.** Исторические утверждения проверять по актуальным надёжным источникам. Альтернативную историю и внутриигровые допущения ясно отделять от реальной истории.
4. **Не унифицировать страны.** Country cards и примеры — контекст, а не шаблоны; не переносить стиль, политическую систему или механику одной страны в другую автоматически.
5. **Сделать связанный набор правок, затем один общий QA-проход.** Сохранять локальный формат файлов и не нормализовать нетронутый legacy-контент. При нескольких затронутых файлах предпочитать один коммит на задачу.

## Границы знания и статический аудит

В checkout нет полного набора файлов целевой сборки. Внешние ID сверять с `docs/research/external-dependencies.md` и машинным реестром `docs/research/external-dependencies.json`. Отсутствие ID в локальном срезе само по себе не доказывает ошибку.

Из корня репозитория:

```bash
python3 -I skills/tdf-country-content/scripts/tdf_inventory.py .
python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --require-external-registry
python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --tags KAZ      # сводка по тегу
python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --details KAZ   # подробные списки
python3 -I -m unittest discover -s skills/tdf-country-content/tests -v
```

Запускай после связанной серии правок, а не после каждой мелкой. Инвентаризация — воспроизводимый подсчёт файлов и блоков, а не оценка качества. В аудиторе ERROR означает доказуемую структурную проблему или нарушенную локальную ссылку; WARN — кандидат на ручную проверку; INFO — справочный сигнал. Длина, generic labels, слова-сигналы и другие редакторские эвристики не становятся ERROR без доказуемой технической причины.

Ни аудитор, ни unit-тесты не запускают HOI4. Не заявлять, что игровой runtime, UI, баланс или внешние определения проверены, если фактически этого не было.
