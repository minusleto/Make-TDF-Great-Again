---
title: Внутренние фракции
description: "Триггеры проверки мнения внутренних фракций MDC"
---

## Триггеры мнения фракций

Здесь — триггеры для **проверки** мнения фракций. Чтобы **изменить** мнение — см. [Эффекты → Внутренние фракции](../../effects/internal-factions/).

У каждой из 23 внутренних фракций MDC есть переменная `<фракция>_opinion` (0–100) и готовый набор из 6 триггеров, проверяющих её без ручного `check_variable`:

| Фракция | Переменная | Восторженно (>79) | Позитивно (60–79) | Нейтрально (40–60) | Негативно (20–39) | Враждебно (<20) |
|---|---|---|---|---|---|---|
| Владельцы малого и среднего бизнеса | `small_medium_business_owners_opinion` | `enthusiastic_small_medium_business_owners` | `positive_small_medium_business_owners` | `indifferent_small_medium_business_owners` | `negative_small_medium_business_owners` | `hostile_small_medium_business_owners` |
| Международные банкиры | `international_bankers_opinion` | `enthusiastic_international_bankers` | `positive_international_bankers` | `indifferent_international_bankers` | `negative_international_bankers` | `hostile_international_bankers` |
| Олигархи | `oligarchs_opinion` | `enthusiastic_oligarchs` | `positive_oligarchs` | `indifferent_oligarchs` | `negative_oligarchs` | `hostile_oligarchs` |
| Промышленные конгломераты | `industrial_conglomerates_opinion` | `enthusiastic_industrial_conglomerates` | `positive_industrial_conglomerates` | `indifferent_industrial_conglomerates` | `negative_industrial_conglomerates` | `hostile_industrial_conglomerates` |
| Нефтегазовая отрасль | `fossil_fuel_industry_opinion` | `enthusiastic_fossil_fuel_industry` | `positive_fossil_fuel_industry` | `indifferent_fossil_fuel_industry` | `negative_fossil_fuel_industry` | `hostile_fossil_fuel_industry` |
| Спецслужбы | `intelligence_community_opinion` | `enthusiastic_intelligence_community` | `positive_intelligence_community` | `indifferent_intelligence_community` | `negative_intelligence_community` | `hostile_intelligence_community` |
| Военные | `the_military_opinion` | `enthusiastic_the_military` | `positive_the_military` | `indifferent_the_military` | `negative_the_military` | `hostile_the_military` |
| Оборонная промышленность | `defense_industry_opinion` | `enthusiastic_defense_industry` | `positive_defense_industry` | `indifferent_defense_industry` | `negative_defense_industry` | `hostile_defense_industry` |
| Морская отрасль | `maritime_industry_opinion` | `enthusiastic_maritime_industry` | `positive_maritime_industry` | `indifferent_maritime_industry` | `negative_maritime_industry` | `hostile_maritime_industry` |
| Ваххабитские улемы | `wahabi_ulema_opinion` | `enthusiastic_wahabi_ulema` | `positive_wahabi_ulema` | `indifferent_wahabi_ulema` | `negative_wahabi_ulema` | `hostile_wahabi_ulema` |
| Духовенство (христианское) | `the_priesthood_opinion` | `enthusiastic_the_priesthood` | `positive_the_priesthood` | `indifferent_the_priesthood` | `negative_the_priesthood` | `hostile_the_priesthood` |
| Улемы | `the_ulema_opinion` | `enthusiastic_the_ulema` | `positive_the_ulema` | `indifferent_the_ulema` | `negative_the_ulema` | `hostile_the_ulema` |
| Клир | `the_clergy_opinion` | `enthusiastic_the_clergy` | `positive_the_clergy` | `indifferent_the_clergy` | `negative_the_clergy` | `hostile_the_clergy` |
| Партийные кадры | `communist_cadres_opinion` | `enthusiastic_communist_cadres` | `positive_communist_cadres` | `indifferent_communist_cadres` | `negative_communist_cadres` | `hostile_communist_cadres` |
| Фермеры | `farmers_opinion` | `enthusiastic_farmers` | `positive_farmers` | `indifferent_farmers` | `negative_farmers` | `hostile_farmers` |
| Землевладельцы | `landowners_opinion` | `enthusiastic_landowners` | `positive_landowners` | `indifferent_landowners` | `negative_landowners` | `hostile_landowners` |
| Профсоюзы | `labour_unions_opinion` | `enthusiastic_labour_unions` | `positive_labour_unions` | `indifferent_labour_unions` | `negative_labour_unions` | `hostile_labour_unions` |
| Иностранные джихадисты | `foreign_jihadis_opinion` | `enthusiastic_foreign_jihadis` | `positive_foreign_jihadis` | `indifferent_foreign_jihadis` | `negative_foreign_jihadis` | `hostile_foreign_jihadis` |
| Иранский КСИР «Кудс» | `iranian_quds_force_opinion` | `enthusiastic_iranian_quds_force` | `positive_iranian_quds_force` | `indifferent_iranian_quds_force` | `negative_iranian_quds_force` | `hostile_iranian_quds_force` |
| Саудовская королевская семья | `saudi_royal_family_opinion` | `enthusiastic_saudi_royal_family` | `positive_saudi_royal_family` | `indifferent_saudi_royal_family` | `negative_saudi_royal_family` | `hostile_saudi_royal_family` |
| Чеболи | `chaebols_opinion` | `enthusiastic_chaebols` | `positive_chaebols` | `indifferent_chaebols` | `negative_chaebols` | `hostile_chaebols` |
| Уолл-стрит | `wall_street_opinion` | `enthusiastic_wall_street` | `positive_wall_street` | `indifferent_wall_street` | `negative_wall_street` | `hostile_wall_street` |
| Тонджу (севкорейские нувориши) | `the_donju_opinion` | `enthusiastic_the_donju` | `positive_the_donju` | `indifferent_the_donju` | `negative_the_donju` | `hostile_the_donju` |

⚠️ **Баг в исходнике мода**: `non_indifferent_*` (столбца в таблице нет специально) есть у всех 23 фракций, но триггер сломан — внутри одновременно требуется `check_variable > 61` **И** `< 39` в одном и том же блоке (а в HOI4-скриптах условия внутри блока триггера объединяются через AND). Ни одно число не может быть одновременно больше 61 и меньше 39 — триггер **никогда не станет true**. Если нужно проверить «мнение не нейтральное» (то есть либо явно позитивное, либо явно негативное), пишите вручную:

```
OR = {
	check_variable = { <фракция>_opinion > 61 }
	check_variable = { <фракция>_opinion < 39 }
}
```

<a id="extra-shortcuts"></a>
### Доп. удобные триггеры

У части фракций (Олигархи, Промышленные конгломераты, Спецслужбы, Военные, Ваххабитские улемы, Духовенство, Улемы, Королевская семья Саудовской Аравии) есть свои дополнительные готовые триггеры с нестандартными порогами — исторически завязанными под конкретные ивенты/фокусы, а не на общую сетку 20/40/60/80:

| Триггер | Условие | Описание |
|---|---|---|
| `oligarchs_at_least_enthusiastic_opinion` | `oligarchs_opinion > 74` | Олигархи на грани восторга (>74) |
| `oligarchs_at_least_positive_opinion` | `oligarchs_opinion > 50` | Олигархи как минимум нейтрально-позитивны (>50) |
| `oligarchs_not_positive_opinion` | `oligarchs_opinion < 50` | Олигархи не позитивны (<50) |
| `industrial_conglomerates_at_least_enthusiastic_opinion` | `industrial_conglomerates_opinion > 74` | Конгломераты на грани восторга (>74) |
| `intelligence_community_at_least_positive_opinion` | `intelligence_community_opinion > 59` | Спецслужбы как минимум позитивны (>59) |
| `intelligence_community_not_positive_opinion` | `intelligence_community_opinion < 59` | Спецслужбы не позитивны (<59) |
| `military_at_least_enthusiastic_opinion` | `the_military_opinion > 74.99` | Военные на грани восторга (>74.99); сработает только если у страны есть фракция военных (`has_idea = the_military`) |
| `military_at_least_positive_opinion` | `the_military_opinion > 50` | Военные как минимум нейтрально-позитивны (>50); сработает только если у страны есть фракция военных (`has_idea = the_military`) |
| `wahule_at_least_positive_opinion` | `wahabi_ulema_opinion > 59` | Ваххабитские улемы как минимум позитивны (>59) |
| `the_priesthood_at_least_enthusiastic_opinion` | `the_priesthood_opinion > 75` | Духовенство на грани восторга (>75) |
| `the_priesthood_at_least_indifferent_opinion` | `the_priesthood_opinion > 49` | Духовенство как минимум нейтрально (>49) |
| `the_ulema_at_least_positive_opinion` | `the_ulema_opinion > 59` | Улемы как минимум позитивны (>59) |
| `sarf_at_least_positive_opinion` | `saudi_royal_family_opinion > 59` | Королевская семья как минимум позитивна (>59) |
| `sarf_at_least_indifferent_opinion` | `saudi_royal_family_opinion > 49` | Королевская семья как минимум нейтральна (>49) |
| `communist_cadres_at_least_enthusiastic_opinion` | `communist_cadres_opinion > 74.99` | Партийные кадры на грани восторга (>74.99); сработает только если у страны есть фракция `has_idea = communist_cadres` |
| `communist_cadres_at_least_positive_opinion` | `communist_cadres_opinion > 50` | Партийные кадры как минимум нейтрально-позитивны (>50); тоже требует `has_idea = communist_cadres` |

:::note
Небольшое пересечение границ в основной шестёрке: `positive_*` требует `> 59` (т.е. ≥60), `indifferent_*` требует `< 61` (т.е. ≤60) — при значении ровно **60** оба триггера истинны одновременно.
:::
