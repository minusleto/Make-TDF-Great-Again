import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "tdf_inventory.py"
SPEC = importlib.util.spec_from_file_location("tdf_inventory", SCRIPT)
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def make_repo(self, root: Path):
        common = root / "mdredux" / "common"
        (common / "national_focus").mkdir(parents=True)
        (common / "ideas").mkdir(parents=True)
        (common / "decisions").mkdir(parents=True)
        (common / "military_industrial_organization" / "organizations").mkdir(parents=True)
        (common / "scripted_localisation").mkdir(parents=True)
        (common / "technologies").mkdir(parents=True)
        (common / "units" / "equipment").mkdir(parents=True)
        (common / "history" / "countries").mkdir(parents=True)
        (root / "mdredux" / "events").mkdir(parents=True)

        (common / "national_focus" / "Kazakhstan_Focus_Tree.txt").write_text(
            "focus_tree = { country = { original_tag = KAZ } "
            "focus = { id = KAZ_one } focus = { id = KAZ_two } }",
            encoding="utf-8",
        )
        (common / "national_focus" / "United Kingdom_Focus_Tree.txt").write_text(
            "focus_tree = { country = { original_tag = ENG } focus = { id = ENG_one } }",
            encoding="utf-8",
        )
        (common / "ideas" / "Kazakhstan_ideas.txt").write_text(
            "ideas = { country = { KAZ_visible = { } } "
            "hidden_ideas = { KAZ_hidden = { } KAZ_hidden2 = { } } }",
            encoding="utf-8",
        )
        (root / "mdredux" / "events" / "Britain.txt").write_text(
            "add_namespace = britain_test "
            "country_event = { id = britain_test.1 } "
            "news_event = { id = britain_test.2 }",
            encoding="utf-8",
        )
        (common / "decisions" / "Belarus.txt").write_text(
            "BLR_category = { BLR_first = { } BLR_second = { } }",
            encoding="utf-8",
        )
        (common / "scripted_localisation" / "99_KAZ_scripted_localisation.txt").write_text(
            "defined_text = { name = KAZ_test }", encoding="utf-8")
        (common / "military_industrial_organization" / "organizations" /
         "MDC_KAZ_organizations.txt").write_text(
            "KAZ_mio = { } generic_mio = { }", encoding="utf-8")
        (common / "technologies" / "custom.txt").write_text("technology = { }", encoding="utf-8")
        (common / "units" / "equipment" / "custom.txt").write_text("equipment = { }", encoding="utf-8")
        (common / "history" / "countries" / "KAZ - Kazakhstan.txt").write_text(
            "2000.1.1 = { }", encoding="utf-8")

    def test_counts_all_supported_content_types(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            result = inventory.collect_inventory(root)
            self.assertEqual(result["files"]["focus_trees"], 2)
            self.assertEqual(result["blocks"]["focuses"], 3)
            self.assertEqual(result["blocks"]["ideas_country"], 1)
            self.assertEqual(result["blocks"]["ideas_hidden"], 2)
            self.assertEqual(result["blocks"]["events_total"], 2)
            self.assertEqual(result["blocks"]["event_namespace_declarations"], 1)
            self.assertEqual(result["blocks"]["decision_categories"], 1)
            self.assertEqual(result["blocks"]["decisions"], 2)
            self.assertEqual(result["blocks"]["scripted_localisation_defined_text"], 1)
            self.assertEqual(result["blocks"]["mio_top_level_definitions_including_generic_templates"], 2)
            self.assertEqual(result["files"]["country_history_files"], 1)
            self.assertEqual(result["files"]["technology_files"], 1)
            self.assertEqual(result["files"]["equipment_files"], 1)
            tags = {row["tag"] for row in result["focus_trees"]}
            self.assertEqual(tags, {"KAZ", "ENG"})

    def test_inventory_parser_reports_malformed_script(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            broken = root / "mdredux" / "events" / "Broken.txt"
            broken.write_text("country_event = { id = broken.1", encoding="utf-8")
            result = inventory.collect_inventory(root)
            self.assertGreater(result["parse_issues"]["event_files"], 0)


if __name__ == "__main__":
    unittest.main()
