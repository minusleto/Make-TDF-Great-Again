---
title: Военные модификаторы
description: "Справочник ванильных военных модификаторов HOI4: сухопутный бой, флот, авиация, техника и лицензии, снабжение, опыт и командование."
---

## Военные модификаторы

<a id="combat"></a>
### Боевые (сухопутные)

Ванильные модификаторы HOI4, применяются к дивизиям страны.

| Модификатор | Описание |
|---|---|
| `army_speed_factor` | Скорость движения дивизий |
| `army_attack_speed_factor` | Скорость, с которой сухопутная армия атакует |
| `army_org_factor` | Максимальная организация войск (%) |
| `army_org` | Максимальная организация войск (плоский бонус) |
| `army_org_regain` | Скорость восстановления организации |
| `army_morale_factor` | Скорость восстановления организации после боя |
| `army_defence_factor` | Защита дивизий |
| `army_defence_against_major_factor` | Защита против великих держав |
| `army_defence_against_minor_factor` | Защита против стран, не являющихся великими державами |
| `army_core_defence_factor` | Защита на своих кор-территориях |
| `army_claim_defence_factor` | Защита на территориях с претензией |
| `army_attack_factor` | Атака дивизий |
| `army_attack_against_major_factor` | Бонус атаки против великих держав |
| `army_attack_against_minor_factor` | Бонус атаки против стран, не являющихся великими державами |
| `army_claim_attack_factor` | Атака на территориях, на которые есть претензия |
| `army_non_core_attack_factor` | Атака на не-национальных территориях |
| `army_strength_factor` | Общая сила сухопутных войск |
| `army_experience_from_volunteers` | Получение армейского опыта от добровольцев |
| `air_superiority_bonus_in_combat` | Влияние превосходства в воздухе на наземный бой |
| `breakthrough_factor` | Пробивная способность (breakthrough) |
| `army_breakthrough_against_major_factor` | Пробивная способность против великих держав |
| `army_breakthrough_against_minor_factor` | Пробивная способность против стран, не являющихся великими державами |
| `recon_factor` | Разведка (recon) дивизий |
| `recon_factor_while_entrenched` | Разведка в окопавшемся состоянии |
| `coordination_bonus` | Бонус координации войск |
| `combat_width_factor` | Ширина боевого построения дивизии |
| `max_planning_factor` | Максимальный уровень планирования |
| `planning_speed` | Скорость набора планирования |
| `dig_in_speed` / `dig_in_speed_factor` | Скорость окапывания (плоский / %) |
| `terrain_penalty_reduction` | Снижение штрафов от местности |
| `pocket_penalty` | Штраф войскам в окружении |
| `cas_damage_reduction` | Снижение урона от штурмовой авиации (CAS) |
| `special_forces_cap` | Максимальная доля спецназа в армии |
| `special_forces_min` | Минимальное число спецназа, не учитываемое в лимите |
| `training_time_army_factor` / `training_time_factor` | Время обучения новых дивизий (первое — только сухопутные, второе — общее) |
| `non_core_manpower` | Доля доступного мобрезерва на не-кор территориях |

<a id="naval-combat"></a>
### Боевые (морские)

| Модификатор | Описание |
|---|---|
| `naval_speed_factor` | Скорость кораблей |
| `naval_damage_factor` | Наносимый флотом урон |
| `naval_defense_factor` | Снижение получаемого кораблями урона |
| `naval_accidents_chance` | Вероятность морских аварий и случайной потери кораблей |
| `naval_critical_score_chance_factor` | Шанс нанести критическое повреждение |
| `naval_critical_effect_factor` | Сила последствий критических повреждений |
| `critical_receive_chance` | Шанс получить критическое повреждение |
| `naval_enemy_fleet_size_ratio_penalty_factor` | Снижение штрафа при численном превосходстве вражеского флота |
| `naval_night_attack` | Урон флота в ночное время |
| `naval_defense_factor` | Защита кораблей |
| `naval_detection` | Обнаружение кораблей |
| `naval_enemy_retreat_chance` | Шанс вынудить вражеский флот отступить |
| `naval_retreat_chance` / `naval_retreat_speed` | Шанс / скорость отступления флота |
| `naval_ship_recovery_chance_factor` | Вероятность спасения корабля после боя |
| `naval_torpedo_damage_reduction_factor` / `naval_torpedo_enemy_critical_chance_factor` | Снижение урона торпед / снижение шанса критического урона от торпед |
| `naval_torpedo_reveal_chance_factor` | Модификатор обнаружения торпедной атаки |
| `naval_light_gun_hit_chance_factor` / `naval_heavy_gun_hit_chance_factor` | Шанс попадания лёгких / тяжёлых орудий |
| `naval_hit_chance` | Шанс попадания в бою |
| `naval_coordination` | Координация флота |
| `convoy_escort_efficiency` | Эффективность эскортирования конвоев |
| `convoy_retreat_speed` | Скорость отступления конвоев |
| `naval_retreat_chance_after_initial_combat` | Шанс отступления флота после начальной фазы боя |
| `naval_mines_effect_reduction` | Снижение урона от вражеских морских мин |
| `mines_planting_by_fleets_factor` / `mines_sweeping_by_fleets_factor` | Эффективность постановки / траления мин флотом |
| `experience_gain_navy_unit` | Плоский прирост опыта корабельных подразделений |
| `naval_has_potf_in_combat_attack` / `naval_has_potf_in_combat_defense` | Атака / защита флота при участии «гордости флота» |
| `strike_force_movement_org_loss` | Потеря организации при движении в режиме ударного соединения |
| `sub_retreat_speed` / `submarine_attack` | Скорость отступления / атака подлодок |
| `naval_morale` / `naval_morale_factor` | Мораль флота (плоский / %) |
| `naval_retreat_chance` / `naval_retreat_speed` | Шанс и скорость отступления флота |
| `ships_at_battle_start` | Число кораблей, вступающих в бой в первом контакте |
| `spotting_chance` | Шанс обнаружить вражеские корабли |
| `navy_anti_air_attack` / `navy_anti_air_attack_factor` | Зенитная атака флота (плоский / %) |
| `navy_capital_ship_attack_factor` / `navy_capital_ship_defence_factor` | Атака/защита капитальных кораблей |
| `navy_screen_attack_factor` / `navy_screen_defence_factor` | Атака/защита кораблей охранения (screen) |
| `navy_submarine_attack_factor` / `navy_submarine_defence_factor` | Атака/защита подлодок |
| `navy_submarine_detection_factor` | Шанс обнаружения вражеских подлодок |
| `convoy_raiding_efficiency_factor` | Эффективность рейдерства против конвоев |
| `naval_torpedo_hit_chance_factor` | Шанс попадания торпед |
| `naval_torpedo_cooldown_factor` | Перезарядка торпед |
| `naval_mine_hit_chance` / `naval_mines_damage_factor` | Шанс попадания и урон от мин |
| `naval_invasion_capacity` / `naval_invasion_penalty` | Вместимость и штраф морского десанта |
| `amphibious_invasion` | Скорость исполнения морского десанта |
| `invasion_preparation` | Время подготовки морского десанта |

<a id="carriers"></a>
### Авианосцы

| Модификатор | Описание |
|---|---|
| `navy_carrier_air_attack_factor` | Атака самолётов с авианосцев |
| `navy_carrier_air_agility_factor` | Манёвренность самолётов с авианосцев |
| `navy_carrier_air_targetting_factor` | Точность самолётов с авианосцев |
| `air_carrier_night_penalty_reduction_factor` | Снижение ночного штрафа для авиации с авианосцев |
| `carrier_capacity_penalty_reduction` | Снижение штрафа за перегрузку авианосца самолётами |
| `carrier_traffic` / `carrier_night_traffic` | Пропускная способность авианосца (общая / ночью) |
| `sortie_efficiency` / `fighter_sortie_efficiency` | Скорость дозаправки/перевооружения самолётов на авианосце (общая / для истребителей) |

<a id="air-combat"></a>
### Боевые (воздушные)

| Модификатор | Описание |
|---|---|
| `air_accidents_factor` | Шанс авиакатастроф |
| `air_cas_efficiency` | Эффективность непосредственной авиационной поддержки |
| `air_escort_efficiency` | Эффективность сопровождения самолётов |
| `air_wing_xp_loss_when_killed_factor` | Потеря опыта авиакрыла при уничтожении самолётов |
| `ground_attack_factor` | Урон авиации по наземным дивизиям |
| `mines_planting_by_air_factor` / `mines_sweeping_by_air_factor` | Эффективность постановки / траления мин авиацией |
| `strategic_bomb_visibility` | Заметность стратегических бомбардировщиков для противника |
| `rocket_attack_factor` | Атака ракет |
| `air_night_penalty` | Штраф за ночные вылеты |
| `air_weather_penalty` | Штраф за плохую погоду |
| `army_bonus_air_superiority_factor` | Бонус наземным войскам от превосходства в воздухе |
| `enemy_army_bonus_air_superiority_factor` | То же самое, но противнику |
| `air_interception_attack_factor` / `_defence_factor` / `_agility_factor` | Атака/защита/манёвренность при перехвате |
| `air_air_superiority_attack_factor` / `_defence_factor` / `_agility_factor` | То же самое для миссий на превосходство в воздухе |
| `air_close_air_support_attack_factor` / `_defence_factor` / `_agility_factor` | То же самое для непосредственной поддержки войск (CAS) |
| `air_strategic_bomber_attack_factor` / `_defence_factor` / `_agility_factor` / `_bombing_factor` | То же самое для стратегических бомбардировщиков (включая эффективность бомбардировки) |
| `air_cas_present_factor` | Эффективность тактических бомбардировок |
| `naval_strike_attack_factor` / `_targetting_factor` / `_agility_factor` | Атака/точность/манёвренность при ударах по кораблям с воздуха |
| `air_paradrop_attack_factor` / `_defence_factor` / `_agility_factor` | То же самое для десантированных парашютом войск |
| `air_ace_generation_chance_factor` | Шанс появления асов |
| `experience_gain_air` / `experience_gain_air_factor` | Прирост опыта авиации (плоский / %) |

<a id="intelligence"></a>
### Разведка и шифрование

| Модификатор | Описание |
|---|---|
| `decryption_power` | Мощность дешифрования (плоский бонус) |
| `decryption_power_factor` | Мощность дешифрования (%) |
| `defense_impact_on_blueprint_stealing` | Защита от кражи чертежей техники |
| `intel_from_combat_factor` | Прирост разведданных от боевых действий |
| `intel_from_operatives_factor` | Прирост разведданных от агентов |
| `intel_network_gain` | Прирост сети разведки в регионе |


<a id="equipment-licensing"></a>
### Захват, конверсия и модернизация техники

| Модификатор | Описание |
|---|---|
| `equipment_capture` | Базовый (плоский) бонус к доле захваченной у противника техники |
| `equipment_capture_factor` | Процентный модификатор доли захваченной техники |
| `equipment_conversion_speed` | Скорость конверсии одного типа техники в другой |
| `equipment_upgrade_xp_cost` | Общий модификатор стоимости опыта для улучшения техники |
| `land_equipment_upgrade_xp_cost` | Стоимость армейского опыта для улучшения сухопутной техники |
| `naval_equipment_upgrade_xp_cost` | Стоимость морского опыта для улучшения кораблей |
| `air_equipment_upgrade_xp_cost` | Стоимость воздушного опыта для улучшения самолётов |
| `refit_ic_cost` | Стоимость промышленной мощности для переоборудования корабля |
| `refit_speed` | Скорость переоборудования кораблей |

<a id="license-modifiers"></a>
### Производственные лицензии

| Модификатор | Описание |
|---|---|
| `license_purchase_cost` | Стоимость покупки производственной лицензии |
| `license_production_speed` | Скорость производства техники по лицензии |
| `license_tech_difference_speed` | Изменение штрафа к производству из-за разницы в технологиях |
| `license_anti_tank_eq_cost_factor` | Стоимость лицензии на противотанковое вооружение |
| `license_anti_tank_eq_production_speed_factor` | Скорость производства лицензионного противотанкового вооружения |
| `license_anti_tank_eq_tech_difference_speed_factor` | Штраф за разницу технологий для лицензионного противотанкового вооружения |
| `license_artillery_eq_cost_factor` | Стоимость лицензии на артиллерию |
| `license_artillery_eq_production_speed_factor` | Скорость производства лицензионной артиллерии |
| `license_artillery_eq_tech_difference_speed_factor` | Штраф за разницу технологий для лицензионной артиллерии |
| `license_infantry_eq_cost_factor` | Стоимость лицензии на пехотное снаряжение |
| `license_infantry_eq_production_speed_factor` | Скорость производства лицензионного пехотного снаряжения |
| `license_infantry_eq_tech_difference_speed_factor` | Штраф за разницу технологий для лицензионного пехотного снаряжения |
| `license_light_tank_eq_cost_factor` | Стоимость лицензии на лёгкие танки |
| `license_light_tank_eq_production_speed_factor` | Скорость производства лицензионных лёгких танков |
| `license_light_tank_eq_tech_difference_speed_factor` | Штраф за разницу технологий для лицензионных лёгких танков |
| `license_armor_purchase_cost` / `license_air_purchase_cost` / `license_naval_purchase_cost` | Стоимость лицензии на бронетехнику / авиацию / морскую технику |

<a id="production-efficiency"></a>
### Эффективность военного производства

| Модификатор | Описание |
|---|---|
| `production_factory_efficiency_gain_factor` | Скорость накопления эффективности военного производства |
| `production_factory_max_efficiency_factor` | Максимальный уровень эффективности военного производства |
| `production_factory_start_efficiency_factor` | Начальный уровень эффективности производственной линии |
| `line_change_production_efficiency_factor` | Сохранение эффективности при смене производимой техники |
| `production_cost_max_ship_hull_light` / `production_cost_max_ship_hull_heavy` / `production_cost_max_ship_hull_cruiser` / `production_cost_max_ship_hull_carrier` / `production_cost_max_ship_hull_submarine` | Модификаторы максимальной стоимости соответствующих типов кораблей |

<a id="supply-logistics"></a>
### Снабжение, топливо и истощение

| Модификатор | Описание |
|---|---|
| `supply_consumption_factor` | Изменяет расход снабжения войсками |
| `out_of_supply_factor` | Изменяет штрафы войск, оставшихся без снабжения |
| `army_fuel_capacity_factor` | Модификатор запаса топлива сухопутных войск |
| `fuel_gain` / `fuel_gain_factor` | Плоский / процентный прирост топлива |
| `supply_node_range` | Дальность снабжения от узлов снабжения |
| `army_fuel_consumption_factor` | Расход топлива сухопутными войсками |
| `air_fuel_consumption_factor` | Расход топлива авиацией |
| `navy_fuel_consumption_factor` | Расход топлива флотом |
| `attrition` | Изменение потерь от истощения |
| `winter_attrition_factor` | Изменение истощения зимой |
| `heat_attrition_factor` | Изменение истощения в жарком климате |

<a id="experience-training"></a>
### Опыт и подготовка

| Модификатор | Описание |
|---|---|
| `experience_gain_army` | Плоский бонус к получаемому опыту армии |
| `experience_gain_army_factor` | Процентный бонус к получаемому опыту армии |
| `experience_gain_navy` | Плоский бонус к получаемому опыту флота |
| `experience_gain_navy_factor` | Процентный бонус к получаемому опыту флота |
| `experience_gain_navy_unit_factor` | Бонус к получению опыта корабельными подразделениями |
| `experience_gain_army_unit` / `experience_gain_army_unit_factor` | Плоский / процентный прирост опыта сухопутных подразделений |
| `land_reinforce_rate` | Скорость поступления подкреплений в сухопутный бой |
| `max_dig_in` | Максимальный уровень окопанности |

<a id="command-power"></a>
### Командование и мобилизация

| Модификатор | Описание |
|---|---|
| `command_power_gain` | Ежедневный прирост командной мощи (плоский) |
| `command_power_gain_mult` | Процентный модификатор прироста командной мощи |
| `max_command_power` | Максимальный запас командной мощи |
| `max_command_power_mult` | Процентный модификатор максимального запаса командной мощи |
| `conscription` | Изменение доли населения, доступного для призыва (плоское) |
| `conscription_factor` | Процентный модификатор доли населения, доступного для призыва |
| `weekly_manpower` | Дополнительная еженедельная людская сила |

<a id="unit-type-bonuses"></a>
### Бонусы отдельным типам войск

| Модификатор | Описание |
|---|---|
| `special_forces_attack_factor` | Атака дивизий спецназа |
| `special_forces_defence_factor` | Защита дивизий спецназа |
| `motorized_attack_factor` | Атака моторизованных войск |
| `motorized_defence_factor` | Защита моторизованных войск |
| `army_core_attack_factor` | Атака на национальных территориях |
| `army_core_defence_factor` | Защита на национальных территориях |
| `army_infantry_attack_factor` / `army_infantry_defence_factor` | Атака / защита пехоты |
| `army_armor_attack_factor` / `army_armor_defence_factor` / `army_armor_speed_factor` | Атака / защита / скорость бронетехники |
| `army_artillery_attack_factor` / `army_artillery_defence_factor` | Атака / защита артиллерии |
| `motorized_attack_factor` / `motorized_defence_factor` | Атака / защита моторизованных войск |
| `mechanized_attack_factor` / `mechanized_defence_factor` | Атака / защита механизированных войск |
| `cavalry_attack_factor` / `cavalry_defence_factor` | Атака / защита кавалерии |

<a id="air-general"></a>
### Общие характеристики авиации

| Модификатор | Описание |
|---|---|
| `air_attack_factor` | Общий модификатор атаки авиации |
| `air_defence_factor` | Общий модификатор защиты авиации |
| `air_agility_factor` | Общий модификатор манёвренности авиации |
| `ace_effectiveness_factor` | Эффективность бонусов асов |
| `air_ace_bonuses_factor` | Модификатор бонусов, предоставляемых асами |

<a id="vanilla"></a>
### Общие

| Модификатор | Описание | Примечание |
|---|---|---|
| `war_support_factor` | Меняет военную поддержку | Н/Д |
| `war_support_weekly` | Еженедельный прирост военной поддержки | Н/Д |
| `war_support_weekly_factor` | Еженедельный прирост военной поддержки (%) | Н/Д |
| `war_stability_factor` | Штраф стабильности от нахождения в состоянии войны | Н/Д |
| `offensive_war_stability_factor` | Штраф стабильности за участие в наступательной войне | Н/Д |
| `defensive_war_stability_factor` | Штраф стабильности за участие в оборонительной войне | Н/Д |
| `weekly_casualties_war_support` | Военная поддержка от еженедельных потерь | Н/Д |
| `weekly_convoys_war_support` | Военная поддержка от потопленных конвоев | Н/Д |
| `weekly_bombing_war_support` | Военная поддержка от бомбёжек наших регионов | Н/Д |
| `surrender_limit` | Меняет % столиц/ВП, которые нужно потерять для капитуляции | Н/Д |
| `ammo_consumption_modifier` | Меняет расход боеприпасов войсками | Н/Д |

<a id="military-bases"></a>
### Военные базы

| Модификатор | Описание | Примечание |
|---|---|---|
| `military_bases_leader_modifier` | Бафф конкретному лидеру от военных баз | + или − в процентах |
| `military_bases_country_modifier` | Бафф всем лидерам страны от военных баз | + или − в процентах |
