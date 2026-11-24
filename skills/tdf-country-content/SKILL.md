---
name: tdf-country-content
description: 'Project-specific required workflow for designing, editing and reviewing country content in Make-TDF-Great-Again (TDF/MDC). Use for any country-content task in this repository. Detailed domain rules live in references; for other HOI4/MD projects use md-hoi4-country-content.'
---

# TDF country content

Это обязательный общий контракт для работы с контентом TDF/MDC, а не полный справочник всех механик. Подробные правила имеют по одному основному источнику: `references/README.md`. Не дублируй там изложенные правила в новых местах.

## Старт и маршрутизация

1. Прочитать `skills/README.md` и этот SKILL.
2. Для текущей задачи открыть только относящиеся к ней документы по карте `references/README.md`.
3. При работе над страной открыть только её карточку из `references/countries/README.md`, если она существует. Не загружать все карточки.
4. Для составного духа-хаба с несколькими скрытыми компонентами дополнительно открыть `skills/hoi4-nested-national-spirits/SKILL.md`. Для обычной идеи он не нужен.

## Обязательный рабочий цикл

1. **Найти весь затрагиваемый контекст.** Focus, prerequisites, available/bypass, events, decisions, ideas, scripted localisation, flags/variables/arrays, MIO, equipment, technology и localisation — открывать только то, на что реально ссылается задача.
2. **Проверить код, прежде чем писать обещание.** Текст должен соответствовать фактической награде и механике; ID, scope, источник и получатель должны быть понятны. Если следствие не подтверждено кодом, не выдавать его за факт.
3. **Разделять факты и сценарий.** Исторические утверждения проверять по актуальным надёжным источникам. Альтернативную историю и внутриигровые допущения ясно отделять от реальной истории.
4. **Не унифицировать страны.** Country cards и примеры — контекст, а не шаблоны; не переносить стиль, политическую систему или механику одной страны в другую автоматически.
5. **Сделать связанный набор правок, затем один общий QA-проход.** Сохранять локальный формат файлов и не нормализовать нетронутый legacy-контент. При нескольких затронутых файлах предпочитать один коммит на задачу.

## Границы знания и статический аудит

В checkout нет полного базового Millennium Dawn, vanilla и DLC. Внешние ID сверять с `docs/research/external-dependencies.md` и машинным реестром `docs/research/external-dependencies.json`. Отсутствие ID в локальном срезе само по себе не доказывает ошибку.

Из корня репозитория:

```bash
python3 -I skills/tdf-country-content/scripts/tdf_inventory.py .
python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --require-external-registry
python3 -I -m unittest discover -s skills/tdf-country-content/tests -v
```

Инвентаризация — воспроизводимый подсчёт файлов и блоков, а не оценка качества. В auditor ERROR означает доказуемую структурную проблему или нарушенную локальную ссылку; WARN — кандидат на ручную проверку; INFO — справочный сигнал. Длина, generic labels, слова-сигналы и другие редакторские эвристики не становятся ERROR без доказуемой технической причины. Подробная классификация и regression tests перечислены в `references/README.md`.

Ни auditor, ни unit tests не запускают HOI4. Не заявлять, что игровой runtime, UI, баланс или базовый MD проверены, если фактически этого не было.
