# External dependency registry

Единый реестр внешних зависимостей TDF/MDC. Машиночитаемый источник истины — `external-dependencies.json`; auditor читает его и публикует найденные ссылки в JSON-разделе `_external_dependencies`.

## Датированный upstream baseline

На **2026-11-24** проверен официальный репозиторий [MillenniumDawn/Millennium-Dawn](https://github.com/MillenniumDawn/Millennium-Dawn), branch `main`, commit [`04b2ba126fc1`](https://github.com/MillenniumDawn/Millennium-Dawn/commit/04b2ba126fc1057bf2ab4bac0407b3235983994c). Descriptor `Millennium_Dawn.mod` в этом snapshot указывает mod version **2.0.0** и `supported_version = "1.19.*"`; commit date — `2026-11-24T15:41:46Z`.

Это справочный снимок, а не обещание совместимости TDF с этой версией Millennium Dawn. При реальной проверке ориентируйся на установленный base MD, версию HOI4, DLC и порядок загрузки модов.

## Статусы

- `confirmed` — точное определение или English localisation key найден в указанном upstream commit либо точное shared definition включено в сам TDF checkout. Для event ID это подтверждает только существование определения; наличие его локализационных ключей и runtime-цепочку фиксируй отдельно.
- `assumption` — найдено использование в upstream, но определяющий блок не проверен независимо.
- `unknown` — не подтверждено. Не объявлять ID существующим или отсутствующим.

## Что собирает auditor

JSON-ключ `_external_dependencies` сопоставляет unresolved candidates из:
- external event namespaces / event calls;
- external event и decision localisation;
- external ideas, включая unprefixed shared IDs;
- scripted effect / trigger candidates;
- MIO references и MIO name localisation;
- equipment types, modules и `has_tech` technology IDs.

Для каждого совпадения выводятся тип, ID, статус, источник, проверка, notes и конкретные места использования. Точные ID, которых нет в JSON-реестре, получают `status = unknown` и `registry_status = unregistered`. Реестр не является allowlist: он не скрывает ссылки и не меняет ERROR/WARN.

Shared TDF definitions тоже могут быть приведены как положительные примеры. Например, `USA_lockheed_martin_aircraft_manufacturer` используется Польшей и Великобританией, но его MIO definition присутствует в TDF checkout — это не missing external MIO.

## Verified base-MD scripted effects

The pinned upstream baseline also defines the two financial effects used by the Aral Sea mechanic:

| Effect | Definition in pinned baseline | Contract |
|---|---|---|
| `modify_treasury_effect` | [`common/scripted_effects/00_budget_effects.txt:1643`](https://github.com/MillenniumDawn/Millennium-Dawn/blob/04b2ba126fc1057bf2ab4bac0407b3235983994c/common/scripted_effects/00_budget_effects.txt#L1643) | Adds `treasury_change` to `treasury`; the charge is skipped only when `MD_skip_treasury_cost` is set. |
| `modify_debt_effect` | [`common/scripted_effects/00_budget_effects.txt:1656`](https://github.com/MillenniumDawn/Millennium-Dawn/blob/04b2ba126fc1057bf2ab4bac0407b3235983994c/common/scripted_effects/00_budget_effects.txt#L1656) | Adds `debt_change` to `debt`, clamps the result to a minimum of zero and refreshes the money UI. |

Both exact definitions are registered as `type = scripted_effect`, `status = confirmed` in `external-dependencies.json`. This confirms their presence and parameter contract in the pinned upstream snapshot, not runtime behavior in every target MD version or load order.

## Поддержка реестра

Для event title/desc/option keys действует аналогичный exact-match fallback: ключ снимается с `missing_localisation` или `missing_option_localisation` только если реестр содержит `type = localisation`, `status = confirmed` и TDF `where_used` указывает на `mdredux/events/`. Подтверждённая focus localisation не может фильтровать event key, и наоборот. Наличие upstream ключа не подтверждает runtime загрузку или смысловую пригодность строки.

Подтверждённые focus title/desc keys учитываются по тому же точному правилу, но только когда `where_used` указывает на TDF `common/national_focus/`. Совпадение с event/MIO localisation или ключ со статусом `unknown`/`assumption` не снимает `title_missing` или `desc_missing`. Это подтверждает наличие ключа в базовом MD, а не пригодность текста или фактическую загрузку baseline.

Реестр также учитывает event ID, на которые ссылается локально объявленный namespace, но точное определение которых находится в pinned base MD. Только точное совпадение `type = event` + `status = confirmed` переводит такой вызов из `unresolved_references` в `confirmed_external_references`; `unknown`, `assumption` и незарегистрированные ID остаются unresolved. Подтверждение определения не подтверждает title/desc/option localisation, scope, получателя или runtime-достижимость.

1. Для `confirmed` открывай defining file, а не просто usage, и сохраняй permalink с commit SHA и строкой. Если определение уже bundled в TDF, фиксируй его как локальную shared dependency.
2. Для `assumption` сохраняй место использования и прямо отмечай, что definition не проверена.
3. Для `unknown` перечисляй call sites и ожидаемый источник как гипотезу.
4. При обновлении MD повторно сверяй descriptor, commit SHA, дату и меняющиеся IDs.
5. Не повышай unregistered / missing-local candidates до ERROR только из-за отсутствующего файла в checkout.

## Ограничения

TDF checkout не содержит полный base MD, vanilla и DLC. Поиск на GitHub и локальный статический индекс не доказывают runtime-существование ID во всех версиях. Auditor не разрешает все динамические scopes, непрямые scripted calls и mod load order; unknown остаётся неизвестным до проверки целевой сборки и error log.
