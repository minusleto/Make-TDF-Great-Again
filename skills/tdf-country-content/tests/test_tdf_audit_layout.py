import ast
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tdf_audit as base  # noqa: E402  (модуль, а не класс: тесты не собираются повторно)

SCRIPTS = Path(__file__).parents[1] / "scripts"
PACKAGE = SCRIPTS / "tdf_audit_lib"
MODULES = sorted(p.stem for p in PACKAGE.glob("*.py") if p.stem != "__init__")
MAX_MODULE_LINES = 1200


def sibling_imports(module):
    text = (PACKAGE / "{}.py".format(module)).read_text(encoding="utf-8")
    return set(re.findall(r"^from \.(\w+) import", text, re.M))


def top_level_names(path):
    names = []
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            names.extend(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


class AuditPackageLayoutTests(unittest.TestCase):
    def test_each_module_imports_on_its_own(self):
        """Импорт без остальных модулей ловит циклы и пропущенные импорты независимо от порядка."""
        for module in MODULES:
            with self.subTest(module=module):
                code = "import sys; sys.path.insert(0, {!r}); import tdf_audit_lib.{}".format(str(SCRIPTS), module)
                proc = subprocess.run([sys.executable, "-I", "-c", code], universal_newlines=True,
                                      encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_module_graph_is_acyclic_and_core_is_a_leaf(self):
        graph = {module: sibling_imports(module) for module in MODULES}
        self.assertEqual(graph["core"], set(), "core must not import sibling modules")
        state = {}

        def visit(module, path):
            self.assertNotEqual(state.get(module), 1, "import cycle: " + " -> ".join(path + [module]))
            if state.get(module) == 2:
                return
            state[module] = 1
            for dep in sorted(graph[module]):
                visit(dep, path + [module])
            state[module] = 2

        for module in MODULES:
            visit(module, [])

    def test_entry_point_reexports_every_definition(self):
        missing = []
        for module in MODULES:
            for name in top_level_names(PACKAGE / "{}.py".format(module)):
                if not hasattr(base.audit, name):
                    missing.append("{}.{}".format(module, name))
        self.assertEqual(missing, [], "tdf_audit.py does not re-export these definitions")

    def test_cli_names_used_by_tools_are_available(self):
        for name in ("main", "ERRORS", "WARNS", "INFOS", "PARSE_ERROR_FIELDS", "audit_country", "parse_hoi"):
            self.assertTrue(hasattr(base.audit, name), name)

    def test_no_module_grows_back_into_a_monolith(self):
        too_long = {m: len((PACKAGE / "{}.py".format(m)).read_text(encoding="utf-8").split("\n"))
                    for m in MODULES}
        too_long = {m: n for m, n in too_long.items() if n > MAX_MODULE_LINES}
        self.assertEqual(too_long, {}, "Split the module (limit {} lines)".format(MAX_MODULE_LINES))

    def test_entry_point_stays_thin(self):
        lines = (SCRIPTS / "tdf_audit.py").read_text(encoding="utf-8").split("\n")
        self.assertLess(len(lines), 80, "tdf_audit.py must stay a thin entry point")


if __name__ == "__main__":
    unittest.main()
