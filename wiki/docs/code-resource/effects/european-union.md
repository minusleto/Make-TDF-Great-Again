---
title: Европейский союз
description: "Эффекты Евросоюза и евроскептицизма"
---

## Эффекты Европейского союза MDC

<a id="euroscepticism-effects"></a>
### Эффекты евроскептицизма

Чтобы добавить/убрать евроскептицизм, достаточно:

```
set_temp_variable = { modify_eurosceptic = 0.05 }
set_temp_variable = { modify_eurosceptic_target = THIS }
eurosceptic_change = yes
```

Вместо "THIS" можно использовать любое из следующего:

- THIS
- ROOT
- PREV
- FROM
- Любой тег страны (например, GER)

Чтобы этот эффект применился ко _всем_ текущим странам ЕС:

```
set_temp_variable = { modify_eurosceptic = -0.05 }
EU_eurosceptic_change = yes
```

И наконец, чтобы эффект применился к _текущим_ и _потенциальным_ членам ЕС:

```
set_temp_variable = { modify_eurosceptic = -0.05 }
EU_potential_eurosceptic_change = yes
```
