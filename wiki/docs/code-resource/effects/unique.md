---
title: Уникальные
description: "Эффекты, которые реально работают только для конкретных стран — завязаны на уникальную механику, существующую только там"
---

## Уникальные эффекты

Эффекты, которые технически можно прописать где угодно, но реально они срабатывают только для конкретных стран — потому что завязаны на механику, которая существует только там. Общий список соответствующих модификаторов — в [Уникальные модификаторы](../../modifiers/unique/).

<a id="britain"></a>
## Британия

Меняют уникальные модификаторы поддержки парламента Британии (ENG) — см. [Уникальные модификаторы → Британия](../../modifiers/unique/#britain). Значение переменной — это изменение (+/-), а не итоговая цифра.

Изменить поддержку заднескамеечников:

```
set_temp_variable = { eng_backbenchers_sup_change = -15 }
ENG_backbenchers_support_change = yes
```

Изменить поддержку оппозиции (Палата общин):

```
set_temp_variable = { eng_house_of_commons_sup_change = -15 }
ENG_house_of_commons_support_change = yes
```

Изменить поддержку Палаты лордов:

```
set_temp_variable = { eng_house_of_lords_sup_change = -15 }
ENG_lords_support_change = yes
```

<a id="russia"></a>
## Россия

Изменить экономическое восстановление РФ (SOV). Значение переменной — это изменение (+/-), а не итоговая цифра.

```
set_temp_variable = { modify_economic = 1 }
modify_economic_support = yes
```

<a id="cartels"></a>
## Картели

Эффект системы картелей, используемый для изменения силы картеля и его политического влияния.

Перед вызовом эффекта задаются временные переменные:

- `cart_strength_change` — изменение силы картеля.
- `cart_influence_change` — изменение политического влияния картеля.

Значения могут быть положительными или отрицательными.

```text
set_temp_variable = { cart_strength_change = 2 }
set_temp_variable = { cart_influence_change = 2 }
modify_cartel_variables_effect = yes
```

`modify_cartel_variables_effect` применяет изменения, заданные в этих переменных.
