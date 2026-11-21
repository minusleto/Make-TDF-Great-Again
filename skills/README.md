# Скилы TDF / MDC

Как выбрать. Если коротко: читай `tdf-country-content`, остальное по ссылкам из него.

| Задача | Скил | Начать с |
|---|---|---|
| Писать или ревьюить фокусы, нацдухи, события, локализацию страны; вопросы "как устроена страна", "что должен давать фокус" | `tdf-country-content` | `tdf-country-content/SKILL.md` |
| Рабочий цикл по одному фокусу, числа баланса, примеры кода, дипломатические цепочки, уроки по Казахстану | `md-hoi4-country-content` | `md-hoi4-country-content/SKILL.md` |
| Создавать, проверять и чинить `defined_text`, динамические tooltip и scripted localization | `hoi4-scripted-localisation` | `hoi4-scripted-localisation/SKILL.md` |

Приоритет: при противоречии `tdf-country-content` главнее (он новее и измерен по десяти деревьям). Для вопросов о синтаксисе и ключах scripted localization дополнительно читать профильный скил.

## Быстрый старт для агента
1. Прочитать `tdf-country-content/SKILL.md` и `tdf-country-content/references/design-guide.md` (философия: фокус даёт инструмент; что кодить, зачем и как; шаблоны веток).
2. Справочники лежат в `tdf-country-content/references/`: геймдизайн - `design-guide.md`; текст фокуса - `focus-loc.md`; события - `event-loc.md`; духи - `national-spirits.md`; ветка и код - `focus-design.md`; числа и ошибки - `balance-and-pitfalls.md`; что входит в страну - `country-structure.md`.
3. При работе с `defined_text`, динамическими tooltip или scripted localization читать также `hoi4-scripted-localisation/SKILL.md`.
4. После правок: `python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --tags TAG --details TAG` (из корня репозитория). Ошибок (ERROR-проверок) не должно прибавиться.
5. Не утверждать, что мод запускали; репозиторий - только срез без базового мода.

## Где что
- `tdf-country-content/` - SKILL.md, `references/` (7 файлов), `scripts/tdf_audit.py`
- `md-hoi4-country-content/` - SKILL.md, `references/` (4 файла), `scripts/mdindex.py` (нужен только вне репозитория)
- `hoi4-scripted-localisation/` - SKILL.md; правила для scripted localization и modifier localization keys
- `../docs/research/` - аудиты; главный `2026-10-tdf-trees-audit.md`
- `../md-hoi4-country-content.skill` - старый zip-пакет, не обновляется
