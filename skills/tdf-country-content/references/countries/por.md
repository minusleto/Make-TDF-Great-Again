# POR — Country style card

**Срез:** 2026-11-24, `main` @ `26a6d8c`. **Основной файл:** [Portugal_Focus_Tree.txt](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Portugal_Focus_Tree.txt). Уверенность высокая для присутствия указанных ID, средняя для редакторской интерпретации; исторические сведения здесь не проверялись.

## Контекст уже имеющегося контента

- **Компании и промышленность:** [POR_navigator_company](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Portugal_Focus_Tree.txt#L196), `POR_portugal_telecom` (строка 759), `POR_altice_portugal` (795) и [POR_made_in_portugal](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Portugal_Focus_Tree.txt#L3408) уже связывают развитие с конкретными корпоративными/производственными сюжетами. Фактическую форму собственности компании всегда проверять отдельно.
- **Экономические ступени и политика:** [POR_fiscal_discipline](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Portugal_Focus_Tree.txt#L3931) открывает отдельный набор последствий; пример не означает, что все экономические фокусы должны повторять его структуру.
- **CPLP и дипломатия:** в дереве есть точки открытия/доступности ветки CPLP (`POR_available_new_branch_cplp` — ключ локализации shortcut, не ID фокуса). Перед добавлением ещё одной общей дипломатической цепочки найти уже существующие обращения и ответы.
- **Союз с Великобританией:** [POR_recall_windsor_treaty](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Portugal_Focus_Tree.txt#L7586) связан с событием `portugal_braganza.14` (см. design-guide).
- **Литий и энергетический переход:** [POR_barroso_lithium](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Portugal_Focus_Tree.txt#L988) — уже использованная ресурсная тема.

## Тон и ограничения

- Сильные тексты могут быть конкретными и цельными, но длина 200–280 знаков и схема «факт → намерение → последствие» — ориентиры общего скилла, не обязательный шаблон Португалии и тем более не закон для других стран.
- CPLP — не универсальная замена двусторонней дипломатии: различать реальные интересы, конкретного партнёра и практический результат соглашения.
- Не называть компанию государственной или частной без источника; наличие компании в фокусе само по себе не устанавливает собственность.
- Экономические ступени должны отражать различимые состояния/последствия, а не просто переименовывать дух без изменения игрового смысла.

## Куда смотреть дальше

Возможные направления для исследования: атлантическая инфраструктура и логистика, морская промышленность, энергосистема и региональные различия. **Это не подтверждённо свободные темы**: сначала проверить весь актуальный контент POR.

**Источники:** [Portugal_Focus_Tree.txt](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Portugal_Focus_Tree.txt), [design-guide.md](../design-guide.md).
