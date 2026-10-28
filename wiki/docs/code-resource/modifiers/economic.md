---
title: Экономические модификаторы
description: "Модификаторы роста экономики, инфляции, налогов, экспорта, филиалов компаний и стоимости апгрейдов"
---

## Экономические модификаторы

Влияют на экономику, налоги, торговлю и производительность.

### Производство гражданского транспорта

| Модификатор | Описание | Примечание |
|---|---|---|
| `auto_production_modifier` | Меняет ежемесячное производство гражданских автомобилей | Числовое значение; может быть отрицательным |
| `planes_production_modifier` | Меняет ежемесячное производство гражданских самолётов | Числовое значение; может быть отрицательным |
| `trains_production_modifier` | Меняет ежемесячное производство гражданских поездов | Числовое значение; может быть отрицательным |
| `helos_production_modifier` | Меняет ежемесячное производство гражданских вертолётов | Числовое значение; может быть отрицательным |
| `ships_production_modifier` | Меняет ежемесячное производство гражданских кораблей | Числовое значение; может быть отрицательным |

### Ожидаемая зарплата

| Модификатор | Описание | Примечание |
|---|---|---|
| `expected_salary_modifier` | Меняет ожидаемую зарплату | Целое число |

<a id="vanilla"></a>
### Ванильные

| Модификатор | Описание | Примечание |
|---|---|---|
| `monthly_population` | Меняет ежемесячный прирост населения в регионах | Н/Д |
| `consumer_goods_factor` | Меняет долю фабрик под потребительские товары | Складывается мультипликативно, см. вики HOI4 |
| `local_resources_factor` | Меняет эффективность добычи **всех** ресурсов сразу, в процентах | Для конкретного ресурса — `local_resources_<ресурс>_factor` (страна, ниже) или `state_resource_<ресурс>` (регион), см. [Региональные модификаторы](../regional/#vanilla) |
| `local_resources_oil_factor` | Меняет эффективность добычи нефти по всей стране, в процентах | Страновой, не региональный |
| `local_resources_aluminium_factor` | Меняет эффективность добычи алюминия по всей стране, в процентах | Страновой, не региональный |
| `local_resources_rubber_factor` | Меняет эффективность добычи каучука по всей стране, в процентах | Страновой, не региональный |
| `local_resources_tungsten_factor` | Меняет эффективность добычи вольфрама по всей стране, в процентах | Страновой, не региональный |
| `local_resources_steel_factor` | Меняет эффективность добычи стали по всей стране, в процентах | Страновой, не региональный |
| `local_resources_chromium_factor` | Меняет эффективность добычи хрома по всей стране, в процентах | Страновой, не региональный |
| `country_resource_<ресурс>` | Добавляет фиксированное количество конкретного ресурса в стратзапас страны (напр. `country_resource_steel`) | Подтверждено офиц. документацией модификаторов Paradox |
| `research_speed_factor` | Меняет скорость исследований | Н/Д |
| `industrial_capacity_factory` | Меняет выпуск военных фабрик | Н/Д |
| `industrial_capacity_dockyard` | Меняет выпуск верфей | Н/Д |
| `production_speed_buildings_factor` | Меняет скорость строительства всех построек | Н/Д |
| `industry_repair_factor` | Меняет скорость починки построек | Н/Д |
| `global_building_slots` | Меняет число слотов построек во всех регионах | Н/Д |
| `global_building_slots_factor` | То же самое, в процентах | Н/Д |
| `conversion_cost_civ_to_mil_factor` | Меняет цену конверсии гражд. фабрик в военные | Н/Д |
| `conversion_cost_mil_to_civ_factor` | Меняет цену конверсии военных фабрик в гражданские | Н/Д |
| `production_oil_factor` | Меняет прирост синтетической нефти | Н/Д |
| `nuclear_production_factor` | Меняет скорость производства ядерного оружия | Н/Д |

<a id="general-economic"></a>
### Общие экономические

| Модификатор | Описание | Примечание |
|---|---|---|
| `interest_rate_multiplier_modifier` | Меняет процентную ставку страны | Целое число (например, -1) |
| `central_bank_rate_change_multiplier_modifier` | Множитель стоимости изменения ставки ЦБ в ПП | Н/Д |
| `tax_rate_change_multiplier_modifier` | Меняет цену смены налоговой ставки в PP | Н/Д |
| `projects_cost_modifier` | Меняет стоимость экономических проектов | Н/Д |
| `tax_gain_multiplier_modifier` | Меняет доход от всех налогов | Н/Д |
| `population_tax_income_multiplier_modifier` | Меняет доход от налогов с населения | Н/Д |
| `corporate_tax_income_multiplier_modifier` | Меняет доход от корпоративных налогов | Н/Д |
| `productivity_growth_modifier` | Меняет рост производительности страны | Держите значение небольшим — эффект накапливается |
| `country_productivity_growth_modifier` | То же самое, но явно на уровне страны | Н/Д |
| `international_market_income_modifier` | Меняет доход от продажи снаряжения на рынке | Н/Д |
| `international_market_purchase_modifier` | Меняет стоимость покупки снаряжения на рынке | Н/Д |
| `production_speed_civil_bunker_factor` | Меняет скорость строительства гражданских бункеров | В процентах |

<a id="spending-cost-multipliers"></a>
### Стоимость обслуживания (расходы)

Множители текущих расходов страны (не путать со стоимостью смены закона в PP — см. `laws.md`).

| Модификатор | Описание | Примечание |
|---|---|---|
| `personnel_cost_multiplier_modifier` | Меняет расходы на военные зарплаты | Н/Д |
| `army_personnel_cost_multiplier_modifier` | Меняет расходы на зарплаты армии | Н/Д |
| `navy_personnel_cost_multiplier_modifier` | Меняет расходы на зарплаты флота | Н/Д |
| `airforce_personnel_cost_multiplier_modifier` | Меняет расходы на зарплаты авиации | Н/Д |
| `equipment_cost_multiplier_modifier` | Меняет стоимость содержания снаряжения | Н/Д |
| `bureaucracy_cost_multiplier_modifier` | Меняет расходы на бюрократию | Н/Д |
| `police_cost_multiplier_modifier` | Меняет расходы на внутреннюю безопасность | Н/Д |
| `education_cost_multiplier_modifier` | Меняет расходы на образование | Н/Д |
| `health_cost_multiplier_modifier` | Меняет расходы на здравоохранение | Н/Д |
| `social_cost_multiplier_modifier` | Меняет расходы на соцобеспечение | Н/Д |
| `border_control_multiplier_modifier` | Меняет расходы на контроль миграции | Н/Д |

<a id="inflation"></a>
### Инфляция

Все значения в процентах: 1 = +100%.

| Модификатор | Описание | Примечание |
|---|---|---|
| `inflation_multiplier_modifier` | Модификатор инфляции | 1 = +100% |
| `inflation_defence_multiplier_modifier` | Модификатор защиты от инфляции | 1 = +100% |
| `inflation_from_dept_multiplier_modifier` | Влияние долга на инфляцию | 1 = +100% |
| `inflation_from_export_multiplier_modifier` | Влияние экспорта на инфляцию | 1 = +100% |
| `treasury_to_gdp_inflation_multiplier_modifier` | Влияние казны на инфляцию | 1 = +100% |
| `base_inflation_percent_modifier` | Модификатор базовой инфляции | 1 = +100% |

<a id="exports-resources"></a>
### Экспорт и ресурсы

| Модификатор | Описание | Примечание |
|---|---|---|
| `resource_export_multiplier_modifier` | Меняет доход от экспорта всех ресурсов | Н/Д |
| `oil_export_multiplier_modifier` | Меняет доход от экспорта топлива | Н/Д |
| `steel_export_multiplier_modifier` | Меняет доход от экспорта стали | Н/Д |
| `aluminium_export_multiplier_modifier` | Меняет доход от экспорта лёгких металлов | Н/Д |
| `tungsten_export_multiplier_modifier` | Меняет доход от экспорта техн. металлов | Н/Д |
| `chromium_export_multiplier_modifier` | Меняет доход от экспорта драг. металлов | Н/Д |
| `rubber_export_multiplier_modifier` | Меняет доход от экспорта каучука | Н/Д |
| `gdp_from_resource_sector_modifier` | Меняет ВВП от ресурсного сектора | Н/Д |

<a id="industry-productivity"></a>
### Производительность промышленности

| Модификатор | Описание | Примечание |
|---|---|---|
| `agricolture_productivity_modifier` | Меняет производительность сельского хозяйства | Н/Д |
| `civilian_factories_productivity` | Меняет производительность гражд. фабрик | Н/Д |
| `military_factories_productivity` | Меняет производительность военных фабрик | Н/Д |
| `dockyard_productivity` | Меняет производительность верфей | Н/Д |
| `rub_ref_productivity` | Меняет производительность резиновых заводов | Н/Д |
| `offices_productivity` | Меняет производительность офисов | Н/Д |

<a id="production-speed-buildings"></a>
### Скорость строительства по типу здания

Аналог `production_speed_buildings_factor`, но действует только на конкретный тип постройки.

| Модификатор | Описание | Примечание |
|---|---|---|
| `production_speed_agriculture_district_factor` | Меняет скорость строительства с/х районов | Н/Д |
| `production_speed_air_base_factor` | Меняет скорость строительства аэродромов | Н/Д |
| `production_speed_air_facility_factor` | Меняет скорость строительства авиазаводов | Н/Д |
| `production_speed_anti_air_building_factor` | Меняет скорость строительства построек ПВО | Н/Д |
| `production_speed_arms_factory_factor` | Меняет скорость строительства военных фабрик | Н/Д |
| `production_speed_bunker_factor` | Меняет скорость строительства бункеров | Н/Д |
| `production_speed_coastal_bunker_factor` | Меняет скорость строительства береговых бункеров | Н/Д |
| `production_speed_dockyard_factor` | Меняет скорость строительства верфей | Н/Д |
| `production_speed_fossil_powerplant_factor` | Меняет скорость строительства топливных электростанций | Н/Д |
| `production_speed_fuel_silo_factor` | Меняет скорость строительства топливных хранилищ | Н/Д |
| `production_speed_industrial_complex_factor` | Меняет скорость строительства гражданских фабрик | Н/Д |
| `production_speed_infrastructure_factor` | Меняет скорость строительства инфраструктуры | Н/Д |
| `production_speed_internet_station_factor` | Меняет скорость строительства интернет-станций | Н/Д |
| `production_speed_land_facility_factor` | Меняет скорость строительства земельных пром. объектов | Н/Д |
| `production_speed_naval_base_factor` | Меняет скорость строительства военно-морских баз | Н/Д |
| `production_speed_naval_facility_factor` | Меняет скорость строительства военно-морских объектов | Н/Д |
| `production_speed_naval_headquarters_factor` | Меняет скорость строительства штабов флота | Н/Д |
| `production_speed_naval_supply_hub_factor` | Меняет скорость строительства узлов снабжения флота | Н/Д |
| `production_speed_nuclear_facility_factor` | Меняет скорость строительства ядерных объектов | Н/Д |
| `production_speed_nuclear_reactor_factor` | Меняет скорость строительства ядерных реакторов | Н/Д |
| `production_speed_offices_factor` | Меняет скорость строительства офисных комплексов | Н/Д |
| `production_speed_radar_station_factor` | Меняет скорость строительства радарных станций | Н/Д |
| `production_speed_rail_way_factor` | Меняет скорость строительства железных дорог | Н/Д |
| `production_speed_rocket_site_factor` | Меняет скорость строительства ракетных площадок | Н/Д |
| `production_speed_rubber_refinery_factor` | Меняет скорость строительства резиновых заводов | Н/Д |
| `production_speed_stronghold_network_factor` | Меняет скорость строительства сети укреплений | Н/Д |
| `production_speed_supply_node_factor` | Меняет скорость строительства узлов снабжения | Н/Д |
| `production_speed_synthetic_refinery_factor` | Меняет скорость строительства инфраструктуры возобновляемых источников энергии | Н/Д |

<a id="production-cost-buildings"></a>
### Стоимость строительства по типу здания

В отличие от скорости, эти модификаторы меняют саму IC-стоимость постройки конкретного типа (сколько "молотков" нужно потратить), а не то, как быстро она строится.

| Модификатор | Описание | Примечание |
|---|---|---|
| `production_cost_agriculture_district_factor` | Меняет стоимость строительства с/х районов | Н/Д |
| `production_cost_air_base_factor` | Меняет стоимость строительства аэродромов | Н/Д |
| `production_cost_anti_air_building_factor` | Меняет стоимость строительства построек ПВО | Н/Д |
| `production_cost_arms_factory_factor` | Меняет стоимость строительства военных фабрик | Н/Д |
| `production_cost_bunker_factor` | Меняет стоимость строительства бункеров | Н/Д |
| `production_cost_coastal_bunker_factor` | Меняет стоимость строительства береговых бункеров | Н/Д |
| `production_cost_dockyard_factor` | Меняет стоимость строительства верфей | Н/Д |
| `production_cost_fossil_powerplant_factor` | Меняет стоимость строительства топливных электростанций | Н/Д |
| `production_cost_fuel_silo_factor` | Меняет стоимость строительства топливных хранилищ | Н/Д |
| `production_cost_industrial_complex_factor` | Меняет стоимость строительства гражданских фабрик | Н/Д |
| `production_cost_infrastructure_factor` | Меняет стоимость строительства инфраструктуры | Н/Д |
| `production_cost_internet_station_factor` | Меняет стоимость строительства сетевой инфраструктуры | Н/Д |
| `production_cost_naval_base_factor` | Меняет стоимость строительства военно-морских баз | Н/Д |
| `production_cost_nuclear_reactor_factor` | Меняет стоимость строительства ядерных реакторов | Н/Д |
| `production_cost_offices_factor` | Меняет стоимость строительства офисных комплексов | Н/Д |
| `production_cost_radar_station_factor` | Меняет стоимость строительства радарных станций | Н/Д |
| `production_cost_rail_way_factor` | Меняет стоимость строительства железных дорог | Н/Д |
| `production_cost_rocket_site_factor` | Меняет стоимость строительства ракетных площадок | Н/Д |
| `production_cost_supply_node_factor` | Меняет стоимость строительства узлов снабжения | Н/Д |
| `production_cost_synthetic_refinery_factor` | Меняет стоимость строительства инфраструктуры возобновляемых источников энергии | Н/Д |

<a id="industry-income-taxes"></a>
### Налоги на доходы промышленности

| Модификатор | Описание | Примечание |
|---|---|---|
| `office_park_income_tax_modifier` | Меняет доход от офисных комплексов | Н/Д |
| `agriculture_district_income_tax_modifier` | Меняет доход от с/х районов | Н/Д |
| `dockyard_income_tax_modifier` | Меняет доход от верфей | Н/Д |
| `rub_ref_income_tax_modifier` | Меняет доход от резиновых заводов | Н/Д |
| `military_industry_tax_modifier` | Меняет доход от военной промышленности | Н/Д |
| `civilian_industry_tax_modifier` | Меняет доход от гражданской промышленности | Н/Д |
| `agriculture_tax_modifier` | Меняет доход от сельского хозяйства | Н/Д |

<a id="small-businesses"></a>
### Малый бизнес

| Модификатор | Описание | Примечание |
|---|---|---|
| `small_businesses_tax_modifier` | Множитель максимальных налогов с малого бизнеса | Н/Д |
| `small_businesses_productivity_modifier` | Прибавляет ВВП, который генерирует малый бизнес | Н/Д |
| `small_businesses_workers_modifier` | Прибавляет % работников малого бизнеса | Н/Д |

<a id="companies-branches"></a>
### Компании и филиалы

| Модификатор | Описание | Примечание |
|---|---|---|
| `companies_workers_ammount_modifier` | Сколько рабочих мест даёт конкретная компания | Прописывается в идее компании |
| `companies_salary_modifier` | Зарплата конкретной компании (% от ВВП/ДН) | Прописывается в идее компании |
| `branches_workers_ammount_modifier` | Сколько рабочих мест даёт конкретный филиал | Прописывается в идее филиала |
| `branches_salary_modifier` | Зарплата конкретного филиала (% от ВВП/ДН) | Прописывается в идее филиала |
| `companies_salary_multiplier_modifier` | Меняет зарплату всех компаний | В процентах |
| `branches_salary_multiplier_modifier` | Меняет зарплату всех филиалов | В процентах |
| `companies_workers_ammount_multiplier_modifier` | Меняет число работников всех компаний | В процентах |
| `branches_workers_ammount_multiplier_modifier` | Меняет число работников всех филиалов | В процентах |
| `companies_tax_gain_multiplier_modifier` | Меняет налоги с компаний | + или − в процентах |
| `branches_tax_gain_multiplier_modifier` | Меняет налоги с филиалов | + или − в процентах |

<a id="campaign-costs"></a>
### Стоимость кампаний

| Модификатор | Описание | Примечание |
|---|---|---|
| `salafist_outlook_campaign_cost_modifier` | Меняет цену кампании салафитской индоктринации | Н/Д |
| `nonaligned_outlook_campaign_cost_modifier` | Меняет цену кампании неприсоединившихся | Н/Д |
| `western_outlook_campaign_cost_modifier` | Меняет цену кампании западной ориентации | Н/Д |
| `emerging_outlook_campaign_cost_modifier` | Меняет цену кампании развивающейся ориентации | Н/Д |
| `nationalist_outlook_campaign_cost_modifier` | Меняет цену кампании националистов | Н/Д |
| `propaganda_campaign_cost_modifier` | Меняет цену всех пропагандистских кампаний | Н/Д |

<a id="investment-modifiers"></a>
### Модификаторы инвестиций

| Модификатор | Описание | Примечание |
|---|---|---|
| `investment_duration_modifier` | Меняет длительность исходящих инвестиций | Н/Д |
| `receiving_investment_duration_modifier` | Меняет длительность входящих инвестиций | Н/Д |
| `investment_cost_modifier` | Меняет стоимость исходящих инвестиций | Н/Д |
| `receiving_investment_cost_modifier` | Меняет стоимость входящих инвестиций | Н/Д |
| `internal_investments_pp_cost_modifier` | Меняет цену внутр. инвестиций в PP | Н/Д |
| `internal_investments_money_cost_modifier` | Меняет цену внутр. инвестиций в деньгах | Н/Д |
| `return_on_investment_modifier` | Меняет норму доходности инвестиций | 0,02 = +2% к доходности |

<a id="workforce-labor"></a>
### Рабочая сила и труд

| Модификатор | Описание | Примечание |
|---|---|---|
| `total_workforce_modifier` | Меняет размер рабочей силы для строительства | Н/Д |
| `high_unemployment_threshold_modifier` | Меняет порог штрафа за высокую безработицу | Н/Д |
| `base_unemployment_modifier` | Модификатор базовой безработицы | Например -0,05 = влияние на 5% меньше |
| `agriculture_workers_modifier` | Меняет число работников для сельского хозяйства | Н/Д |
| `resource_sector_workers_modifier` | Меняет число работников для ресурсных секторов | Н/Д |
| `civ_facs_worker_requirement_modifier` | Меняет число работников для гражд. фабрики | Н/Д |
| `mil_facs_worker_requirement_modifier` | Меняет число работников для воен. фабрики/верфи | Н/Д |
| `rub_ref_worker_requirement_modifier` | Меняет число работников для резинового завода | Н/Д |
| `offices_worker_requirement_modifier` | Меняет число работников для офисного комплекса | Н/Д |
| `agriculture_district_worker_requirement_modifier` | Меняет число работников для с/х районов | Н/Д |
| `buildings_worker_requirement_modifier` | Меняет число работников для всех построек | Н/Д |

<a id="upgrade-special-costs"></a>
### Стоимость улучшений и специальных действий

| Модификатор | Описание | Примечание |
|---|---|---|
| `econ_cycle_upg_cost_multiplier_modifier` | Меняет стоимость улучшения экон. цикла | Н/Д |
| `leased_civilian_factories_cost_modifier` | Меняет стоимость аренды гражданских фабрик | + или − в процентах |
| `leased_civilian_factories_income_modifier` | Меняет доход от сданных в аренду гражданских фабрик | + или − в процентах |
| `leased_military_factories_cost_modifier` | Меняет стоимость аренды военных фабрик | + или − в процентах |
| `leased_dockyards_cost_modifier` | Меняет стоимость аренды верфей | + или − в процентах |
