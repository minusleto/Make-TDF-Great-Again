---
title: Сепаратизм и терроризм
description: "Изменение уровня сепаратизма, поддержка терроризма и накопление террористической активности"
---

## Эффекты сепаратизма и терроризма

<a id="separatism"></a>
## Сепаратизм

<a id="separatism-support"></a>
### Изменение сепаратизма

Работает как переменная `separatism` у конкретного тега (0–100), меняется через `set_temp_variable` + вызов общего эффекта:

```txt
set_temp_variable = { modify_separatism = 1 }
modify_separatism_support = yes
```

Значение переменной — это изменение (+/-), а не итоговая цифра. Ограничено диапазоном `1`–`100`.

Доступно только для тегов сепаратистских/потенциально сепаратистских регионов — их довольно много по всему миру, не только Россия:

`ADJ` `ADY` `ALA` `ALT` `ARA` `ASK` `BAY` `BDA` `BLR` `BRY` `BSH` `CAL` `CAT` `CHE` `CHU` `CKK` `CNR` `CRE` `CRM` `DAG` `DPR` `DRU` `EST` `ETK` `FLN` `GAL` `GDR` `GGZ` `GRL` `HUN` `ING` `KAS` `KBK` `KCC` `KHM` `KHS` `KLM` `KOM` `KRP` `LAT` `LIT` `LOR` `MEL` `MIL` `NAP` `NAV` `NEE` `PIE` `PKK` `RGD` `RHE` `RSK` `SAZ` `SCO` `SIC` `SIL` `SLA` `SLO` `SPA` `TAM` `TAT` `TEX` `TIB` `TLS` `TRC` `TUS` `TUV` `UDM` `VNC` `VOJ` `YAK` `YAM` `ZAP`

:::note
При достижении высоких значений (обычно >75) у тега запускается собственный сценарий сепаратистского восстания/событий — свой для каждого тега. Это отдельная, специфичная для каждого региона логика, не общий эффект.
:::

<hr/>

<a id="terrorism"></a>
## Терроризм

<a id="terrorism-support"></a>
### Поддержка терроризма

Доступно только для указанных тегов.

**Коммунистические:** `ITA`, `GER`, `NOR`, `CZE`, `HUN`, `AUS`  
**Другие террористические:** `SYR`, `IRQ`, `SAU`, `UAE`, `EGY`, `NIG`, `ALG`, `TUN`, `TAJ`, `ING`, `KBK`, `KCC`, `DAG`, `CHE`, `ARW`

```txt
set_temp_variable = { modify_terrorism = 1 }
modify_terrorism_support = yes
```

Поддержка терроризма ограничена значением `100`.

<a id="terrorism-mana"></a>
### Накопление террористической активности

Изменяет накопление террористической активности страны.

```txt
add_to_variable = { terrorism_mana = 10 }
clamp_variable = {
    var = terrorism_mana
    min = 1
    max = 100
}
```
