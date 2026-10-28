---
title: Департаменты и компании
description: "Эффекты для отображения тултипов об открытии новых департаментов, компаний и филиалов"
---

## Эффекты департаментов, компаний и филиалов

Если вам нужно показать в тултипе фокуса, что открывается новый департамент или компания, используйте `custom_effect_tooltip` вместе с `show_ideas_tooltip`, указав идею нужного департамента/компании.

<a id="new-department"></a>
### Новый департамент

```
custom_effect_tooltip = available_new_departament
show_ideas_tooltip = GDR_shtazi_idea
```

<a id="new-company"></a>
### Новая компания

```
custom_effect_tooltip = available_new_company
show_ideas_tooltip = GDR_Deutsche_Reichsbahn_idea
```

<a id="new-branch"></a>
### Новый филиал

Для филиалов синтаксис немного другой — вместо прямого значения используется `localization_key`, а сам филиал передаётся через `BRANCH_NAME`.

```
custom_effect_tooltip = {
    localization_key = available_new_branch
    BRANCH_NAME = POR_salvador_caetano_branch
}
```
