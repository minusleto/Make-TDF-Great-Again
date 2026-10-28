---
title: Регионы и провинции
description: "Триггеры принадлежности к историческим/географическим регионам, континентам, группам стран и Арктике"
---

## Именованные регионы (85 штук)

Для каждого из 85 исторических/географических регионов заведена пара триггеров:

- **`is_X_state`** — проверяется в скоупе состояния (провинции): принадлежит ли эта провинция региону X. Реализовано как `OR` по конкретным ID состояний.
- **`is_X_state_owned`** — проверяется в скоупе страны: владеет ли страна **вообще всеми** провинциями региона X. Реализовано как `AND` по `owns_state = ID`.


**Северная Америка**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Североамериканский союз (США+Канада+Мексика) | `is_north_american_union_state` | `is_north_american_union_state_owned` |
| США | `is_usa_state` | `is_usa_state_owned` |
| Канада | `is_canada_state` | `is_canada_state_owned` |
| Мексика | `is_mexico_state` | `is_mexico_state_owned` |

**СНГ / бывший СССР**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Советский Союз (весь бывший СССР) | `is_soviet_union_state` | `is_soviet_union_state_owned` |
| Россия | `is_russia_state` | `is_russia_state_owned` |
| Украина | `is_ukraine_state` | `is_ukraine_state_owned` |
| Беларусь | `is_belarus_state` | `is_belarus_state_owned` |
| Прибалтика | `is_baltic_state` | `is_baltic_state_owned` |
| Казахстан | `is_kazakhstan_state` | `is_kazakhstan_state_owned` |
| Средняя Азия | `is_center_asia_state` | `is_center_asia_state_owned` |
| Кавказ | `is_caucasus_state` | `is_caucasus_state_owned` |
| Молдова | `is_moldova_state` | `is_moldova_state_owned` |

**Восточная Азия**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| континентальный Китай | `is_mainland_china_state` | `is_mainland_china_state_owned` |
| Большой Китай (материк+Тайвань+Гонконг и т.д.) | `is_greater_china_state` | `is_greater_china_state_owned` |
| Тайвань | `is_taiwan_area_state` | `is_taiwan_area_state_owned` |
| малые острова Южно-Китайского моря | `is_south_china_sea_minor_state` | `is_south_china_sea_minor_state_owned` |
| Внешняя Монголия | `is_outer_mongolia_state` | `is_outer_mongolia_state_owned` |
| Внешняя Маньчжурия | `is_outer_manchuria_state` | `is_outer_manchuria_state_owned` |
| Бурятия | `is_buryatia_state` | `is_buryatia_state_owned` |
| Урянхай (Тыва) | `is_uriankhai_state` | `is_uriankhai_state_owned` |
| Внешний Синьцзян | `is_outer_xinjiang_state` | `is_outer_xinjiang_state_owned` |

**Океания**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Австралазия (Австралия+Новая Зеландия) | `is_australasia_state` | `is_australasia_state_owned` |
| Австралия | `is_australia_state` | `is_australia_state_owned` |
| Новая Зеландия | `is_newzealand_state` | `is_newzealand_state_owned` |

**Британские острова и CANZUK**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Великобритания | `is_uk_state` | `is_uk_state_owned` |
| остров Великобритания (без Сев. Ирландии) | `is_great_britain_state` | `is_great_britain_state_owned` |
| CANZUK (Канада+Австралия+НЗ+Великобритания) | `is_canzuk_state` | `is_canzuk_state_owned` |

**Южная Америка**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Союз южноамериканских наций | `is_union_of_south_american_state` | `is_union_of_south_american_state_owned` |
| Бразилия | `is_brazil_state` | `is_brazil_state_owned` |
| Бразильская Амазония | `is_brazilian_amazon_state` | `is_brazilian_amazon_state_owned` |
| Аргентина | `is_argentina_state` | `is_argentina_state_owned` |
| Чили | `is_chile_state` | `is_chile_state_owned` |
| Перу | `is_peru_state` | `is_peru_state_owned` |
| Колумбия | `is_colombia_state` | `is_colombia_state_owned` |
| Венесуэла | `is_venezuela_state` | `is_venezuela_state_owned` |
| Боливия | `is_bolivia_state` | `is_bolivia_state_owned` |
| Эквадор | `is_ecuador_state` | `is_ecuador_state_owned` |
| Югославия | `is_yugoslavia_state` | `is_yugoslavia_state_owned` |

**Центральная Америка**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Соединённые провинции Центральной Америки | `is_united_provinces_of_central_america_state` | `is_united_provinces_of_central_america_state_owned` |

**Западная Европа**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Франция | `is_france_state` | `is_france_state_owned` |
| Германия | `is_germany_state` | `is_germany_state_owned` |
| Германия + Австрия (аншлюс) | `is_germany_anschluss_state` | `is_germany_anschluss_state_owned` |
| Италия | `is_italy_state` | `is_italy_state_owned` |
| Испания | `is_spain_state` | `is_spain_state_owned` |
| Португалия | `is_portugal_state` | `is_portugal_state_owned` |
| Пиренейский п-ов (Испания+Португалия) | `is_iberian_state` | `is_iberian_state_owned` |
| Бенилюкс | `is_benelux_state` | `is_benelux_state_owned` |
| Польша | `is_poland_state` | `is_poland_state_owned` |
| Румыния | `is_romania_state` | `is_romania_state_owned` |

**Восточная Европа**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Великая Румыния (с Молдовой и др.) | `is_great_romania_state` | `is_great_romania_state_owned` |
| Швейцария | `is_switzerland_state` | `is_switzerland_state_owned` |
| Кальмарская уния (Дания+Швеция+Норвегия) | `is_kalmar_union_state` | `is_kalmar_union_state_owned` |

**Северная Европа**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Дания | `is_denmark_state` | `is_denmark_state_owned` |
| Швеция | `is_sweden_state` | `is_sweden_state_owned` |
| Норвегия | `is_norway_state` | `is_norway_state_owned` |
| Финляндия | `is_finland_state` | `is_finland_state_owned` |
| Великий Индостан | `is_great_hindustan_state` | `is_great_hindustan_state_owned` |

**Южная Азия**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Индия | `is_indian_state` | `is_indian_state_owned` |
| Пакистан | `is_pakistan_state` | `is_pakistan_state_owned` |
| Бангладеш | `is_bangladesh_state` | `is_bangladesh_state_owned` |
| Непал | `is_nepal_state` | `is_nepal_state_owned` |
| Бутан | `is_bhutan_state` | `is_bhutan_state_owned` |
| Шри-Ланка | `is_srilanka_state` | `is_srilanka_state_owned` |
| Афганистан | `is_afghanistan_state` | `is_afghanistan_state_owned` |
| Иран | `is_iran_state` | `is_iran_state_owned` |

**Иран / Афганистан / Курдистан**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Курдистан | `is_kurdistan_state` | `is_kurdistan_state_owned` |
| Алжир | `is_algeria_state` | `is_algeria_state_owned` |
| Ливия | `is_libya_state` | `is_libya_state_owned` |

**Северная Африка и Ближний Восток**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Австро-Венгрия | `is_austria_hungary_state` | `is_austria_hungary_state_owned` |
| Сирия | `is_syria_state` | `is_syria_state_owned` |
| Египет | `is_egypt_state` | `is_egypt_state_owned` |
| Ливан | `is_lebanese_state` | `is_lebanese_state_owned` |
| Ирак | `is_iraq_state` | `is_iraq_state_owned` |
| Мавритания | `is_mauritania_state` | `is_mauritania_state_owned` |
| Саудовская Аравия | `is_saudi_state` | `is_saudi_state_owned` |
| Оман | `is_oman_state` | `is_oman_state_owned` |
| ОАЭ | `is_uae_state` | `is_uae_state_owned` |
| Западная Сахара | `is_sahrawi_state` | `is_sahrawi_state_owned` |
| Тунис | `is_tunis_state` | `is_tunis_state_owned` |

**Африка южнее Сахары**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Сомали | `is_somali_state` | `is_somali_state_owned` |
| Центральноафриканские государства | `is_central_african_state` | `is_central_african_state_owned` |
| Малийские государства | `is_malian_state` | `is_malian_state_owned` |
| Сенегальские государства | `is_senegal_state` | `is_senegal_state_owned` |

**Карибы**

| Регион | `is_X_state` (регион состояния) | `is_X_state_owned` (страна владеет всем регионом) |
|---|---|---|
| Карибские острова | `is_caribbean_island_state` | — |

⚠️ Два расхождения между списками: у `is_caribbean_island_states` нет пары `_owned` (Карибы разбросаны по слишком многим владельцам, чтобы это было осмысленно), а у США есть дополнительный `is_usa_state_mainland_owned` — вариант только для континентальной части США, без заморских территорий (Аляска, Пуэрто-Рико и т.д. не считаются).

<a id="continents"></a>
## Континенты

| Триггер | Условие |
|---|---|
| `is_in_africa` / `is_in_asia` / `is_in_europe` / `is_in_south_america` / `is_in_north_america` | Столица страны находится на этом континенте |
| `is_in_the_americas` | Столица в Северной **или** Южной Америке |
| `is_in_the_middle_east` | Столица на Ближнем Востоке (отдельный от Азии/Африки континент в разметке карты) |
| `is_in_oceania` | Столица в Океании |
| `is_in_the_caribbean` | Хотя бы одна провинция страны находится в ai_area 16 (Карибы) |
| `PREV_is_on_same_continent` | THIS и PREV на одном континенте (перебирает все континенты попарно) |
| `PREV_is_not_on_same_continent` | Обратное — THIS и PREV на разных континентах |

⚠️ **Возможная нестыковка**: `is_in_oceania` использует континент `oceania`, а вот `PREV_is_on_same_continent`/`PREV_is_not_on_same_continent` вместо этого сравнивают континент `australia` — то есть эти два триггера де-факто не знают о существовании Океании как отдельного континента и могут неверно определять «тот же континент» для тихоокеанских островных стран. Возможно, стоит привести к единому имени континента.

<a id="country-groups"></a>
## Группы стран

Смешанная категория — географические, языковые и тематические/сюжетные группы.

**Географические союзы/блоки**

| Триггер | Описание |
|---|---|
| `is_EFTA` | Член ЕАСТ (Европейская ассоциация свободной торговли) |
| `is_Schengen_Area` | Член Шенгенской зоны |
| `is_North_America` / `is_Central_America` / `is_South_America` | Страна в соответствующей части Америки |
| `is_Central_Asia` / `is_Caucasus` / `is_South_Asia` / `is_East_Asia` | Регион Азии |
| `is_asean_nation` | Член АСЕАН |
| `is_oceania_nation` | Тихоокеанская страна |
| `is_caribbean_nation` | Карибская страна |

**Более широкие цивилизационные/культурные группы**

| Триггер | Описание |
|---|---|
| `is_european_nation` / `is_east_european_nation` / `is_balkan_nation` | Европа целиком / Восточная Европа / Балканы |
| `is_middle_eastern_nation` / `is_arabic_nation` / `is_iranian_nation` | Ближний Восток / арабский мир / Иран (персидский мир) |
| `is_asian_nation` / `is_american_nation` / `is_western_nation` / `is_african_nation` | Крупные цивилизационные блоки |
| `is_west_african_nation` / `is_central_african_nation` / `is_horn_of_africa_nation` / `is_somali_nation` / `is_sudanese_nation` | Африканские субрегионы |
| `is_sahara_nation` / `is_sahel_nation` | Сахара / Сахель |
| `is_french_africa_nation` | Франкоязычная Африка |

⚠️ **Баг: `is_sahel_nation` определён дважды** в файле — первая версия (12 тегов, включая BUF/ERI/GUB/TIE/TUA) находится выше по файлу, но затем ниже идёт вторая версия с другим списком (6 тегов, включая BFA вместо BUF). В HOI4-скриптах повторное определение триггера с тем же именем **тихо перезаписывает предыдущее** — значит, первая версия мертва и никогда не используется, независимо от того, что задумывалось изначально.

**Языковые группы**

`French_Speaking`, `Spanish_Speaking`, `Portugese_Speaking`, `Chinese_Speaking`, `Swahili_Speaking`, `German_Speaking`, `Russian_Proficient`, `English_Speaking` — проверяют, говорит ли страна на соответствующем языке (список тегов).

**Тематические / сюжетные группы**

| Триггер | Описание |
|---|---|
| `is_islamist_secularism_mechanic` | Страна использует механику «исламизм vs. секуляризм» |
| `is_arid_nation` / `is_tropical_nation` | Засушливый / тропический климат страны |
| `is_earthquake_prone_nation` | Страна в сейсмоопасной зоне |
| `is_micro_nation` | Микрогосударство |
| `is_banana_nation` | «Банановая республика» — экономика на монокультуре (CAM, CDI, COL, COS, DOM, ECU, GUA, HON, PHI) |
| `is_island_country` | Островное государство |
| `HIV_Epidemic` | Страна с эпидемией ВИЧ (для континента Африка) |
| `Is_Possible_Muslim_Brotherhood` / `Is_Muslim_Brotherhood` | Потенциально/фактически управляется «Братьями-мусульманами» |
| `Is_2017_Riyadh_Summit_Member` | Участник саммита в Эр-Рияде 2017 года (антитеррористическая коалиция) |
| `Is_Permanent_UN_Member` / `Is_UN_Member` | Постоянный член СБ ООН / просто член ООН |
| `is_not_custom_mio_country` | Страна НЕ входит в список из 9 держав с уникальным военно-промышленным блоком (BRA, ROM, JAP, CHI, HOL, GER, ENG, SWE, AST) |
| `mediterranean_tags` | Не совсем триггер в привычном смысле — список тегов Средиземноморья для нужд ИИ |
| `ROOT_and_THIS_are_in_the_same_group` | ROOT и THIS входят в одну и ту же именованную группу стран (используется как обобщённая проверка) |

<a id="arctic"></a>
## Арктика

Арктическая система делит карту на ~19 пронумерованных зон (0–18) с собственной таблицей соседства между ними (какая зона граничит с какой) и глобальными массивами `global.arctic_controllers` (кто контролирует зону), `global.arctic_military` (есть ли военная база), `global.arctic_unit_strngth`/`global.arctic_unit_org` (войска в зоне).

| Триггер | Описание |
|---|---|
| `arctic_state_is_coastal` | Зона ROOT — одна из прибрежных (список конкретных ID зон) |
| `arctic_state_is_neighbor` | Проверяет, граничит ли зона ROOT с конкретной другой зоной (по таблице соседства) |
| `controlls_neighbor_arctic_state` | ROOT контролирует хотя бы одну из зон, соседних с его собственной |
| `has_enemy_neighbor_states` | В соседней зоне сидит враждебная (в состоянии войны) держава |
| `has_root_neighbor_state_with_unit` | В соседней зоне у контролирующей её страны есть боеспособные войска (сила и организация > 0) |
| `has_arctic_military_base` | У страны есть военная база хотя бы в одной из своих арктических зон |

Расшифровать, какая именно географическая территория скрывается за каждым номером зоны (0–18), по этому файлу невозможно — соответствие «номер зоны → реальный регион» задаётся в других файлах (decisions/state ID), которых нет в этом архиве.
