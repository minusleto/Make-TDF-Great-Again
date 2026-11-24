# MIO, equipment and military industry

Справочник для проектирования и технического ревью MIO, вариантов техники, выдачи оборудования и связей с технологиями. Это инструкция для статического аудита; она не заменяет проверку в игре.

## 1. Где искать определения

Индексировать нужно глобально, а не только по файлу текущей страны:

- MIO: `mdredux/common/military_industrial_organization/organizations/**/*.txt`.
- Equipment и archetypes/chassis: `mdredux/common/units/equipment/**/*.txt`, определения находятся внутри `equipments = { ... }`.
- Equipment modules: `mdredux/common/units/equipment/modules/**/*.txt`, внутри `equipment_modules = { ... }`.
- Research technologies: `mdredux/common/technologies/**/*.txt`, внутри `technologies = { ... }`.
- Локализация: все `mdredux/localisation/english/*.yml`, а не один заранее выбранный файл.
- Использования: все focus trees, decisions, events, scripted effects и остальные доступные `mdredux/common/**/*.txt`.

В текущем срезе на 2026-11-24 каталог организаций содержит 57 файлов; английская локализация — 18 YML. Базового Millennium Dawn и полного vanilla/DLC-контента в репозитории нет. Поэтому неизвестный ID не всегда означает ошибку: разделяй локального кандидата и внешнюю зависимость.

## 2. Как устроена MIO

Обычная MIO definition имеет собственный ID и блок с полями вроде:

```hoi4
ENG_bae_land_systems_materiel_manufacturer = {
    allowed = { original_tag = ENG }
    icon = GFX_idea_BAE_Systems
    name = ENG_bae_land_systems_materiel_manufacturer
    include = generic_infantry_equipment_organization
}
```

- ID организации и значение `name` — разные вещи. `name` указывает на ключ локализации; нельзя подставлять ID автоматически.
- `allowed` задаёт допустимость организации для страны; `visible` — дополнительную видимость/гейт. Если `visible` ссылается на `has_completed_focus`, сверяй этот focus ID с деревьями.
- `include` наследует шаблон/профиль организации. По нему часто можно понять специализацию: infantry/materiel, tanks, air, naval, helicopters и специализированные ветки. Не путай тип MIO с конкретным equipment ID.
- `initial_trait`, `trait`, `equipment_bonus`, `production_bonus`, `organization_modifier`, `limit_to_equipment_type`, `ai_will_do` задают дерево и механику развития MIO. Для нового trait проверь родительские связи, взаимоисключения, ограничение оборудования и эффект выбора.
- Повторный `name` key у нескольких MIO может быть намеренным: одна компания может иметь отдельные организации для разных типов оборудования. Это не автоматическая ошибка.
- Но если поле `name` одной организации указывает на ID другой MIO, это сильный кандидат на копипасту. Проверь, действительно ли компания и локализационный ключ совпадают.

В фокусах возможны оба сценария:
```hoi4
unlock_military_industrial_organization_tooltip = mio:KAZ_KPE_tank_manufacturer
mio:KAZ_KPE_tank_manufacturer = {
    add_mio_funds = 500
    add_mio_research_bonus = 0.01
}
```

Первую строку нельзя считать доказательством существования MIO. Сверь сам ID с глобальным индексом. Аналогично, `mio:USA_lockheed_martin_aircraft_manufacturer` в польском или британском дереве может быть корректной ссылкой на иностранную организацию: не объявляй её отсутствующей только потому, что её нет в `MD_POL_organizations.txt` или `MD_ENG_organizations.txt`.

## 3. Equipment, technologies and variants

Equipment ID и technology ID — разные пространства имён.

- Equipment/chassis ID ищи среди direct children блока `equipments`.
- Module ID ищи в `equipment_modules`.
- Technology ID ищи среди direct children `technologies`.
- Equipment type в `create_equipment_variant` и `add_equipment_to_stockpile` должен указывать на equipment/archetype/chassis ID, а не на название технологии.
- В `create_equipment_variant` сверяй `name`, `type`, `parent_version`, `design_team`, `modules`, `upgrades`, `icon`, `model` и `allow_without_tech`. Сверяй module IDs со всем локальным индексом модулей, а `design_team = mio:...` — с общим MIO индексом.
- `allow_without_tech` не следует ставить автоматически: проверяй, зачем вариант выдаётся до исследования базовой техники.
- В `add_equipment_to_stockpile` проверяй `type`, положительное `amount`, `producer` и `variant_name`. `variant_name` — строковое имя варианта, а не обязательно ключ локализации.
- В `create_equipment_variant` обычно используется строковое `name`; не требуй YML-ключ для буквального имени. Не смешивай эти имена с ID оборудования.
- Технологическое ограничение нельзя надёжно вывести только из значения `type`: проверь research tree, связи unlock и `allow_without_tech`. Статический аудит фиксирует инвентарь технологий и неизвестные ID, но не симулирует доступность в интерфейсе.
- Если equipment/module/technology ID не найден в этом срезе, помечай как кандидат на проверку вне репозитория. Не делай ERROR, если определение может быть в базовом MD, vanilla или DLC.

## 4. Откуда берётся производитель

Различай:
- `design_team = mio:...` — назначенная MIO в создаваемом equipment variant;
- `producer = TAG` — страна-производитель в `add_equipment_to_stockpile`;
- `name` / `variant_name` — отображаемое имя варианта.

Не подменяй producer тегом MIO и не подменяй MIO локализационным ключом. Для зарубежной поставки сверяй producer, equipment type и страну-получателя в контексте эффекта/фокуса; статический индекс не может доказать реальную дипломатическую или производственную возможность сделки.

## 5. Что проверяет tdf_audit.py

Глобальный раздел JSON `_industry` и консольная сводка показывают:

- все локальные MIO definitions, ID и name keys; повторные IDs;
- ссылки `mio:ID` во всех доступных common scripts и events, отдельно локальные отсутствующие и внешние;
- локализацию имени MIO, name key, совпадающий с ID другой организации, и MIO visibility focus references;
- equipment/chassis IDs, module IDs и technology IDs;
- `create_equipment_variant`, `design_team`, equipment type, modules и `allow_without_tech`;
- `add_equipment_to_stockpile`: type, amount, producer и variant name;
- кандидатов на неразрешённые equipment/module IDs, локализацию локального equipment и некорректные значения amount.

Отчёты `missing_local` — кандидаты, а не разрешение автоматически менять страновой контент. Внешние зависимости остаются отдельной категорией. Повторный name key не считается ошибкой сам по себе.

## 6. Ручной checklist

1. MIO соответствует реальному производителю и специализации, а её роль не дублирует другую организацию без причины.
2. `allowed` и `visible` делают компанию доступной правильной стране и в правильный момент; фокус не вызывает эффект для MIO, которая не может быть открыта.
3. MIO включена в подходящий шаблон; стартовый trait и дерево развития отражают реальные компетенции производителя.
4. Бонусы и `limit_to_equipment_type` применимы к нужной технике; MIO не даёт бонусы к несвязанным archetypes.
5. Variant type, parent version, module slots, module IDs и upgrades совместимы между собой.
6. Назначенный design team существует и подходит производителю; зарубежные MIO проверены глобально.
7. Технологии, DLC и `allow_without_tech` согласованы с тем, как игрок получает вариант.
8. Stockpile grant выдаёт правильное количество нужного оборудования, с правильными producer и variant name.
9. При описании сделки/поставки recipient, producer, количество и реальные ограничения согласованы с эффектами.
10. Историческая правдоподобность производителя, модификации и сроков проверена отдельно; статический аудитор этого не доказывает.

## 7. Запуск

Из корня репозитория:

```bash
python3 -I -m unittest discover -s skills/tdf-country-content/tests -v
python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --json industry-audit.json
```

Скрипт не запускает HOI4 и не проверяет runtime-поведение, цены, реальную доступность технологий, историческую правдоподобность или содержимое отсутствующего базового мода.
