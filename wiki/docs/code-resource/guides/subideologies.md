---
title: Субидеологии и партии
description: "Добавление партий и субидеологий"
---

## MDC: как добавить партии субидеологий

Добавление политических партий — отличный способ добавить нового колорита странам без больших затрат труда!

Чтобы партии отображались в игре, нужно отредактировать несколько файлов.

- `common/scripted_localisation/subideology_scripted_localisation.txt`
- `localisation/english/[название]_parties_l_english.yml` (и `..._l_russian.yml` для русской версии)
- `interface/parties_icons.gfx`
- Иконки партий хранятся в `gfx/texticons/parties_icons/nation_name`
- Кастомные лидеры хранятся в `common/scripted_effects/[TAG]_political_leaders.txt`

Всё довольно просто, но нужно точно следовать тегам, как они написаны.

:::tip
Полный список слотов субидеологий (индексы `party_index` 0–23, теги, названия) перенесён в справочник — см. [Системы → Политика → Субидеологии](../../systems/politics/#subideologies).
:::

_**КАК ЭТО СДЕЛАТЬ**_

:::caution
Ниже — исправленное описание после сверки с реальным `subideology_scripted_localisation.txt`. Раньше здесь было написано, что нужно «добавить три отдельных ключа локализации» — это **неточно** и могло запутать. На деле для каждой субидеологии (`conservatism`, `Nat_Autocracy` и т.д.) уже существует **один общий** `defined_text`-блок на все ~190 стран игры — вы не создаёте новый блок, а **дописываете туда одну строку** для своего тега.
:::

Для каждой субидеологии в `subideology_scripted_localisation.txt` есть **три** таких общих блока: `{subideology}_L` (название + иконка в одной строке UI), `{subideology}_L_desc` (описание) и `{subideology}_L_icon` (иконка отдельно). Внутри каждого — список `text = { trigger = {...} localization_key = ... }`, по одной строке (а то и по нескольку) на каждую страну, и в конце — общий вариант по умолчанию (`generic.<subideology>`), если ни одно условие не подошло. Блок читается **сверху вниз, срабатывает первое подходящее условие** — поэтому строку для своей страны нужно вставить где угодно **до** общего варианта по умолчанию (обычно — по тегу в алфавитном порядке рядом с соседями).

**Пример на СССР/России (тег `SOV`, субидеология `conservatism`):**

```
# внутри defined_text { name = conservatism_L ... }
text = { trigger = { original_tag = SOV } localization_key = SOV.conservatism }

# внутри defined_text { name = conservatism_L_desc ... }
text = { trigger = { original_tag = SOV } localization_key = SOV.conservatism_desc }

# внутри defined_text { name = conservatism_L_icon ... }
text = { trigger = { original_tag = SOV } localization_key = SOV.conservatism_icon }
```

Сам текст (`SOV.conservatism`, `SOV.conservatism_desc`, `SOV.conservatism_icon`) задаётся уже обычной строкой в `.yml`-локализации:

```yaml
SOV.conservatism: "£SOV_western_conservative (СПС) Союз правых сил"
SOV.conservatism_icon: "£SOV_western_conservative"
SOV.conservatism_desc: "(Свободный рыночный либерализм) Союз правых сил...\n\nОписание партии."
```

`£SOV_western_conservative` — это не сам файл иконки, а имя `spriteType`, зарегистрированного в `interface/parties_icons.gfx` (именно туда вы добавляете новый `spriteType` со ссылкой на .dds-файл, лежащий в `gfx/texticons/parties_icons/{tag}`). Значок `£` подставляет иконку прямо внутри строки текста.

### Несколько вариантов названия для одной страны (по дате/флагу/косметическому тегу)

У одной страны для одной субидеологии может быть **несколько** `text`-строк в общем блоке — какая именно сработает, решает `trigger`. Реальный пример на Армении (три взаимоисключающих варианта партии `conservatism`):

```
text = { trigger = { original_tag = ARM has_country_flag = ARM_cons_first } localization_key = ARM.conservatism_alt }
text = { trigger = { original_tag = ARM has_country_flag = ARM_cons_second } localization_key = ARM.conservatism_alty }
text = { trigger = { original_tag = ARM NOT = { OR = { has_country_flag = ARM_cons_first has_country_flag = ARM_cons_second } } } localization_key = ARM.conservatism }
```

Кроме `has_country_flag` и `date <`/`date >` (самые частые варианты), встречается и **`has_cosmetic_tag`** — например, у СССР партия `socialism` меняет название, если у страны включён косметический тег «реставрации СССР»:

```
text = { trigger = { original_tag = SOV has_cosmetic_tag = SOV_USSR_AUTH_S } localization_key = SOV.socialism_dem }
text = { trigger = { original_tag = SOV NOT = { has_cosmetic_tag = SOV_USSR_AUTH_S } } localization_key = SOV.socialism }
```

То есть в фокусе/эффекте, который выставляет `set_cosmetic_tag = SOV_USSR_AUTH_S`, обычно сразу следом вызывается `update_party_name = yes` — это принудительно обновляет уже отображаемое название партии в интерфейсе прямо сейчас, а не ждёт следующего цикла (например, выборов), когда игра сама перечитает `defined_text`.

Этот же принцип (несколько строк + условие) — **основной и самый частый** в моде способ сделать «партия меняет название по ходу игры». Вариант через встроенный `set_party_name` (см. раздел ниже) тоже работает, но используется реже — он не требует заранее прописанных вариантов в локализации, зато и не позволяет красиво завязать смену на конкретные условия сценария без ручного вызова эффекта в нужный момент.

Следующий шаг — реализовать иконки в файле интерфейса партий. Сначала нужно сохранить иконки партий в формате .dds в `gfx/texticons/parties_icons/{tag}`. Затем переходите к `interface/parties_icons.gfx` и реализуйте новый `spriteType` по аналогии с другими примерами — именно на его имя (без префикса `GFX_`) ссылается `£` в локализации выше.

Если вы правильно выполнили эти шаги, ваши партии теперь должны корректно отображаться в игре.

Новые политические лидеры немного сложнее и требуют больше деталей для корректной настройки в игре. Для начала нужно сохранить портреты в `gfx/leaders/{tag}` в формате .dds или .tga. После этого переходим к `common/scripted_effects/{tag}_political_leaders.txt`.

Есть несколько моментов, которые нужно учитывать. В зависимости от идеологии лидера, нужно задать её, заменив set_Nat_Autocracy на set_{subideology}. Это относит лидера к нужной субидеологии, к которой принадлежит конкретный персонаж. Единственное, что нужно добавить, если лидер не должен быть доступен после определённого условия или даты — это
`if = { limit = { date < 2016.1.2 } set_temp_variable = { b = 1 } } #пропустить, если 2017`. Эта строка определяет, будет ли лидер пропущен в следующий раз, когда он должен прийти к власти.

```
if = { limit = { has_country_flag = set_Nat_Autocracy }
		if = { limit = { check_variable = { Nat_Autocracy_leader = 0 } }
			add_to_variable = { Nat_Autocracy_leader = 1 }
			hidden_effect = { kill_country_leader = yes }

			create_country_leader = {
				name = "Clifford Husbands"
				picture = "generic.dds"
				ideology = Nat_Autocracy
				traits = {
					nationalist_Nat_Autocracy
				}
			}

			if = { limit = { has_country_flag = do_not_retire } subtract_from_variable = { Nat_Autocracy_leader = 1 } }
			if = { limit = { date < 2016.1.2 } set_temp_variable = { b = 1 } } #пропустить, если 2017
		}
		if = { limit = { check_variable = { Nat_Autocracy_leader = 1 } NOT = { check_variable = { b = 1 } } }
			add_to_variable = { Nat_Autocracy_leader = 1 }
			hidden_effect = { kill_country_leader = yes }

			create_country_leader = {
				name = "Sandra Mason"
				picture = "sandra_mason.dds"
				ideology = Nat_Autocracy
				traits = {
					nationalist_Nat_Autocracy
				}
			}

			if = { limit = { has_country_flag = do_not_retire } subtract_from_variable = { Nat_Autocracy_leader = 1 } }
			set_temp_variable = { b = 1 }
		}
	}
```

## Как переименовать уже существующую партию

Это два разных вопроса — «поменять название партии навсегда для всех» и «переименовать её только для одной страны или только в рамках конкретного фокуса/ивента, во время игры».

### Навсегда (для всех стран, у которых нет своего варианта)

Внутри общего блока `defined_text { name = {subideology}_L ... }` (см. выше) самая последняя строка — без `trigger`, вида `text = { localization_key = generic.{subideology} }`. Именно она отображается всем странам, для которых нет отдельной строки по тегу. Меняете текст по ключу `generic.{subideology}` в `.yml`-локализации — и общее название меняется везде, где нет странового переопределения.

Если же нужно переименовать конкретную существующую партию конкретной страны навсегда — правите не общий ключ, а `.yml`-строку по её собственному ключу (`SOV.conservatism` и т.д.), которая уже подставляется через `text = { trigger = { original_tag = SOV } ... }` в общем блоке.

### Только для одной страны

Это ровно тот механизм, что описан в примере с Арменией выше — своя строка `text = { trigger = { original_tag = TAG ... } localization_key = TAG.{subideology} }` в общем блоке плюс своя запись в `.yml`. Если у страны такой строки ещё нет (она просто показывает `generic.{subideology}`) — добавляете новую строку по тегу, ориентируясь на соседние примеры (ARM, SOV, SPR, FRA и другие).

:::note
Как выбранный текст физически попадает в UI: эффект `update_party_name` (файл `00_subideology_scripted_effects.txt`) вызывает родной эффект движка `set_party_name`, где `name`/`long_name` берутся из скриптовой локализации `[show_ruling_party]` — то есть `defined_text`-блоки, описанные выше (`{subideology}_L` и т.д.), не показываются напрямую, а сначала прогоняются через `show_ruling_party`, а затем уже присваиваются партии через `set_party_name`. Для правки текста партии это ничего не меняет — редактируете `{subideology}_L`/`.yml`-строки, как описано выше, просто имейте в виду, что между вашей строкой локализации и тем, что видит игрок, есть этот промежуточный шаг.
:::

### Динамически во время партии (по условию или через эффект)

Два способа, оба рабочие:

**1. Заранее прописанные варианты + условие** (см. раздел выше про СССР/`has_cosmetic_tag` и Армению/`has_country_flag`) — это основной способ в этом моде. Нужно заранее прописать все варианты названия в `.yml`, и переключение происходит само, когда меняется `date`/флаг/косметический тег. Если переключение должно случиться немедленно (не ждать следующих выборов) — сразу после установки условия (флага, косметического тега и т.д.) вызывайте `update_party_name = yes`.

**2. Родной эффект `set_party_name`** (с версии HOI4 1.9, работает в любом моде, включая MDC) — не требует заранее прописанных вариантов в общем `defined_text`-блоке, название задаётся прямо в моменте:

```
set_party_name = {
	ideology = conservatism
	name = MY_NEW_PARTY_NAME_SHORT
	long_name = MY_NEW_PARTY_NAME_LONG
}
```

- `ideology` — тег субидеологии (та же строка, что в `party_index`/`ruling_party`, например `conservatism`, `liberalism`, `Nat_Autocracy`)
- `name` / `long_name` — ключи локализации (короткое и полное название); должны быть определены в любом `.yml` файле локализации, как обычный текст
- Работает даже после сохранения игры, действует у любого игрока в мультиплеере
- Чтобы новое название подхватилось в интерфейсе, вкладку «Политика» нужно закрыть и открыть заново
- Никакие ванильные/модовые файлы при этом не перезаписываются — эффект просто временно переопределяет название поверх того, что задано в локализации через `defined_text`
