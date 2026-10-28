---
title: Внутренние фракции
description: "Эффекты и команды внутренних фракций"
---

## Эффекты внутренних фракций MDC

Здесь — эффекты для **изменения** мнения фракций. Чтобы **проверить** текущий уровень мнения (враждебное/негативное/нейтральное/позитивное/восторженное) — см. [Триггеры → Внутренние фракции](../../triggers/internal-factions/).

<a id="faction-list"></a>
### Название и смена мнения фракций

<div style="overflow-x:auto">
<table style="width:100%; border-collapse:collapse; font-size:0.82em; line-height:1.25; table-layout:auto; border:1px solid #444">
<thead>
<tr style="background:#2d2d2d; color:#fff">
<th style="padding:3px 8px; text-align:left; white-space:nowrap">Фракция</th>
<th style="padding:3px 8px; text-align:left; white-space:nowrap">ID</th>
<th style="padding:3px 8px; text-align:left; white-space:nowrap">Эффект смены мнения</th>
</tr>
</thead>
<tbody>
<tr style="background:#5B9BD5; color:#000"><td style="padding:2px 8px; white-space:nowrap">Малый и средний бизнес</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">small_medium_business_owners</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_small_medium_business_owners_opinion</code></td></tr>
<tr style="background:#5B9BD5; color:#000"><td style="padding:2px 8px; white-space:nowrap">Международные банкиры</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">international_bankers</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_international_bankers_opinion</code></td></tr>
<tr style="background:#5B9BD5; color:#000"><td style="padding:2px 8px; white-space:nowrap">Нефтегазовая промышленность</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">fossil_fuel_industry</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_fossil_fuel_industry_opinion</code></td></tr>
<tr style="background:#5B9BD5; color:#000"><td style="padding:2px 8px; white-space:nowrap">Промышленные конгломераты</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">industrial_conglomerates</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_industrial_conglomerates_opinion</code></td></tr>
<tr style="background:#5B9BD5; color:#000"><td style="padding:2px 8px; white-space:nowrap">Олигархи</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">oligarchs</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_oligarchs_opinion</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px; white-space:nowrap">Морская промышленность</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">maritime_industry</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_maritime_industry_opinion</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px; white-space:nowrap">Оборонная промышленность</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">defense_industry</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_defense_industry_opinion</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px; white-space:nowrap">Военные</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">the_military</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_the_military_opinion</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px; white-space:nowrap">Разведывательное сообщество</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">intelligence_community</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_intelligence_community_opinion</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px; white-space:nowrap">Иностранные джихадисты</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">foreign_jihadis</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_foreign_jihadis_opinion</code></td></tr>
<tr style="background:#C0504D; color:#000"><td style="padding:2px 8px; white-space:nowrap">Профсоюзы</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">labour_unions</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_labour_unions_opinion</code></td></tr>
<tr style="background:#C0504D; color:#000"><td style="padding:2px 8px; white-space:nowrap">Землевладельцы</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">landowners</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_landowners_opinion</code></td></tr>
<tr style="background:#C0504D; color:#000"><td style="padding:2px 8px; white-space:nowrap">Фермеры</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">farmers</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_farmers_opinion</code></td></tr>
<tr style="background:#C0504D; color:#000"><td style="padding:2px 8px; white-space:nowrap">Коммунистические кадры</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">communist_cadres</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_communist_cadres_opinion</code></td></tr>
<tr style="background:#8064A2; color:#000"><td style="padding:2px 8px; white-space:nowrap">Священство</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">the_priesthood</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_the_priesthood_opinion</code></td></tr>
<tr style="background:#8064A2; color:#000"><td style="padding:2px 8px; white-space:nowrap">Улемы</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">the_ulema</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_the_ulema_opinion</code></td></tr>
<tr style="background:#8064A2; color:#000"><td style="padding:2px 8px; white-space:nowrap">Духовенство</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">the_clergy</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_the_clergy_opinion</code></td></tr>
<tr style="background:#8064A2; color:#000"><td style="padding:2px 8px; white-space:nowrap">Ваххабитские улемы</td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">wahabi_ulema</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_the_wahabi_ulema_opinion</code></td></tr>
<tr style="background:#ED7D31; color:#000"><td style="padding:2px 8px; white-space:nowrap"><abbr title="Уникальная фракция — только для Северной Кореи" style="text-decoration:underline dotted; text-decoration-color:currentColor; cursor:help">Донжу</abbr></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">the_donju</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_the_donju_opinion</code></td></tr>
<tr style="background:#ED7D31; color:#000"><td style="padding:2px 8px; white-space:nowrap"><abbr title="Уникальная фракция — только для стран Персидского залива" style="text-decoration:underline dotted; text-decoration-color:currentColor; cursor:help">Саудовская королевская семья</abbr></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">saudi_royal_family</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_saudi_royal_family_opinion</code></td></tr>
<tr style="background:#ED7D31; color:#000"><td style="padding:2px 8px; white-space:nowrap"><abbr title="Уникальная фракция — только для Ирана. Включает IRGC (отдельного эффекта для IRGC не существует)" style="text-decoration:underline dotted; text-decoration-color:currentColor; cursor:help">Иранские силы Кудс</abbr></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">iranian_quds_force</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_iranian_quds_force_opinion</code></td></tr>
<tr style="background:#ED7D31; color:#000"><td style="padding:2px 8px; white-space:nowrap"><abbr title="Уникальная фракция — только для Южной Кореи" style="text-decoration:underline dotted; text-decoration-color:currentColor; cursor:help">Чеболи</abbr></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">chaebols</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_chaebols_opinion</code></td></tr>
<tr style="background:#ED7D31; color:#000"><td style="padding:2px 8px; white-space:nowrap"><abbr title="Уникальная фракция — только для США" style="text-decoration:underline dotted; text-decoration-color:currentColor; cursor:help">Уолл-стрит</abbr></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">wall_street</code></td><td style="padding:2px 8px; white-space:nowrap"><code style="background:transparent; color:inherit; padding:1px 5px">change_wall_street_opinion</code></td></tr>
</tbody>
</table>
</div>

<a id="how-to-change-factions"></a>
### Как правильно менять фракции

При смене основной фракции сначала проверь, какая идея уже установлена, и только потом меняй её через `swap_ideas`. Так закон не сломается, если у страны изначально другая фракция.

```txt
if = {
    limit = { has_idea = labour_unions }
    swap_ideas = {
        remove_idea = labour_unions
        add_idea = the_military
    }
}
else_if = {
    limit = { has_idea = farmers }
    swap_ideas = {
        remove_idea = farmers
        add_idea = the_military
    }
}
```

**Не обязательно перечислять все возможные фракции.** В законе достаточно обработать те, что реально могут встретиться при его условиях — полный список тегов идей см. в [таблице фракций](#faction-list) ниже. Уникальные и страновые фракции добавляйте, только если закон действительно может их застать.

<a id="how-it-works"></a>
### Как это работает

1. У каждой активной фракции есть мнение **0–100**, обычно стартующее с **50**.
2. `change_*_opinion` меняет мнение на указанное значение, а не задаёт итоговое число. Для массового изменения используется `change_all_internal_faction_opinion`.
3. **Автократы получают двойной эффект** — позитивное изменение удваивается, если правящая партия относится к автократическому архетипу (прозападные, зарождающиеся или неприсоединившиеся автократы, фашисты, военная хунта).
4. Мнение влияет на связанные с фракцией динамические модификаторы и может постепенно тянуться обратно к минимуму, если оно выше него.

<a id="bulk-and-utility-effects"></a>
### Служебные эффекты

Изменить мнение сразу у всех активных фракций:

```
set_temp_variable = { temp_all_opinion = 5 }
change_all_internal_faction_opinion = yes
```

Дебаг/чит-команды:

```
set_to_max_internal_faction_opinions = yes
reset_all_internal_faction_opinions = yes
```

<a id="election-funding"></a>
### Влияние на выборы

Мнение фракций участвует в системе выборов MDC: базовое значение `campaign_funding_count` — **10**, а активные фракции добавляют от **-2 до +2** в зависимости от своего отношения. Это считается автоматически эффектом `display_election_campaign_status`.
