# Скилы TDF / MDC

Как выбрать. Если коротко: читай `tdf-country-content`, остальное по ссылкам из него.

| Задача | Скил | Начать с |
|---|---|---|
| Писать или ревьюить фокусы, нацдухи, события, локализацию страны; вопросы "как устроена страна", "что должен давать фокус" | `tdf-country-content` | `tdf-country-content/SKILL.md` |
| Рабочий цикл по одному фокусу, числа баланса, примеры кода, дипломатические цепочки, уроки по Казахстану | `md-hoi4-country-content` | `md-hoi4-country-content/SKILL.md` |

Приоритет: при противоречии `tdf-country-content` главнее (он новее и измерен по десяти деревьям).

## Быстрый старт для агента
1. Прочитать `tdf-country-content/SKILL.md` (философия: фокус даёт инструмент, 6 шагов цикла).
2. Справочники лежат в `tdf-country-content/references/`: текст фокуса - `focus-loc.md`; события - `event-loc.md`; духи - `national-spirits.md`; ветка и код - `focus-design.md`; числа и ошибки - `balance-and-pitfalls.md`; что входит в страну - `country-structure.md`.
3. После правок: `python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --tags TAG --details TAG` (из корня репозитория). Ошибок (ERROR-проверок) не должно прибавиться.
4. Не утверждать, что мод запускали; репозиторий - только срез без базового мода.

## Где что
- `tdf-country-content/` - SKILL.md, `references/` (6 файлов), `scripts/tdf_audit.py`
- `md-hoi4-country-content/` - SKILL.md, `references/` (4 файла), `scripts/mdindex.py` (нужен только вне репозитория)
- `../docs/research/` - аудиты; главный `2026-10-tdf-trees-audit.md`
- `../md-hoi4-country-content.skill` - старый zip-пакет, не обновляется
