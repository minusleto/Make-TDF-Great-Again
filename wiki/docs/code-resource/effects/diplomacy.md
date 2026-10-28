---
title: Дипломатия
description: "Скриптовые эффекты дипломатии, мнения, отношений, влияния и санкций"
---

## Эффекты дипломатии MDC

Раздел содержит именно **эффекты**: команды, которые напрямую меняют дипломатические отношения, мнение, влияние, эмбарго и связанные состояния.

## Мнение и отношения

### Добавить модификатор мнения

`add_opinion_modifier` добавляет модификатор мнения текущей страны о целевой стране.

```txt
add_opinion_modifier = {
    target = ROOT
    modifier = reduced_our_influence
}
```

`target` — страна, о которой меняется мнение. `modifier` — имя модификатора мнения из `common/opinion_modifiers`.

### Удалить модификатор мнения

`remove_opinion_modifier` удаляет модификатор мнения с указанной страны.

```txt
remove_opinion_modifier = {
    target = ROOT
    modifier = reduced_our_influence
}
```

### Добавить обратный модификатор мнения

`reverse_add_opinion_modifier` добавляет модификатор мнения в обратном направлении.

```txt
reverse_add_opinion_modifier = {
    target = ROOT
    modifier = reduced_our_influence
}
```

### Добавить модификатор отношений

`add_relation_modifier` добавляет статический модификатор между текущей страной и целевой страной.

```txt
add_relation_modifier = {
    target = ROOT
    modifier = my_relation_modifier
}
```

### Удалить модификатор отношений

`remove_relation_modifier` удаляет статический модификатор отношений.

```txt
remove_relation_modifier = {
    target = ROOT
    modifier = my_relation_modifier
}
```

## Дипломатические отношения

### Установить или отменить дипломатическое отношение

`diplomatic_relation` создаёт или отменяет дипломатическое отношение между двумя странами.

```txt
diplomatic_relation = {
    country = ROOT
    relation = military_access
    active = yes
}
```

Чтобы отменить отношение, используется тот же эффект с `active = no`:

```txt
diplomatic_relation = {
    country = ROOT
    relation = military_access
    active = no
}
```

## Влияние

Процентное изменение задаётся целым числом: например, `10` = +10%, `-10` = -10%.

### Внутреннее влияние

`change_domestic_influence_percentage` изменяет **внутреннее влияние** страны, на которой выполняется эффект.

#### Пример: увеличить внутреннее влияние на 10%

```txt
set_temp_variable = { percent_change = 10 }
change_domestic_influence_percentage = yes
```

#### Пример: уменьшить внутреннее влияние на 10%

```txt
set_temp_variable = { percent_change = -10 }
change_domestic_influence_percentage = yes
```

Эффект использует временную переменную `percent_change`. Значение задаётся непосредственно числом без знаков-заполнителей.

### Влияние иностранных сторон

Эта группа управляет **внешним влиянием**: позволяет изменить процент влияния конкретной стороны и выбрать, какая сторона считается влияющей.

#### Изменить процент иностранного влияния

Для `change_influence_percentage` задаются три временные переменные:

- `percent_change` — изменение влияния в процентах;
- `tag_index` — индекс влияющей стороны;
- `influence_target` — страна, на которую направлено влияние.

Поддерживаемые скоупы для `tag_index` и `influence_target`: `FROM`, `ROOT`, `PREV`, `TAG` и другие стандартные скоупы, когда они указывают на нужный тег/страну.

#### Пример: увеличить влияние FROM на ROOT на 10%

```txt
set_temp_variable = { percent_change = 10 }
set_temp_variable = { tag_index = FROM }
set_temp_variable = { influence_target = ROOT }
change_influence_percentage = yes
```

#### Пример: уменьшить влияние FROM на ROOT на 10%

```txt
set_temp_variable = { percent_change = -10 }
set_temp_variable = { tag_index = FROM }
set_temp_variable = { influence_target = ROOT }
change_influence_percentage = yes
```

:::caution
Если у 7-й влияющей стороны уже больше влияния, чем величина вашего `percent_change`, целевая страна может получить прирост внутреннего влияния вместо прироста влияния вашей стороны. Например, если у 7-й стороны 5%, а изменение составляет 3%, вместо прироста вашего влияния целевая страна получает внутреннее влияние.
:::

### Изменить индекс влияющей стороны

`change_current_influencer_index_percentage` изменяет индекс текущей влияющей стороны.

```txt
set_temp_variable = { percent_change = 10 }
set_temp_variable = { influencer_index = 3 }
change_current_influencer_index_percentage = yes
```

`influencer_index` принимает индекс влияющей стороны в диапазоне `0`–`6`.

:::note
Индекс `0`–`6` выбирает конкретную позицию в списке влияющих сторон. Если тебе нужно изменить именно процент влияния между двумя странами, используй `change_influence_percentage`.
:::

## Санкции и эмбарго

### Повысить сопротивление санкциям

`custom_effect_tooltip = sanctions_resistance_tt` показывает подсказку об увеличении сопротивления санкциям, а `add_to_variable` увеличивает счётчик `quarters_since_sanctions`.

```txt
custom_effect_tooltip = sanctions_resistance_tt
add_to_variable = { quarters_since_sanctions = 5 }
```

**Важно:** максимальное значение сопротивления санкциям — **75**. Учитывайте текущее значение счётчика и не повышайте его сверх этого предела.

### Наложить санкции на другую страну

Эффект `issued_sanctions_prev = yes` отмечает, что страна наложила санкции на целевую страну. Во вложенном скоупе внешний тег — страна, которая вводит санкции, внутренний — цель.

Пример: США накладывают санкции на Бирму (`BRM`):

```txt
USA = {
    BRM = {
        issued_sanctions_prev = yes
    }
}
```

### Отозвать санкции

Эффект `revoke_sanctions = yes` снимает санкции с целевой страны.

Пример: США снимают санкции с Кубы (`CUB`):

```txt
USA = {
    CUB = {
        revoke_sanctions = yes
    }
}
```


### Наложить эмбарго

`send_embargo` накладывает эмбарго на указанную страну.

```txt
send_embargo = ROOT
```

### Снять эмбарго

`break_embargo` снимает существующее эмбарго между текущей страной и указанной страной.

```txt
break_embargo = ROOT
```

:::note
`break_embargo` должен выполняться со стороны страны, которая наложила эмбарго.
:::

### Подготовка санкций (по цели)

Перед самим наложением санкций страна ставит себе временный флаг-метку «санкции против конкретной цели подготовлены», используя динамическое имя флага с тегом цели через `@`:

```
FRA = {
	set_country_flag = {
		flag = sanctions_prepared@NIG
		value = 1
		days = 365
	}
}
```

Здесь Франция получает флаг `sanctions_prepared@NIG` — «санкции против Нигерии подготовлены» — со сроком действия 365 дней (`value = 1` просто отмечает флаг как установленный). Подставляйте нужный тег цели вместо `NIG`, чтобы флаг был именно про эту страну — `@TAG` в конце имени делает флаг уникальным для пары «санкционирующая страна ↔ цель», а не общим на всю страну.

Проверяется обычным `has_country_flag = sanctions_prepared@NIG` (см. [Базовые триггеры](../../triggers/basic/) про синтаксис флагов).

## Дипломатические ограничения

### Добавить переопределение правила отношений

`add_relation_rule_override` добавляет переопределение правила отношений для целевой страны.

```txt
add_relation_rule_override = {
    target = ROOT
    can_not_declare_war = yes
}
```

### Удалить переопределение правила отношений

`remove_relation_rule_override` удаляет ранее добавленное переопределение правила.

```txt
remove_relation_rule_override = {
    target = ROOT
    can_not_declare_war = yes
}
```

### Установить правило страны

`set_rule` добавляет правило, которое переопределяет другие правила страны.

```txt
set_rule = {
    can_not_declare_war = yes
}
```
