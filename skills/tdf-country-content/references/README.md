---
status: source-of-truth-map
updated: 2026-11-25
scope: Canonical authority map for TDF/MDC skill rules, references, audit severity and verification boundaries.
limits: This is a routing and authority index, not a replacement for domain references or a guarantee of HOI4 runtime behaviour.
---

# TDF/MDC reference map — source of truth

Этот файл — единственная подробная карта доменных правил. В нём указано, какой документ является основным источником по теме, каков статус его положений и где проходят границы проверки. Общий SKILL и AGENTS должны маршрутизировать к этим источникам, а не переписывать их содержание.

## Как разрешать противоречия

1. Актуальная явная инструкция пользователя и решения команды для текущей задачи.
2. Критические правила репозитория из AGENTS.md и обязательный рабочий контракт из skills/tdf-country-content/SKILL.md.
3. Основной доменный reference из таблицы ниже.
4. Country style cards и country-specific maintenance — только контекст для указанной страны.
5. Исторические research notes, статистика и примеры — наблюдения на дату снимка, не более поздний источник истины.

Фактический код в текущем checkout, актуальная wiki и целевая версия HOI4/MD важнее устаревшего примера. Если source отсутствует или не подтверждён, помечай его как неизвестный, а не заполняй предположением.

## Типы положений

- **[REQUIRED]** — техническое требование, подтверждённое целевой спецификацией, или явно принятое командой соглашение проекта. Проектное соглашение не следует выдавать за ограничение движка.
- **[RECOMMENDED]** — рекомендация дизайна/редактуры; допускает обоснованные исключения.
- **[OBSERVATION]** — статистика, частота или пример из конкретного среза; не задаёт целевую норму.
- **[UNVERIFIED]** — гипотеза или внешний ID, для которого недостаточно доказательств.

В references должны быть ясно различимы эти категории. Числовые ориентиры, частые слова, generic подписи и stylistic patterns сами по себе не создают ERROR. Новые автоматические проверки обязаны иметь unit test и fixture допустимого/внешнего случая.

## Единственные основные источники по доменам

| Область | Единственный основной источник | Статус и границы |
|---|---|---|
| Общий порядок работы и обязательный цикл | [Основной SKILL](../SKILL.md) | Краткий контракт и маршрутизатор; подробные правила не дублируются здесь |
| Критические правила репозитория и проверка перед записью | [AGENTS.md](../../../AGENTS.md) | Только repo workflow и ограничения; не дизайн-справочник |
| Физический формат .txt и localisation YML | [file-formatting.md](file-formatting.md) | [REQUIRED] Принятые соглашения TDF о форматировании; не описание семантики эффектов |
| Проектирование страны и выбор focus/decision/event/idea | [design-guide.md](design-guide.md) | [RECOMMENDED] Позиция команды и проверенные примеры, не спецификация движка |
| Focus tree, focus blocks, prerequisites, gates, bypass | [focus-design.md](focus-design.md) | [REQUIRED] Структура и проектные соглашения; примеры legacy могут требовать перепроверки |
| Focus title/description, ключи и динамические имена | [focus-loc.md](focus-loc.md) | [RECOMMENDED] Редактура; общая договорённость GetCapital помечена отдельно как [REQUIRED] |
| Events, options, chains, event localisation | [event-loc.md](event-loc.md) | [RECOMMENDED] Редакторские советы и статические QA-правила; generic labels не запрещены |
| Decision categories и decisions | [decision-design.md](decision-design.md) | [REQUIRED] Семантика полей/локальных связей; баланс и optional fields требуют контекста |
| Ideas / national spirits и lifecycle | [national-spirits.md](national-spirits.md) | Проектный reference; численные сравнения — исторические наблюдения |
| Составные hidden-idea hubs | [Nested national spirits skill](../../hoi4-nested-national-spirits/SKILL.md) | Специализированный pattern; не загружать для обычного духа |
| MIO, equipment, modules, technologies и variants | [mio-and-equipment.md](mio-and-equipment.md) | Статический QA; missing definitions остаются unknown до проверки точного TDF-файла |
| Межфайловые flags, variables, arrays, scripts, history и связность focus/event/idea/MIO-цепочек | [state-flow.md](state-flow.md) | Статический typed evidence graph _state_flow + _branch_connectivity; candidates не доказывают runtime-reachability |
| Балансные предупреждения и общий checklist | [balance-and-pitfalls.md](balance-and-pitfalls.md) | [RECOMMENDED] Никаких универсальных числовых лимитов |
| Файловая структура страны и общие системы | [country-structure.md](country-structure.md) | Частично исторический обзор; подробные измерения — срез 2026-10-30 |
| Дополнительные соглашения Казахстана | [kazakhstan-maintenance.md](kazakhstan-maintenance.md) | Country-specific; не переносить на остальные страны |
| Текущие темы и примеры одной страны | [Country style cards](countries/README.md) | Контекстные, неполные references; загружать только карточку нужного тега |
| Неразрешённые внешние ID и зависимости TDF | [Реестр зависимостей](../../../docs/research/external-dependencies.md) + [JSON](../../../docs/research/external-dependencies.json) | `confirmed` допускается только по точному TDF-файлу или файлу целевой сборки, предоставленному пользователем |
| Воспроизводимый подсчёт файлов и блоков | [tdf_inventory.py](../scripts/tdf_inventory.py) + [inventory report](../../../docs/research/2026-11-24-tdf-inventory.md) | Скрипт — способ пересчёта; Markdown report — снимок на 2026-11-24 |

## Аудитор: границы ERROR / WARN / INFO

Текущая классификация зафиксирована в tdf_audit.py (ERRORS, WARNS, INFOS). Изменять её можно только вместе с тестами:

- **ERROR:** parser failures, duplicate IDs/keys, mismatched log IDs, missing required localisation/known local references, unresolved event IDs in a locally declared namespace и другие доказуемые структурные дефекты.
- **WARN:** title_gt30, desc_lt150, desc_gt340, banned_phrase, event_generic_label, event_label_gt35, external/unresolved candidates, possible unused state. Все требуют контекста; ни один не является доказанной stylistic error.
- **INFO:** event_without_picture. Картинка желательна, но не обязательна.
- Внешние зависимости с unknown/unregistered status остаются review candidates, не ERROR только из-за отсутствия в checkout.

## Tests и допустимые исключения

skills/tdf-country-content/tests/ — регрессионная база auditor и inventory. При добавлении новой проверки добавить unit test и fixture, включая валидный/внешний случай. Уже предусмотрены fixture-примеры:
- неизвестные namespace/ID и shared cross-country MIO не должны автоматически становиться missing-local ERROR;
- extensionless scripted effects и country history участвуют в карте связей;
- generic event option label отражается как редакторский кандидат, а не запрещённая строка;
- branch-connectivity fixture связывает focus → event → idea → tooltip/scripted localisation → следующую focus gate, а также отделяет внешний event namespace и незамкнутый local chain как review candidates;
- отсутствие picture — INFO, не обязательный структурный дефект;
- отключённые ветки и допустимые внешние ссылки отделяются от активных локальных ошибок.

Запуск полного набора: `python3 -I -m unittest discover -s skills/tdf-country-content/tests -v`.

Автоматический CI настроен в `.github/workflows/tdf-audit-validation.yml` (GitHub Actions). Workflow запускается при изменениях в `mdredux/**`, `skills/tdf-country-content/**`, реестре внешних зависимостей и самом workflow; также доступен через `workflow_dispatch`. Он выполняет unit-тесты, полный статический аудит, отдельные проверки всех 12 стран и структурную инвентаризацию. JSON-отчёты и журналы загружаются как artifacts на 14 дней.

**Статус CI отделён от статуса содержимого.** Exit code `1` означает, что аудитор завершился штатно и нашёл контентные ERROR-кандидаты: workflow сохраняет сырой код в `exit-code.txt`, публикует findings в log/JSON и завершает audit job успешно (зелёный статус означает, что проверка отработала и отчёт сохранён, а не что контент чистый). Exit code `2` и другие ненулевые коды означают ошибку входных данных/выполнения и по-прежнему проваливают job. Неуспешные unit tests или inventory также проваливают workflow. Для решения о готовности контента изучай JSON-артефакты, а не только цвет check.

Ни workflow, ни unit-тесты не заменяют проверку HOI4 runtime.
