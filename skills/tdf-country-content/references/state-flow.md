---
status: project-reference
updated: 2026-11-25
scope: "Static cross-file analysis of flags, variables, arrays, scripted effects/triggers, on_actions, history and direct decision/event links."
limits: "Evidence candidates only; cannot resolve dynamic scopes, indirect calls, execution order or missing base-MD content and does not simulate HOI4 runtime."
---

# Межфайловые связи и жизненный цикл состояния

Статический справочник и маршрут аудита для tdf_audit.py (JSON-раздел _state_flow). Он дополняет проверки focus, event, decision, idea и MIO/equipment, но не симулирует runtime HOI4.

## Область обхода

Аудитор собирает доступные .txt из mdredux/common/ и mdredux/events/. Для scripted_effects, scripted_triggers и on_actions отдельно читаются .txt и файлы без расширения. Для country history проверяются оба встречающихся пути:

- mdredux/history/countries/;
- mdredux/common/history/countries/.

В текущем checkout country-history файлы находятся во втором пути. Для каждого файла сохраняются тип источника, путь и строка; date blocks содержат список выдаваемых ideas, инициализаций variables и startup event calls.

Отсутствующий каталог — ограничение доступного checkout, а не ошибка. Если on_actions или scripted_triggers отсутствуют, нельзя утверждать, что startup/yearly цепочки или все пользовательские триггеры проверены полностью.

## Flags

Учитываются чтения has_country_flag, has_global_flag, has_state_flag, has_province_flag и записи/снятия соответствующих set_*_flag / clr_*_flag, а также timed flag setters.

Для tag-prefixed IDs аудитор показывает записи без локального читателя и чтения без локального writer, с файлами, строками, командами и типами источника. Это WARN-кандидаты: флаг может читаться или устанавливаться базовым Millennium Dawn, другим модулем, DLC, on_action или скриптом вне checkout. Отсутствие пары в локальном срезе само по себе не доказывает баг.

## Variables и arrays

Для переменных индексируются известные команды записи (set_variable, set_temp_variable, add_to_variable, subtract_from_variable, multiply_variable, divide_variable, clamp_variable, modulo_variable), условия check_variable / compare_variables и статические var: / global_var: expressions.

Для массивов учитываются add_to_array, remove_from_array, clear_array и чтение через any_of_scopes, all_of_scopes, random_scope_in_array, for_each_scope_loop. Поддерживаются обе формы: array = X и X = VALUE.

Неизвестные helper-эффекты, динамически формируемые имена, индексы массивов и переменные, передаваемые через scope, могут потребовать ручного просмотра. Unprefixed symbols не объявляются отсутствующими только потому, что локальный writer не найден.

## Scripted effects, triggers и on_actions

- Definitions индексируются по всем локальным скриптовым файлам .txt и без расширения в соответствующих папках.
- Вызовы существующих definitions находятся по точному имени; дубликаты definitions показываются отдельно.
- Definitions без локального вызова и tag-prefixed TAG_custom_call = yes/no, для которых нет локального определения, являются кандидатами. Вызов может происходить в базовом MD или через отсутствующий скрипт.
- on_actions индексируются как hooks; отсутствие каталога отражается boolean-флагом.

Неизвестный prefixed call не превращается в ERROR. Перед исправлением сверить базовый MD и формат вызова.

## Lifecycle ideas

on_add / on_remove просматриваются на записи flags, variables и arrays. Дополнительно индексируются прямые вызовы country_event / news_event внутри этих lifecycle-блоков: в _branch_connectivity появляется ребро idea → event. Такое событие считается локально достижимым только если в доступном checkout найден хотя бы один локальный add_idea / add_ideas / add_timed_idea для этой идеи. Если grant не найден, ребро остаётся в графе, но само по себе не снимает кандидат unreachable_triggered_event. Для простых пар set/clr, add/remove, add/subtract показывается несопоставленный эффект. Это редакторская проверка, а не требование зеркалить любые эффекты: часть изменений намеренно постоянная, часть завершается timed flag или отдельным событием.

## Scope и ограничения

В JSON сохраняются количества и частоты ROOT, FROM, PREV, THIS. Само наличие scope marker не доказывает, что команда выполняется в правильном scope. Auditor не разрешает target-scope chains, не симулирует runtime, не может доказать вызов из отсутствующего base MD и строит candidate links для прямых записей и положительных gates decision/event, но не доказывает причинно-следственную связь и корректность scope.

Все массивы вида potentially_*, *_without_writer, *_without_local_call, unresolved_* и idea_on_add_without_matching_on_remove читать как WARN / review candidates, а не автоматические ошибки.

## Запуск

\`\`\`bash
python3 -I skills/tdf-country-content/scripts/tdf_audit.py .
python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --json audit.json
python3 -I -m unittest discover -s skills/tdf-country-content/tests -v
\`\`\`

Полная карта связей сохраняется в JSON-ключе _state_flow.

## Прямые связи decision/event → flag/idea

В JSON дополнительно строится `decision_event_state_links`: прямые записи country/global/state/province flags и выдачи ideas из `complete_effect`, `remove_effect`, `timeout_effect`, `cancel_effect`, `immediate` и option effects сопоставляются с положительными условиями в других объектах.

Проверяются gates:
- у decision: `visible`, `available`, `allowed`, `activation`;
- у decision category: `potential`, `allowed`, `visible`;
- у event: `trigger`;
- у option события: `trigger`, отдельно от event trigger.

Flag links сопоставляют точный ID и отдельно отмечают совместимость setter/getter scope (country/global/state/province). Timed flag setters сравниваются с соответствующим обычным getter scope. Idea links связывают `add_ideas`, `add_idea` и `add_timed_idea` с `has_idea` / `has_ideas`. Проверки внутри `NOT` и `NOR` не трактуются как положительное условие разблокировки. Совпадения внутри того же event ID исключаются, чтобы не считать внутренний цикл межобъектной связью.

Это evidence-кандидаты, а не доказательство корректной цепочки: статический анализ не подтверждает порядок выполнения, совпадение фактического country scope/получателя, отсутствие снятия флага/духа между объектами или влияние scripted effects, которых нет в прямом блоке. Он также не разрешает динамические ID и scope chains, а базовый MD в checkout отсутствует. Поэтому результаты не повышают уровень ERROR и требуют ручной проверки.

## Связность целых веток — JSON _branch_connectivity

Дополнительный отчёт собирает существующие локальные ссылки в единый граф:
- focus → prerequisite focus (игровая зависимость; отдельно хранится relative_position_id, это только layout);
- focus → event → event;
- focus/event → выдаваемые идеи и технику;
- idea on_add/on_remove → event, с проверкой наличия локального grant идеи;
- focus → idea gate (available/bypass) и источники выдачи идеи по цепочке prerequisite ancestors → called events;
- idea → custom_modifier_tooltip → scripted localisation → idea conditions;
- focus → MIO и MIO → focus из visible;
- прямые event/decision state handoffs, найденные state-flow анализом.

focus_idea_gate_paths — review candidate, если локально определённая идея используется как gate, но среди prerequisite ancestors и событий, вызванных ими, не найден локальный grant. Возможны стартовая выдача через history, decision, on_action, scripted effect или базовый MD; отчёт перечисляет известные локальные writers и не считает отсутствие доказательства доказательством ошибки.

unresolved_local_event_calls, external_event_calls, tooltip_script_resolution, unreachable_triggered_events и ссылки MIO показываются как отдельные типы кандидатов. Внешние namespace не превращаются в локальный missing ID. Ни один новый candidate не повышает exit code: существующие точные ERROR/WARN правила остаются источником статуса. В JSON данные расположены в _branch_connectivity, краткая статистика выводится при запуске, подробные кандидаты — через --details TAG.

**Ограничения:** prerequisite ancestry — консервативное объединение ID, а не полная симуляция AND/OR, войны, DLC, динамических scope, вероятностей AI или порядка исполнения. Наличие локального пути доказывает только статическую связь вызовов, не успешное выполнение эффекта в игре. Отсутствие локального writer может означать базовый MD/историю/скрипт, которого нет в checkout. Для idea lifecycle локальная выдача лишь подтверждает статическую возможность включения on_add/on_remove в локальную цепочку; она не подтверждает фактическую дату выдачи, снятие духа или выполнение в runtime. Использовать граф для навигации и ручного ревью, не для автоматического вывода о runtime-reachability.

