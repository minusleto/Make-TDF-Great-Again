# Make-TDF-Great-Again

- `mdredux/` — исходники самостоятельного мода TDF: деревья, духи, решения, события и локализация
- `wiki/` — справочник по коду MDC
- `docs/research/` — аудиты и исследования; статические отчёты не заменяют проверку в игре
- `skills/` — скиллы проекта (индекс: `skills/README.md`): основной `tdf-country-content` и узкий `hoi4-nested-national-spirits`
- `AGENTS.md` — инструкции для работы с репозиторием

## Быстрый старт

Из корня репозитория (нужен только Python 3, внешних зависимостей нет):

```bash
python3 -I -m unittest discover -s skills/tdf-country-content/tests   # тесты инструментов
python3 -I skills/tdf-country-content/scripts/tdf_baseline.py check   # только новые находки аудита
```

Проект развивает инструменты и скиллы поиска ошибок; известные находки зафиксированы в `docs/research/audit-baseline.json`. Правила работы с репозиторием: `AGENTS.md`; подробности по проверкам: `skills/tdf-country-content/SKILL.md`.
