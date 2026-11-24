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

on_add / on_remove просматриваются на записи flags, variables и arrays. Для простых пар set/clr, add/remove, add/subtract показывается несопоставленный эффект. Это редакторская проверка, а не требование зеркалить любые эффекты: часть изменений намеренно постоянная, часть завершается timed flag или отдельным событием.

## Scope и ограничения

В JSON сохраняются количества и частоты ROOT, FROM, PREV, THIS. Само наличие scope marker не доказывает, что команда выполняется в правильном scope. Auditor не разрешает target-scope chains, не симулирует runtime, не может доказать вызов из отсутствующего base MD и не проверяет семантическую связь «decision/event открылся флагом, а затем прочитал тот же ID».

Все массивы вида potentially_*, *_without_writer, *_without_local_call, unresolved_* и idea_on_add_without_matching_on_remove читать как WARN / review candidates, а не автоматические ошибки.

## Запуск

\`\`\`bash
python3 -I skills/tdf-country-content/scripts/tdf_audit.py .
python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --json audit.json
python3 -I -m unittest discover -s skills/tdf-country-content/tests -v
\`\`\`

Полная карта связей сохраняется в JSON-ключе _state_flow.
