#!/usr/bin/env python3
"""Статический аудит контента стран TDF/MDC по правилам tdf-country-content.

Запуск из корня репозитория:
    python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --require-external-registry
    python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --tags POR,KAZ
    python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --details KAZ
    python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --json audit.json

Скрипт не запускает HOI4 и не содержит файлов целевой сборки вне среза. Ссылки на
отсутствующие в срезе внешние namespace/идеи не объявляются ошибками без достаточных оснований.
Код завершения: 0 — ERROR нет; 1 — найдены ERROR; 2 — ошибка входных файлов/репозитория.
Тесты: python -m unittest discover -s skills/tdf-country-content/tests -v
Реализация: пакет tdf_audit_lib рядом со скриптом (устройство и правила: skills/README.md).
"""
import sys
from pathlib import Path

# `python -I` не добавляет каталог скрипта в sys.path: подключаем пакет рядом со скриптом явно.
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from tdf_audit_lib import (  # noqa: E402
    core,
    indexes,
    decisions,
    state_flow,
    connectivity,
    events,
    country,
    external_dependencies,
    ideas,
    industry,
    cli,
)

from tdf_audit_lib.cli import main  # noqa: E402

# Обратная совместимость: тесты и tdf_inventory.py обращаются к именам как к атрибутам этого модуля.
for _module in (core, indexes, decisions, state_flow, connectivity, events, country, external_dependencies, ideas, industry, cli):
    globals().update({name: value for name, value in vars(_module).items() if not name.startswith("__")})

if __name__ == "__main__":
    raise SystemExit(main())
