---
title: Постройки
description: "Стоимость и скриптовые эффекты для зданий"
tableOfContents:
  minHeadingLevel: 2
  maxHeadingLevel: 4
---

## Стоимость построек MDC

Стоимость ниже — то, что реально списывается через готовые MDC scripted effects (`one_random_*` / `one_state_*` и т.д.) из `common\\scripted_effects\\00_scripted_effects.txt`. Для построек, которые занимают строительный слот, указанная стоимость уже включает стоимость самого слота.

### Промышленность

| Постройка | ID | Стоимость |
|---|---|---:|
| [Гражданская промышленность](#гражданская-фабрика) | `industrial_complex` | $3.75 |
| [Военная промышленность](#военная-фабрика) | `arms_factory` | $3.75 |
| [Верфь](#верфь) | `dockyard` | $3.75 |
| [Офисы](#офисы)* | `offices` | $6.00 |
| [Коммерческий сельскохозяйственный район](#коммерческий-сельскохозяйственный-район) | `agriculture_district` | $1.875 |

\* Эффекты офисов всегда дают в комплекте ещё и электростанцию на ископаемом топливе — $6.00 это стоимость связки, а не только офисов отдельно.

### Инфраструктура и связь

| Постройка | ID | Стоимость |
|---|---|---:|
| [Инфраструктура](#инфраструктура) | `infrastructure` | $1.75 |
| Туристическая инфраструктура | `tourism_infrastructure` | $0.600 |
| Культурная инфраструктура | `culture_infrastructure` | $0.600 |
| [Авиабаза](#авиабазы) | `air_base` | $1.25 |
| [Сетевая инфраструктура](#сетевая-инфраструктура) | `internet_station` | $1.50 |
| Железные дороги | `rail_way` | $0.01 за провинцию |

### Энергетика и топливо

| Постройка | ID | Стоимость |
|---|---|---:|
| [Инфраструктура возобновляемых источников энергии](#инфраструктура-возобновляемых-источников-энергии) | `synthetic_refinery` | $4.25 |
| [Резиновый завод](#резиновый-завод) | `rubber_refinery` | $1.75 |
| [Топливное хранилище](#топливное-хранилище) | `fuel_silo` | $1.50 |
| [Электростанция на ископаемом топливе](#электростанция-на-ископаемом-топливе) | `fossil_powerplant` | $1.625 |
| [Ядерный реактор](#ядерный-реактор) | `nuclear_reactor` | $4.50 |

### Оборона

| Постройка | ID | Стоимость |
|---|---|---:|
| [ЗРК](#зрк) | `anti_air_building` | $1.625 |
| [Радарная станция](#радарная-станция) | `radar_station` | $0.50 |
| Региональная оборонительная сеть | `stronghold_network` | $8.00 |
| Сухопутный форт | `bunker` | $0.50 за уровень |
| Береговой бункер | `coastal_bunker` | $0.50 за уровень |

### Специальные и провинциальные постройки

| Постройка | ID | Стоимость |
|---|---|---:|
| Пусковая площадка ракет | `rocket_site` | $3.00 |
| [Объект военно-морских исследований](#научно-исследовательские-объекты) | `naval_facility` | $7.50 |
| [Объект сухопутных исследований](#научно-исследовательские-объекты) | `land_facility` | $7.50 |
| [Объект аэродинамики и авионики](#научно-исследовательские-объекты) | `air_facility` | $7.50 |
| [Гражданский научно-исследовательский объект](#научно-исследовательские-объекты) | `nuclear_facility` | $7.50 |
| Военно-морская база | `naval_base` | $0.50 за уровень |
| Узел снабжения | `supply_node` | $2.50 |

**Минимальная стоимость строительного слота: $1.00 за слот.**

### Ресурсы

В MDC 8 единиц ресурсов соответствуют одной гражданской фабрике. Поэтому добавление 1 единицы стали обходится стране в $0.938 млрд по стандарту MDC. Ниже показан принцип расчёта стоимости ресурсов через казну.

```text
capital_scope = {
    add_resource = {
        type = steel
        amount = 4
    }
}
set_temp_variable = { treasury_change = -3.75 }
modify_treasury_effect = yes
```

<a id="mdc-building-effects"></a>

## Как добавить здание

Для стандартных построек MDC используйте готовые scripted effects из `common\\scripted_effects\\00_scripted_effects.txt`. Они уже содержат необходимую логику добавления здания и его стоимости.

Есть два основных варианта:

- `one_random_*`, `two_random_*`, `three_random_*`, `four_random_*` — добавить постройку в случайные подходящие регионы.
- `one_state_*`, `two_state_*`, `three_state_*`, `four_state_*` — добавить постройку в конкретный регион.

Эффекты `one_state_*` и другие `*_state_*` должны использоваться внутри scope нужного региона.

### Бесплатное добавление здания

Если нужно добавить здание напрямую, без списания стоимости через scripted effect MDC, используйте `add_building_construction`. Параметр `instant_build = yes` завершает строительство сразу.

Шаблон:

```text
add_building_construction = {
    type = industrial_complex
    level = 1
    instant_build = yes
}
```

В `type` указывается тот же ID здания, что и в таблицах стоимости в начале страницы (`industrial_complex`, `arms_factory`, `dockyard` и т.д.).

Пример для нескольких уровней:

```text
add_building_construction = {
    type = arms_factory
    level = 3
    instant_build = yes
}
```

Этот способ не использует `treasury_change`: стоимость из таблицы выше относится к платным MDC scripted effects, а `add_building_construction` в таком виде используется для бесплатного прямого добавления.

### Гражданская фабрика

**Случайный регион**

```text
one_random_industrial_complex = yes
two_random_industrial_complex = yes
three_random_industrial_complex = yes
four_random_industrial_complex = yes
```

**Конкретный регион**

```text
one_state_industrial_complex = yes
two_state_industrial_complex = yes
three_state_industrial_complex = yes
four_state_industrial_complex = yes
```

### Военная фабрика

**Случайный регион**

```text
one_random_arms_factory = yes
two_random_arms_factory = yes
three_random_arms_factory = yes
four_random_arms_factory = yes
```

**Конкретный регион**

```text
one_state_arms_factory = yes
two_state_arms_factory = yes
three_state_arms_factory = yes
four_state_arms_factory = yes
```

### Верфь

**Случайный регион**

```text
one_random_dockyard = yes
two_random_dockyards = yes
```

**Конкретный регион**

```text
one_state_dockyard = yes
two_state_dockyards = yes
```

### Офисы

Следующие эффекты также дают электростанцию на ископаемом топливе.

**Случайный регион**

```text
one_office_construction = yes
two_office_construction = yes
three_office_construction = yes
```

**Конкретный регион**

```text
one_state_office_construction = yes
two_state_office_construction = yes
three_state_office_construction = yes
```

### Коммерческий сельскохозяйственный район

**Случайный регион**

```text
one_random_agriculture_district = yes
```

**Конкретный регион**

```text
one_state_agriculture_district = yes
```

### Резиновый завод

**Случайный регион**

```text
one_random_rubber_refinery = yes
two_random_rubber_refinery = yes
three_random_rubber_refinery = yes
```

**Конкретный регион**

```text
one_state_rubber_refinery = yes
two_state_rubber_refinery = yes
three_state_rubber_refinery = yes
```

### Инфраструктура

**Случайный регион**

```text
one_random_infrastructure = yes
two_random_infrastructure = yes
three_random_infrastructure = yes
```

**Конкретный регион**

```text
one_state_infrastructure = yes
two_state_infrastructure = yes
three_state_infrastructure = yes
```

### Туристическая инфраструктура

**Случайный регион**

```text
one_random_tourism_infrastructure = yes
two_random_tourism_infrastructure = yes
three_random_tourism_infrastructure = yes
```

**Конкретный регион**

```text
one_state_tourism_infrastructure = yes
two_state_tourism_infrastructure = yes
three_state_tourism_infrastructure = yes
```

### Культурная инфраструктура

**Случайный регион**

```text
one_random_culture_infrastructure = yes
two_random_culture_infrastructure = yes
three_random_culture_infrastructure = yes
```

**Конкретный регион**

```text
one_state_culture_infrastructure = yes
two_state_culture_infrastructure = yes
three_state_culture_infrastructure = yes
```

### Сетевая инфраструктура

**Случайный регион**

```text
one_random_network_infrastructure = yes
two_random_network_infrastructure = yes
```

**Конкретный регион**

```text
one_state_network_infrastructure = yes
two_state_network_infrastructure = yes
```

### Авиабазы

**Случайный регион**

```text
one_air_base = yes
two_air_base = yes
```

**Конкретный регион**

```text
one_state_air_base = yes
two_state_air_base = yes
```

### Инфраструктура возобновляемых источников энергии

**Случайный регион**

```text
one_random_synthetic_refinery = yes
two_random_synthetic_refinery = yes
three_random_synthetic_refinery = yes
```

**Конкретный регион**

```text
one_state_synthetic_refinery = yes
two_state_synthetic_refinery = yes
three_state_synthetic_refinery = yes
```

### Топливное хранилище

**Случайный регион**

```text
one_fuel_reserve = yes
two_fuel_reserve = yes
```

**Конкретный регион**

```text
one_state_fuel_reserve = yes
two_state_fuel_reserve = yes
```

### Электростанция на ископаемом топливе

Отдельно от офисов — если нужна только электростанция.

**Случайный регион**

```text
one_random_fossil_fuel_powerplant = yes
two_random_fossil_fuel_powerplant = yes
```

**Конкретный регион**

```text
one_state_fossil_fuel_powerplant = yes
two_state_fossil_fuel_powerplant = yes
```

### Ядерный реактор

**Случайный регион**

```text
one_random_nuclear_reactor = yes
two_random_nuclear_reactor = yes
```

**Конкретный регион**

```text
one_state_nuclear_reactor = yes
two_state_nuclear_reactor = yes
```

### ЗРК

**Случайный регион**

```text
one_anti_air = yes
two_anti_air = yes
```

**Конкретный регион**

```text
one_state_anti_air = yes
two_state_anti_air = yes
```

### Радарная станция

**Случайный регион**

```text
one_radar_station = yes
two_radar_station = yes
```

**Конкретный регион**

```text
one_state_radar_station = yes
two_state_radar_station = yes
```

### Научно-исследовательские объекты

Всегда добавляются в случайную провинцию текущего региона (без варианта "конкретный регион"):

```text
one_random_land_facility = yes    # Объект сухопутных исследований
one_random_naval_facility = yes   # Объект военно-морских исследований
one_random_air_facility = yes     # Объект аэродинамики и авионики
one_random_nuclear_facility = yes # Гражданский научно-исследовательский объект
```
