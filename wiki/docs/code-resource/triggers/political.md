---
title: Политика
description: "Скриптовые триггеры политической системы MDC: партии, коалиции, идеологические блоки, пороги популярности."
---

## Базовая идеология страны

Ванильный триггер `has_government = <тег>` работает как обычно, принимает любой из 5 тегов идеологий MDC:

```
has_government = democratic   # Западники
has_government = communism    # Реакционеры (в файлах ещё называются "emerging")
has_government = neutrality   # Нейтралы
has_government = nationalist  # Националисты
has_government = fascism      # Салафиты (в файлах ещё называются "totalitarian/caliphate")
```

Соответствие тегов группам и полный список субидеологий (0–23) — см. [Системы → Политика](../../systems/politics/#subideologies).

## Партия у власти / в коалиции

Помимо `is_in_array = { ruling_party = N }` (сырая проверка индекса), для каждой из 24 субидеологий заведён именованный триггер с тултипом — их и стоит использовать в скриптах.

```
western_liberals_are_in_power = yes
```

Чтобы проверить **обратное** («партии нет у власти»), в моде заведён отдельный именованный триггер — не нужно оборачивать в `NOT` вручную:

```
western_liberals_are_not_in_power = yes
```

Полная таблица таких триггеров — сразу под основной, в подразделе [«Партия не у власти / не в коалиции»](#партия-не-у-власти--не-в-коалиции) ниже. Единственный случай, где готового триггера нет и нужен `NOT` — «не в коалиции» сама по себе (без учёта того, у власти партия или нет), об этом сказано в сноске к той таблице.

⚠️ **Баг в исходнике мода**: у партии 12 (Умеренные исламисты) в файле `00_political_triggers.txt` триггер «у власти или в коалиции» назван `salafist_caliphate_in_power_or_coalition_TT` — явно скопирован с соседнего триггера партии 11 (Салафитский джихадизм) и не переименован. Правильного по конвенции имени (`neutrality_neutral_muslim_brotherhood_in_power_or_coalition` или похожего) для этой партии в моде не существует — используйте `salafist_caliphate_in_power_or_coalition_TT`, как бы странно оно ни звучало.

<div style="overflow:auto; max-height:70vh; border:1px solid #444">
<table style="width:100%; border-collapse:collapse; font-size:0.82em; line-height:1.25">
<thead>
<tr style="background:#2d2d2d; color:#fff; position:sticky; top:0"><th style="padding:3px 8px; text-align:left; width:2.5em">#</th><th style="padding:3px 8px; text-align:left">Партия</th><th style="padding:3px 8px; text-align:left">У власти</th><th style="padding:3px 8px; text-align:left">В коалиции</th><th style="padding:3px 8px; text-align:left">У власти или в коалиции</th></tr>
</thead>
<tbody>
<tr><td colspan="5" style="padding:3px 8px; background:#5B9BD5; color:#000; font-weight:600">Западники (0–3)</td></tr>
<tr style="background:#5B9BD5; color:#000"><td style="padding:2px 8px">0</td><td style="padding:2px 8px">Прозападные автократы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_autocrats_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_autocrats_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_autocrats_are_in_power_or_coalition</code></td></tr>
<tr style="background:#5B9BD5; color:#000"><td style="padding:2px 8px">1</td><td style="padding:2px 8px">Консерваторы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_conservatism_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_conservatism_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_conservatism_are_in_power_or_coalition</code></td></tr>
<tr style="background:#5B9BD5; color:#000"><td style="padding:2px 8px">2</td><td style="padding:2px 8px">Либералы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_liberals_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_liberals_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_liberal_are_in_power_or_coalition</code></td></tr>
<tr style="background:#5B9BD5; color:#000"><td style="padding:2px 8px">3</td><td style="padding:2px 8px">Социал-демократы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_social_democrats_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_social_democrats_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_socialism_are_in_power_or_coalition</code></td></tr>
<tr><td colspan="5" style="padding:3px 8px; background:#70AD47; color:#000; font-weight:600">Реакционеры (4–9)</td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px">4</td><td style="padding:2px 8px">Коммунисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_communist_state_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_communist_state_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_communist_state_in_power_or_coalition</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px">5</td><td style="padding:2px 8px">Левые радикалы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_anarchist_communism_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_anarchist_communism_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_anarchist_communism_in_power_or_coalition</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px">6</td><td style="padding:2px 8px">Реакционеры</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_reactionaries_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_reactionaries_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_conservative_in_power_or_coalition</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px">7</td><td style="padding:2px 8px">Автократы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_autocracy_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_autocracy_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_autocracy_in_power_or_coalition</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px">8</td><td style="padding:2px 8px">Умеренные шиитские революционеры</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_moderate_shiite_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_moderate_shiite_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_mod_vilyat_e_faqih_in_power_or_coalition</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px">9</td><td style="padding:2px 8px">Жёсткие шиитские революционеры</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_hardline_shiite_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_hardline_shiite_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_vilayat_e_faqih_in_power_or_coalition</code></td></tr>
<tr><td colspan="5" style="padding:3px 8px; background:#757171; color:#000; font-weight:600">Салафизм (10–11)</td></tr>
<tr style="background:#757171; color:#000"><td style="padding:2px 8px">10</td><td style="padding:2px 8px">Ваххабитские монархисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">salafist_kingdom_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">salafist_kingdom_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">salafist_kingdom_in_power_or_coalition</code></td></tr>
<tr style="background:#757171; color:#000"><td style="padding:2px 8px">11</td><td style="padding:2px 8px">Салафитские джихадисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">salafist_caliphate_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">salafist_caliphate_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">salafist_caliphate_in_power_or_coalition</code></td></tr>
<tr><td colspan="5" style="padding:3px 8px; background:#A6A6A6; color:#000; font-weight:600">Неприсоединившиеся (12–19)</td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">12</td><td style="padding:2px 8px">Умеренные исламисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_muslim_brotherhood_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_muslim_brotherhood_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">salafist_caliphate_in_power_or_coalition_TT</code> ⚠️</td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">13</td><td style="padding:2px 8px">Автократы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_autocracy_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_autocracy_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_autocracy_in_power_or_coalition</code></td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">14</td><td style="padding:2px 8px">Консерваторы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_conservatism_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_conservatism_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_conservatism_in_power_or_coalition</code></td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">15</td><td style="padding:2px 8px">Олигархи</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_oligarch_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_oligarch_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_oligarchism_in_power_or_coalition</code></td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">16</td><td style="padding:2px 8px">Либертарианцы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_libertarians_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_libertarians_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_libertarian_in_power_or_coalition</code></td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">17</td><td style="padding:2px 8px">Зелёные</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_green_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_green_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_green_in_power_or_coalition</code></td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">18</td><td style="padding:2px 8px">Социал-демократы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_social_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_social_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_social_in_power_or_coalition</code></td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">19</td><td style="padding:2px 8px">Коммунисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_communism_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_communism_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_communism_in_power_or_coalition</code></td></tr>
<tr><td colspan="5" style="padding:3px 8px; background:#C65911; color:#000; font-weight:600">Националисты (20–23)</td></tr>
<tr style="background:#C65911; color:#000"><td style="padding:2px 8px">20</td><td style="padding:2px 8px">Правые популисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_right_wing_populists_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_right_wing_populists_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_right_wing_populists_are_in_power_or_coalition</code></td></tr>
<tr style="background:#C65911; color:#000"><td style="padding:2px 8px">21</td><td style="padding:2px 8px">Фашисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_fascist_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_fascist_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_fascists_are_in_power_or_coalition</code></td></tr>
<tr style="background:#C65911; color:#000"><td style="padding:2px 8px">22</td><td style="padding:2px 8px">Военные</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_military_junta_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_military_junta_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_military_junta_are_in_power_or_coalition</code></td></tr>
<tr style="background:#C65911; color:#000"><td style="padding:2px 8px">23</td><td style="padding:2px 8px">Монархисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_monarchists_are_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_monarchists_are_in_coalition</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_monarchists_are_in_power_or_coalition</code></td></tr>
</tbody>
</table>
</div>

### Партия не у власти / не в коалиции

В отличие от позитивных триггеров, для «не у власти» и «ни у власти, ни в коалиции» в моде реально заведены отдельные именованные триггеры — используем их. Для «не в коалиции» отдельного триггера нет, там `NOT`-обёртка (см. сноску).

<div style="overflow:auto; max-height:70vh; border:1px solid #444">
<table style="width:100%; border-collapse:collapse; font-size:0.82em; line-height:1.25">
<thead>
<tr style="background:#2d2d2d; color:#fff; position:sticky; top:0"><th style="padding:3px 8px; text-align:left; width:2.5em">#</th><th style="padding:3px 8px; text-align:left">Партия</th><th style="padding:3px 8px; text-align:left">Не у власти</th><th style="padding:3px 8px; text-align:left">Не в коалиции¹</th><th style="padding:3px 8px; text-align:left">Ни у власти, ни в коалиции</th></tr>
</thead>
<tbody>
<tr><td colspan="5" style="padding:3px 8px; background:#5B9BD5; color:#000; font-weight:600">Западники (0–3)</td></tr>
<tr style="background:#5B9BD5; color:#000"><td style="padding:2px 8px">0</td><td style="padding:2px 8px">Прозападные автократы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_autocrats_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { western_autocrats_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_autocrats_are_not_in_power_or_coalition</code></td></tr>
<tr style="background:#5B9BD5; color:#000"><td style="padding:2px 8px">1</td><td style="padding:2px 8px">Консерваторы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_conservatism_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { western_conservatism_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_conservative_are_not_in_power_or_coalition</code></td></tr>
<tr style="background:#5B9BD5; color:#000"><td style="padding:2px 8px">2</td><td style="padding:2px 8px">Либералы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_liberals_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { western_liberals_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_liberal_are_not_in_power_or_coalition</code></td></tr>
<tr style="background:#5B9BD5; color:#000"><td style="padding:2px 8px">3</td><td style="padding:2px 8px">Социал-демократы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_social_democrats_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { western_social_democrats_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">western_socialism_are_not_in_power_or_coalition</code></td></tr>
<tr><td colspan="5" style="padding:3px 8px; background:#70AD47; color:#000; font-weight:600">Реакционеры (4–9)</td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px">4</td><td style="padding:2px 8px">Коммунисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_communist_state_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { emerging_communist_state_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_communist_state_not_in_power_or_coalition</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px">5</td><td style="padding:2px 8px">Левые радикалы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_anarchist_communism_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { emerging_anarchist_communism_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_anarchist_communism_not_in_power_or_coalition</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px">6</td><td style="padding:2px 8px">Реакционеры</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_reactionaries_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { emerging_reactionaries_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_conservative_not_in_power_or_coalition</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px">7</td><td style="padding:2px 8px">Автократы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_autocracy_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { emerging_autocracy_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_autocracy_not_in_power_or_coalition</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px">8</td><td style="padding:2px 8px">Умеренные шиитские революционеры</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_moderate_shiite_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { emerging_moderate_shiite_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_mod_vilyat_e_faqih_not_in_power_or_coalition</code></td></tr>
<tr style="background:#70AD47; color:#000"><td style="padding:2px 8px">9</td><td style="padding:2px 8px">Жёсткие шиитские революционеры</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_hardline_shiite_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { emerging_hardline_shiite_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">emerging_vilayat_e_faqih_not_in_power_or_coalition</code></td></tr>
<tr><td colspan="5" style="padding:3px 8px; background:#757171; color:#000; font-weight:600">Салафизм (10–11)</td></tr>
<tr style="background:#757171; color:#000"><td style="padding:2px 8px">10</td><td style="padding:2px 8px">Ваххабитские монархисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">salafist_kingdom_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { salafist_kingdom_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">salafist_kingdom_not_in_power_or_coalition</code></td></tr>
<tr style="background:#757171; color:#000"><td style="padding:2px 8px">11</td><td style="padding:2px 8px">Салафитские джихадисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">salafist_caliphate_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { salafist_caliphate_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">salafist_caliphate_not_in_power_or_coalition</code></td></tr>
<tr><td colspan="5" style="padding:3px 8px; background:#A6A6A6; color:#000; font-weight:600">Неприсоединившиеся (12–19)</td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">12</td><td style="padding:2px 8px">Умеренные исламисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_muslim_brotherhood_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { neutrality_neutral_muslim_brotherhood_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_muslim_brotherhood_not_in_power_or_coalition</code></td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">13</td><td style="padding:2px 8px">Автократы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_autocracy_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { neutrality_neutral_autocracy_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_autocracy_not_in_power_or_coalition</code></td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">14</td><td style="padding:2px 8px">Консерваторы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_conservatism_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { neutrality_neutral_conservatism_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutral_conservative_are_not_in_power_or_coalition</code></td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">15</td><td style="padding:2px 8px">Олигархи</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_oligarch_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { neutrality_neutral_oligarch_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_oligarchism_not_in_power_or_coalition</code></td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">16</td><td style="padding:2px 8px">Либертарианцы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_libertarians_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { neutrality_neutral_libertarians_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_libertarian_not_in_power_or_coalition</code></td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">17</td><td style="padding:2px 8px">Зелёные</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_green_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { neutrality_neutral_green_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_green_not_in_power_or_coalition</code></td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">18</td><td style="padding:2px 8px">Социал-демократы</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_social_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { neutrality_neutral_social_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_social_not_in_power_or_coalition</code></td></tr>
<tr style="background:#A6A6A6; color:#000"><td style="padding:2px 8px">19</td><td style="padding:2px 8px">Коммунисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_communism_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { neutrality_neutral_communism_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">neutrality_neutral_communism_not_in_power_or_coalition</code></td></tr>
<tr><td colspan="5" style="padding:3px 8px; background:#C65911; color:#000; font-weight:600">Националисты (20–23)</td></tr>
<tr style="background:#C65911; color:#000"><td style="padding:2px 8px">20</td><td style="padding:2px 8px">Правые популисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_right_wing_populists_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { nationalist_right_wing_populists_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_right_wing_populists_are_not_in_power_or_coalition</code></td></tr>
<tr style="background:#C65911; color:#000"><td style="padding:2px 8px">21</td><td style="padding:2px 8px">Фашисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_fascist_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { nationalist_fascist_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_fascists_are_not_in_power_or_coalition</code></td></tr>
<tr style="background:#C65911; color:#000"><td style="padding:2px 8px">22</td><td style="padding:2px 8px">Военные</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_military_junta_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { nationalist_military_junta_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_military_junta_are_not_in_power_or_coalition</code></td></tr>
<tr style="background:#C65911; color:#000"><td style="padding:2px 8px">23</td><td style="padding:2px 8px">Монархисты</td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_monarchists_are_not_in_power</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">NOT = { nationalist_monarchists_are_in_coalition = yes }</code></td><td style="padding:2px 8px"><code style="background:rgba(255,255,255,.55); color:#000; padding:1px 5px; border-radius:4px">nationalist_monarchists_are_not_in_power_or_coalition</code></td></tr>
</tbody>
</table>
</div>

¹ Для «не в коалиции» отдельно (без учёта того, у власти партия или нет) выделенного триггера в исходниках нет — используется `NOT = { <партия>_are_in_coalition = yes }`.

:::caution
В исходниках встречаются несогласованные окончания (`western_liberal_are_in_power_or_coalition` вместо `_liberals_`, `emerging_conservative_...` вместо `_reactionaries_`, `nationalist_fascist_...` вместо `_fascists_`) — это не опечатка в доке, так буквально называются триггеры в моде. Копируйте имена из таблицы, не по аналогии с соседними строками.
:::

## Идеологические блоки (по кластеру взглядов)

Группируют несколько партий по общей политической позиции — то, что реально стоит проверять в решениях/фокусах, вместо перечисления индивидуальных `is_in_array`.

| Позиция | У власти | В коалиции | У власти или в коалиции | Партии (индексы) |
|---|---|---|---|---|
| Социалисты | `has_socialist_government` | `has_socialist_in_coalition` | `has_socialist_government_or_in_coalition` | 3, 4, 5, 18, 19 |
| Коммунисты | `has_communist_government` | `has_communist_in_coalition` | `has_communist_government_or_in_coalition` | 4, 5, 19 |
| Экологи | `has_environmentalist_government` | `has_environmentalist_in_coalition` | `has_environmentalist_government_or_in_coalition` | 17 (в коалиции — ещё и 5) |
| Либералы | `has_liberal_government` | `has_liberal_in_coalition` | `has_liberal_government_or_in_coalition` | 2, 16, 17 |
| Консерваторы | `has_conservative_government` | `has_conservative_in_coalition` | `has_conservative_government_or_in_coalition` | 0, 1, 6, 7, 10, 11, 12, 13, 14, 15, 20, 21, 22, 23 |
| Реакционеры | `has_reactionary_government` | `has_reactionary_in_coalition`¹ | `has_reactionary_government_or_in_coalition` | 0, 7, 10, 11, 13, 15, 20, 21, 22, 23 |
| Автократы | `has_autocratic_government` | `has_autocratic_in_coalition` | `has_autocratic_government_or_in_coalition` | 0, 4, 7, 9, 10, 11, 13, 15, 19, 20, 21, 22, 23 |
| Тоталитаристы | `has_totalitarian_government` | `has_totalitarian_in_coalition` | `has_totalitarian_government_or_in_coalition` | 4, 11, 21 |
| Экономически либеральные | `has_economically_liberal_government` | `has_economically_liberal_in_coalition` | `has_economically_liberal_government_or_in_coalition`² | 1, 2, 14, 16 |

¹ Для индекса 0 (Прозападные автократы) вариант «в коалиции» дополнительно требует `NOT = { has_country_leader_with_trait = western_technocrat }` — технократ-лидер выводит партию из числа реакционных даже формально.
² `has_economically_liberal_government_or_in_coalition` — это `OR` из двух предыдущих триггеров, а не отдельный список индексов.

Отдельно: `has_not_environmentalist_government_or_in_coalition` — инверсия `has_environmentalist_government_or_in_coalition` (готовый, не через `NOT` снаружи).

## Идеологический блок целиком (5 групп)

Совпадает по границам индексов с группами из [Системы → Политика](../../systems/politics/#subideologies):

| Триггер | Индексы | Инверсия |
|---|---|---|
| `has_western_aligned_government` | 0–3 | `not_has_western_aligned_government` |
| `has_emerging_aligned_government` | 4–9 | `not_has_emerging_aligned_government` |
| `has_salafist_government` | 10–11 | — |
| `has_neutral_government` | 12–19 | — |
| `has_nationalist_government` | 20–23 | — |

## Общественное настроение по группе (outlook)

Проверяет не правящую партию, а общий уровень поддержки идеологического блока (`party_popularity@<тег>`), даже если у власти другая партия:

```
democratic_outlook_larger_than_0 = yes
```

| Триггер | Тег идеологии |
|---|---|
| `democratic_outlook_larger_than_0` | `democratic` |
| `emerging_outlook_larger_than_0` | `communism` |
| `fascism_outlook_larger_than_0` | `fascism` |
| `neutrality_outlook_larger_than_0` | `neutrality` |
| `nationalist_outlook_larger_than_0` | `nationalist` |

## Фракции влияния

```
has_economic_faction = yes
```

| Триггер | Проверяет наличие идеи |
|---|---|
| `has_economic_faction` | `small_medium_business_owners`, `international_bankers`, `fossil_fuel_industry`, `industrial_conglomerates`, `oligarchs`, `landowners`, `maritime_industry`, `defense_industry`, а также нация-специфичные `wall_street`, `chaebols`, `the_donju` |
| `has_religious_faction` | `the_priesthood`, `the_ulema`, `the_clergy`, `wahabi_ulema` |

## Пороги популярности

### Сила правящей коалиции

`government_coalition_strength` — суммарная популярность правящей партии + союзников. Готовые пороги:

`10_percent_government_popularity`, `20_percent_government_popularity`, `30_percent_government_popularity`, `35_percent_government_popularity`, `40_percent_government_popularity`, `50_percent_government_popularity`, `60_percent_government_popularity`, `66_percent_government_popularity`, `70_percent_government_popularity`, `80_percent_government_popularity`, `90_percent_government_popularity`

(число в названии — реальный порог минус 0.001, т.е. `check_variable = { government_coalition_strength > 0.099 }` и т.д.)

### Пороги отдельных партий

| Триггер | Партия (индекс) | Порог |
|---|---|---|
| `35_percent_emerging_communist_state_popularity` | Формирующиеся коммунисты (4) | > 35% |
| `35_percent_neutral_communist_popularity` | Коммунисты (19) | > 35% |
| `35_percent_nationalist_right_wing_populists_popularity` | Правые популисты (20) | > 35% |
| `35_percent_nationalist_nat_autocracy_popularity` | Военная хунта (22) | > 35% |
| `35_percent_nationalist_absolutist_monarchist_popularity` | Абсолютные монархисты (23) | > 35% |
| `45_percent_nationalist_nat_autocracy_popularity` | Военная хунта (22) | > 45% |

### Порог явки на выборы, по каждой партии

`party_0_has_more_than_threshold` … `party_23_has_more_than_threshold` — проверяет `party_pop_array^N > election_threshold` для соответствующего индекса N (0–23, см. таблицу субидеологий). Используется, чтобы понять, преодолела ли партия заградительный барьер для участия в выборах/коалиции, независимо от того, у власти она сейчас или нет.

## Есть ли у партии пространство для роста

`party_N_is_not_maxed` (N = 0–23) — проверяет, что популярность конкретной партии **не равна** суммарной популярности всего её идеологического блока, т.е. внутри блока есть ещё другие партии с ненулевой поддержкой (партия не «съела» весь блок целиком):

```
party_2_is_not_maxed = yes
```

Индекс N — тот же party_index (0–23), тег идеологии в проверке подставляется автоматически под нужный блок (democratic/communism/neutrality/nationalist/fascism) в зависимости от N.

## Служебные (параметризованные) триггеры/эффекты

Эти блоки не предназначены для прямого копирования в контент мода — они принимают вход через `party_index` или `ruling_party` и используются внутри других скриптов избирательной системы:

- **`is_party_banned_trigger`** — принимает `party_index` (temp-переменная), возвращает `yes`, если соответствующая партия (флаг `partyN_banned`) запрещена.
- **`outlook_larger_than_0_by_index`** — параметризованная версия блока «Общественное настроение по группе»: сама определяет идеологический блок по диапазону `party_index` (0–3 / 4–9 / 10–11 / 12–19 / 20–23) и вызывает нужный `*_outlook_larger_than_0`.
- **`bigger_than_ruling_elect_zero` … `bigger_than_ruling_elect_twenty_three`** (24 блока) — сравнивает `party_pop_elect_array^N` конкретной партии N с массивом текущей правящей партии; внутренняя логика подсчёта результатов выборов.
- **`calculate_pp_cost_banned_amount`** — на самом деле **эффект**, а не триггер (несмотря на расположение в этом файле): считает стоимость PP за снятие банов со всех незапрещённых партий, кроме правящей.
