# Локализация фокусов: эталон - Португалия

Португалия выбрана эталоном по описаниям фокусов: из десяти деревьев она лучше всех держит единый стиль на всём дереве (303 описания). Эталон относится к тексту, а не к коду: в коде Португалии тоже есть баги (11 фокусов с чужим `log`, несколько наград только внутри `effect_tooltip`).

## 1. Измеренный эталон (английская локализация фокусов)

| Страна | Описаний | Медиана знаков | В 200-280 | В 150-340 | Медиана предложений | Есть "we/our/us" | Явное намерение ("we will", "we must"...) | Есть конкретика (имя, число) | Запретные слова |
|---|---|---|---|---|---|---|---|---|---|
| **POR** | 304 | **257** | 53% | **92%** | **3** | 81% | **65%** | **85%** | 9% |
| SYR | 489 | 194 | 28% | 64% | 2 | 76% | 58% | 73% | 6% |
| SOV | 987 | 165 | 22% | 56% | 2 | 58% | 37% | 74% | 9% |
| KAZ | 375 | 187 | 22% | 64% | 2 | 38% | 26% | 66% | 5% |
| POL | 647 | 168 | 23% | 65% | 1 | 6% | 3% | 78% | 11% |
| HUN | 335 | 173 | 29% | 62% | 2 | 47% | 25% | 66% | 14% |
| ARM | 498 | 136 | 13% | 35% | 1 | 78% | 60% | 70% | 3% |
| BLR | 360 | 127 | 12% | 32% | 1 | 57% | 32% | 61% | 1% |
| ISR | 703 | 115 | 8% | 25% | 1 | 77% | 61% | 68% | 3% |
| SLO | 183 | 102 | 9% | 15% | 1 | 17% | 13% | 63% | 3% |

Выводы: целевая длина 200-280 знаков, жёсткие границы 150-340; 2-4 предложения; почти всегда "мы" и явное намерение; почти всегда конкретика. Польша пишет без "мы" (6%) и без намерения (3%): шаблонные зачины "A policy...", "A foreign...", "A comprehensive..." - так не писать. Израиль, Армения, Беларусь и Словакия слишком коротки: медиана - одно предложение.

Меры сделаны по ключам вида `ID_desc` (скрипт `scripts/tdf_audit.py` считает длины и запретные слова по тем же ключам). Цифры - ориентиры.

## 2. Формула описания

1. **Факт или проблема** (1-2 предложения): реальное имя, договор, компания, число, место. Дата только как вечный факт прошлого ("In 1602", "the 1386 Windsor Treaty"), без привязки к дате прохождения.
2. **"We will ..."** (что делает именно ЭТОТ фокус). Намерение должно совпадать с наградой.
3. **Короткое последствие** (до одного предложения): цена или побочный эффект, если он есть в награде. Сухая ирония допустима, только если ирония есть в самом факте.

Идеологические ветки пишутся голосом партии (коммунисты, Chega): от первого лица, с эмоцией, но с тем же скелетом.

## 3. Эталонные примеры (Португалия, награды сверены с кодом)

`POR_recall_windsor_treaty` [191 знак]
> The oldest alliance in the world must be renewed. We will reach out to our British cousins, invoking the spirit of the 1386 Windsor Treaty, to forge a new bond between the two ancient crowns.

Награда: событие-предложение Англии, гарантии и военный доступ. Текст объясняет, что делает фокус, и не называет цифр.

`POR_fiscal_discipline` [259]
> Decades of deficit spending have left Portugal vulnerable. We will impose fiscal discipline: curb excessive spending, reduce public debt, and meet our European commitments. A necessary course - even when it tests our traditional allies in the labour movement.

Награда: дух дисциплины, минус к популярности партии, `change_labour_unions_opinion` -2. Последнее предложение - честное описание цены.

`POR_modern_army` [240]
> The 'New Organic Structure' ends years of chronic underfunding. Committing to NATO's 2% GDP target, we increase military spending and reorganise our forces to meet modern strategic challenges with proper financing and modernised structures.

Награда: снимается `POR_chronic_underfunding_idea`, улучшается дух профессиональной армии, добавляется черта лидера. Текст называет реальную проблему и реальную реформу.

`POR_avenge_1602` [201]
> In 1602, the Persians stole Bahrain from us. The insult remains. Now, with our power restored, we will settle the ancient score. The Persian Gulf will once again know the power of the Portuguese crown.

Награда: casus belli на Персию и временный дух. Короткий и в характере ветки.

## 4. Слабые места самой Португалии

`POR_air_force_desc` [225] - энциклопедия без намерения и без связи с наградой:
> Formally established in 1952, the Portuguese Air Force unified earlier Army and Navy aviation. As a NATO key player, it guards the Atlantic approaches. With proud Asas squadrons, the FAP is a compact but highly capable force.

Награда: `air_experience = 20`, скидка на доктрину (2 использования), +3 к мнению военных. Переписанный вариант, который объясняет реальную награду [264 знака]:
> The Força Aérea Portuguesa has flown as a single service since 1952 - a small force that polices the Atlantic approaches for NATO. We will put more hours in its pilots' logbooks and bring its doctrine up to date, so the Asas squadrons can punch above their weight.

Прочее: слово `ensuring` в 12 описаниях, `key` в 5, `comprehensive` в 4 - заменить конкретным глаголом.

## 5. Заголовки

2-4 слова, до 30 знаков (88% заголовков Португалии укладываются). Глагол + объект ("Recall the Windsor Treaty") или название вещи ("Zenit Shipyard"). Криптичные и анахроничные названия заменять. Соседние описания не должны начинаться одинаково: у Португалии самый частый зачин "We will" встречается лишь 10 раз на 303 описания, у Польши "A policy" - 14 раз.

## 6. Правила, перенесённые из MD-скила

- Перед описанием посмотреть точный `completion_reward` и всё, что он выдаёт (идеи, события). Не описывать ангары, полосы, системы подготовки и другие награды, которых нет.
- Не называть технику или проекты, которые выдают более поздние фокусы (никаких спойлеров).
- Не хардкодить столицу и прилагательное страны: они меняются. В русской локализации токены `[X.GetAdjective]` ломаются после предлогов и притяжательных - использовать токены только как подлежащее.
- Запретные слова и клише: `strengthen ties`, `mutual benefit`, `significant`, `foothold`, `valuable`, `comprehensive`, `ensuring`, `key`, `foster`, `paving the way`.
- Факт без источника не писать: отделять подтверждённую историю от намерения игрока и альтернативной истории.

## 7. Формат yml

UTF-8 с BOM, заголовок `l_english:` без отступа, ключи с одним пробелом отступа (` key: "text"`), `\"` для кавычек, `\n` для переноса, без номера версии, без дублей. Ключи: фокус `<id>`, описание `<id>_desc`, событие `<ns>.<n>.t/.d/.a/.b`, дух `<id>`, `<id>_desc`, подсказка `<что>_tt`, scripted loc `X_loc` с ключами `X_loc1..`. Окончания строк CRLF не менять; править точечно по ключам, а не пересобирать файл целиком.
