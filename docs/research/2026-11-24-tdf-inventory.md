# Структурная инвентаризация TDF / MDC

**Снимок:** 24 ноября 2026 года.  
**База:** `main`, commit `536a03ed9f69f39ecce022e25bcacb8903f3ce3a`.  
**Область:** файлы текущего репозитория `mdredux/`; полный базовый Millennium Dawn здесь отсутствует.

Это инвентаризация файлов и синтаксических блоков, а не оценка качества контента. Она не подтверждает, что события, идеи, MIO, эффекты или технологии из базового мода существуют; отсутствие внешнего определения в этом срезе не доказывает ошибку. Игра не запускалась.

## Сводка

| Тип | Файлов | Блоков / объявлений |
|---|---:|---:|
| Focus trees | 12 | 5 422 фокуса |
| Ideas | 15 | 1 806 в `country`, 795 в `hidden_ideas` (2 601 всего) |
| Events | 10 | 2 606 `country_event`, 158 `news_event` (2 764 всего), 147 объявлений namespace |
| Decisions | 6 | 25 категорий, 279 непосредственных блоков решений |
| Scripted localisation | 10 | 602 `defined_text` |
| MIO organizations | 57 | 401 блок верхнего уровня, включая generic templates |
| Country history | 7 | — |
| Technologies | 28 | — |
| Equipment | 36 | — |

### Focus trees

| Тег | Путь | Фокусов |
|---|---|---:|
| ARM | `mdredux/common/national_focus/Armenia_Focus_Tree.txt` | 454 |
| BLR | `mdredux/common/national_focus/Belarus_Focus_Tree.txt` | 271 |
| GEO | `mdredux/common/national_focus/Georgia_Focus_Tree.txt` | 264 |
| HUN | `mdredux/common/national_focus/Hungary_Focus_Tree.txt` | 326 |
| ISR | `mdredux/common/national_focus/Israel_Focus_Tree.txt` | 667 |
| KAZ | `mdredux/common/national_focus/Kazakhstan_Focus_Tree.txt` | 377 |
| POL | `mdredux/common/national_focus/Poland_Focus_Tree.txt` | 647 |
| POR | `mdredux/common/national_focus/Portugal_Focus_Tree.txt` | 303 |
| SOV | `mdredux/common/national_focus/Russia_Focus_Tree.txt` | 658 |
| SLO | `mdredux/common/national_focus/Slovakia_Focus_Tree.txt` | 180 |
| SYR | `mdredux/common/national_focus/Syria_Focus_Tree.txt` | 413 |
| ENG | `mdredux/common/United Kingdom_Focus_Tree.txt` | 862 |

## Метод подсчёта

Единый скрипт: `skills/tdf-country-content/scripts/tdf_inventory.py`. Он использует тот же структурный парсер `parse_hoi`, что и статический аудитор, а не grep по строкам. Команда запуска из корня:

```bash
python3 -I skills/tdf-country-content/scripts/tdf_inventory.py .
python3 -I skills/tdf-country-content/scripts/tdf_inventory.py . --json inventory.json
```

Правила подсчёта:
- Focus trees: все файлы `*_Focus_Tree.txt` в `mdredux/common/` и рекурсивно в `mdredux/common/national_focus/`; число всех блоков `focus`.
- Ideas: непосредственные дочерние блоки `country` и `hidden_ideas` внутри найденных блоков `ideas`. Счёт не является числом уникальных ID по всему базовому моду.
- Events: верхнеуровневые блоки `country_event` и `news_event`, а также объявления `add_namespace` во всех `mdredux/events/*.txt`.
- Decisions: блоки верхнего уровня считаются категориями; их непосредственные дочерние блоки — решения. Вложенные категории и внешние динамические решения не разворачиваются.
- Scripted localisation: верхнеуровневые `defined_text`.
- MIO: верхнеуровневые блоки в каталоге organizations. Число включает generic-шаблоны и не должно трактоваться как количество только страновых MIO.
- Technologies, equipment и country history: число файлов `.txt` в соответствующих каталогах, а не количество определений.

Скрипт также выводит parse issues по проверяемым категориям. Любые изменения структуры файлов требуют повторной генерации отчёта; этот документ — снимок указанного commit, а не автоматически обновляемая статистика.

## Ограничения и известные расхождения

- Британское дерево хранится вне `common/national_focus/`. Старый `tdf_audit.py` его пропускал; исправление поиска обоих расположений включено в этап 0.
- Старый отчёт `2026-10-tdf-trees-audit.md` и таблицы в references — исторический срез 30 октября по более узкой выборке и прежней методике. Не сравнивать его суммы напрямую с этой инвентаризацией.
- Число блоков не равно числу активных, достижимых или видимых в игре элементов. В выборку входят отключённые ветки, общие и вспомогательные definitions.
- Решения считаются по непосредственной структуре файла; MIO учитывает generic templates. Эти правила нужно сохранять при сравнении следующих снимков.

## Что этим отчётом не проверяется

Синтаксическая достижимость фокусов, корректность scope, баланс, историческая достоверность, полнота локализации, работа tooltip, цепочки событий, поведение ИИ и наличие внешних определений в Millennium Dawn. Для этого нужны профильные проверки, базовый мод и/или запуск игры.
