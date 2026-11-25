# Скиллы TDF / MDC

Это проектные скиллы репозитория Make-TDF-Great-Again. Для задач этого репозитория применяются только правила TDF/MDC.

## Маршрутизация

| Задача | Что читать |
|---|---|
| Любая работа с контентом страны TDF/MDC | `tdf-country-content/SKILL.md` |
| Подробная маршрутизация и source-of-truth по доменам | `tdf-country-content/references/README.md` |
| Формат `.txt`, focus-комментарии, YML BOM/CRLF и сохранение legacy | `tdf-country-content/references/file-formatting.md` |
| Контекст конкретной страны и уже использованные темы | `tdf-country-content/references/countries/README.md`, затем только карточку нужного тега |
| Проектирование или ревью целой ветки | Дополнительно `tdf-country-content/references/design-guide.md` |
| Структура страны и её систем | `tdf-country-content/references/country-structure.md` |
| Код фокусов, prerequisite, `available`, `bypass`, структура дерева | `tdf-country-content/references/focus-design.md` |
| Описания и локализация фокусов | `tdf-country-content/references/focus-loc.md` |
| Решения: категории, стоимость, повторяемость, AI, география и связи | `tdf-country-content/references/decision-design.md` |
| Межфайловые связи: flags, variables, arrays, scripted effects/triggers, on_actions и history | `tdf-country-content/references/state-flow.md` |
| Внешние и пока неразрешённые зависимости TDF | `../docs/research/external-dependencies.md` и `../docs/research/external-dependencies.json` |
| События, цепочки и локализация событий | `tdf-country-content/references/event-loc.md` |
| Национальные духи | `tdf-country-content/references/national-spirits.md` |
| Составной дух-хаб с несколькими скрытыми идеями-компонентами | Дополнительно `hoi4-nested-national-spirits/SKILL.md` |
| Баланс, типовые ошибки и итоговый чек-лист | `tdf-country-content/references/balance-and-pitfalls.md` |
| Любая работа с Казахстаном | Дополнительно `tdf-country-content/references/kazakhstan-maintenance.md` |

Читай только материалы, относящиеся к текущей задаче. Не загружай весь каталог `references/` по умолчанию. Для country style cards открывай одну карточку нужного тега, а не весь каталог стран.

Для модификаторов, эффектов и триггеров сначала проверяй вики MDC: https://github.com/minusleto/MDC. Если нужного определения или объяснения там нет, попроси пользователя прислать соответствующий файл целевой сборки. Не подменяй отсутствующие данные сведениями из другого мода или общими предположениями.

## Проверка после правок

После связанной серии изменений из корня репозитория:

```bash
python3 -I skills/tdf-country-content/scripts/tdf_inventory.py .
python3 -I skills/tdf-country-content/scripts/tdf_audit.py .
python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --tags KAZ
python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --details KAZ
python3 -I -m unittest discover -s skills/tdf-country-content/tests -v
```

`--tags` ограничивает сводку выбранными тегами; `--details` выводит подробные списки для одного тега. ERROR требует проверки, WARN — ручного разбора; статистика и DESIGN не равны багам. Скрипт проверяет текстовую структуру, но не запускает игру.

## Состав пакета

- `tdf-country-content/` — основной скил проекта, справочники и статический аудитор.
- `hoi4-nested-national-spirits/` — узкий дополнительный скил для составных национальных духов.
- `../docs/research/` — проектные аудиты и фактчеки.
