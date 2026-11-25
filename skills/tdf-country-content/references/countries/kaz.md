---
status: contextual-country-reference
country: KAZ
scope: "Selected themes and examples already present in the local KAZ country content."
limits: "Not exhaustive; technical notes and historical claims require current-code and external verification; re-scan before assuming a theme is absent."
---

# KAZ — Country style card

**Срез:** 2026-11-24, `main` @ `26a6d8c`. **Основной файл:** [Kazakhstan_Focus_Tree.txt](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Kazakhstan_Focus_Tree.txt). Уверенность высокая для наличия ID и связей в дереве; средняя для редакторской интерпретации. Исторические утверждения не подтверждались внешним фактчекингом.

## Контекст уже имеющегося контента

- **Национальное строительство и память об Алаше:** маршрут начинается с [KAZ_return_alash](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Kazakhstan_Focus_Tree.txt#L7019). Не представлять его как универсальную замену современной политике или как однозначную историческую трактовку.
- **Ресурсная и промышленная экономика:** в дереве уже есть урановые направления `KAZ_korea_uran`, `KAZ_west_uran`, `KAZ_east_uran`, а также [KAZ_kashagan](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Kazakhstan_Focus_Tree.txt#L258), [KAZ_tengiz](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Kazakhstan_Focus_Tree.txt#L370) и промышленный контекст `KAZ_ABP` (строка 68).
- **Каспий и внешняя политика:** [KAZ_kaspiy](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Kazakhstan_Focus_Tree.txt#L304), [KAZ_sparks_over_caspian](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Kazakhstan_Focus_Tree.txt#L2771) и [KAZ_caspian_union_state](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Kazakhstan_Focus_Tree.txt#L3400) уже используют Каспий как самостоятельную тему.
- **Армейская модернизация:** [KAZ_reorganization_infantry](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Kazakhstan_Focus_Tree.txt#L3484) — пример отдельной военной линии, которую нельзя сводить к одному общему бонусу армии.

## Тон и ограничения

- Многовекторность показывать конкретными интересами, инфраструктурой, ресурсами и соглашениями; не писать абстрактное «дружим со всеми».
- Не сводить экономику к нефти: в уже имеющемся контенте есть уран, промышленность, транспорт и отдельные компании. Новая ресурсная тема должна отличаться от простого расширения добычи.
- Военный контент должен учитывать, что именно закупается или производится, реальные категории техники и местные производственные возможности. Для технических деталей читать [kazakhstan-maintenance.md](../kazakhstan-maintenance.md), а не дублировать его в карточке.
- Динамическую столицу не зашивать в тексты: соблюдать правило `GetCapital` из общего скилла.

## Куда смотреть дальше

Возможные направления для исследования: вода и ирригация, логистические узлы за пределами уже отмеченных нефтегазовых проектов, переработка сырья и цепочки добавленной стоимости, управление Каспийской экологией. **Не считать их свободными слотами**: проверить весь focus tree, decisions, events, ideas и MIO перед планированием.

**Техническая точка внимания:** внешние и неразрешённые ID сверять с [реестром зависимостей](../../../../docs/research/external-dependencies.md).

**Источники:** [Kazakhstan_Focus_Tree.txt](https://github.com/minusleto/Make-TDF-Great-Again/blob/26a6d8ca1f21fdaabbe7ca1c9294401727c1c165/mdredux/common/national_focus/Kazakhstan_Focus_Tree.txt), [Kazakhstan maintenance](../kazakhstan-maintenance.md), [current inventory](../../../../docs/research/2026-11-24-tdf-inventory.md).
