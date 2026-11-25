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

## Проверка после правок

Из корня репозитория, после связанной серии изменений:

```bash
python3 -I skills/tdf-country-content/scripts/tdf_inventory.py .
python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --require-external-registry
python3 -I -m unittest discover -s skills/tdf-country-content/tests -v
```

Подробности по флагам аудитора (`--tags`, `--details`) и границам проверки — в `tdf-country-content/SKILL.md`.
