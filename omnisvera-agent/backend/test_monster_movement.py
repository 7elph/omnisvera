"""Testes determinísticos do parser de movimento de monstros."""
from unittest import TestCase

from app.monster_movement import movement_modes, movement_pending, selected_movement


class MovementModesTests(TestCase):
    def test_native_speed_annotation_is_already_scaled_not_an_unknown_mode(self):
        for text,speed in [('36 m · Velocidade ×4',36),('18 m · Velocidade ×2',18),('27 m · Velocidade ×3',27)]:
            with self.subTest(text=text):self.assertEqual(selected_movement(text),speed)
        self.assertTrue(movement_pending('36 m · Velocidade ×99'))
        self.assertTrue(movement_pending('36 m · modo inventado ×4'))

    def test_numeric_and_metric_walk(self):
        self.assertEqual({"walk": 9.0}, movement_modes(9))
        self.assertEqual({"walk": 9.0}, movement_modes(9.0))
        self.assertEqual({"walk": 9.0}, movement_modes("9"))
        self.assertEqual({"walk": 9.0}, movement_modes("9 m"))
        self.assertEqual({"walk": 9.0}, movement_modes("9 metros"))
        self.assertEqual({"walk": 1.5}, movement_modes("1,5 m"))
        self.assertEqual({"walk": 0.0}, movement_modes("0"))

    def test_srd_lists_keep_walk_and_fly_separate(self):
        self.assertEqual({"walk": 9.0, "fly": 21.0}, movement_modes("9, 21V"))
        self.assertEqual({"walk": 9.0, "fly": 21.0}, movement_modes("9,21V"))
        self.assertEqual({"walk": 9.0, "fly": 18.0}, movement_modes("9,18V"))
        self.assertEqual({"walk": 12.0, "fly": 21.0}, movement_modes("12, 21V"))

    def test_only_flight_and_other_declared_codes(self):
        self.assertEqual({"fly": 18.0}, movement_modes("18V"))
        self.assertEqual({"walk": 9.0, "swim": 6.0}, movement_modes("9, 6N"))
        self.assertEqual({"walk": 6.0, "climb": 9.0}, movement_modes("6, 9E"))
        self.assertEqual({"walk": 12.0, "burrow": 9.0}, movement_modes("12, 9C"))

    def test_textual_modes_when_unambiguous(self):
        self.assertEqual({"walk": 9.0, "fly": 21.0}, movement_modes("9 m de caminhada e 21 m de voo"))
        self.assertEqual({"walk": 9.0, "fly": 21.0}, movement_modes("caminhada 9 m; voo 21 m"))
        self.assertEqual({"swim": 12.0}, movement_modes("natação 12 m"))
        self.assertEqual({"climb": 6.0}, movement_modes("escalada 6 metros"))
        self.assertEqual({"burrow": 3.0}, movement_modes("escavação 3 m"))
        self.assertEqual({"fly": 18.0}, movement_modes("voar 18 metros"))

    def test_unknown_symbol_never_invents_speed(self):
        self.assertEqual({"walk": 9.0}, movement_modes("9, 18X"))
        self.assertEqual(["18x"], movement_pending("9, 18X"))
        self.assertEqual({}, movement_modes("18X"))
        self.assertEqual(["18x"], movement_pending("18X"))

    def test_invalid_or_empty_is_rejected(self):
        with self.assertRaises(ValueError):
            selected_movement("")
        with self.assertRaises(ValueError):
            selected_movement(None)
        self.assertEqual({}, movement_modes("movimento indefinido"))
        self.assertEqual(["indefinido"], movement_pending("movimento indefinido"))
        with self.assertRaises(ValueError):
            selected_movement("movimento indefinido")


class SelectedMovementTests(TestCase):
    def test_walk_is_default_when_available(self):
        self.assertEqual(9.0, selected_movement("9, 21V"))
        self.assertEqual(9.0, selected_movement("9,18V"))
        self.assertEqual(9.0, selected_movement("9 m"))

    def test_explicit_mode_selects_only_that_mode(self):
        self.assertEqual(21.0, selected_movement("9, 21V", "fly"))
        self.assertEqual(21.0, selected_movement("9,21V", "voo"))
        self.assertEqual(9.0, selected_movement("9, 21V", "walk"))
        self.assertEqual(9.0, selected_movement("9, 21V", "terrestrial"))

    def test_single_clear_mode_is_used_when_walk_absent(self):
        self.assertEqual(18.0, selected_movement("18V"))
        self.assertEqual(12.0, selected_movement("natação 12 m"))

    def test_mode_selection_rejects_absent_or_invalid_mode(self):
        with self.assertRaises(ValueError):
            selected_movement("9, 21V", "swim")
        with self.assertRaises(ValueError):
            selected_movement("9, 21V", "galope")
        with self.assertRaises(ValueError):
            selected_movement("9 m", "fly")

    def test_multiple_modes_without_walk_require_explicit_mode(self):
        with self.assertRaises(ValueError):
            selected_movement("6N, 12V")
        self.assertEqual(6.0, selected_movement("6N, 12V", "swim"))
        self.assertEqual(12.0, selected_movement("6N, 12V", "fly"))

    def test_does_not_add_walk_and_fly(self):
        modes = movement_modes("9, 21V")
        self.assertEqual(9.0, selected_movement("9, 21V"))
        self.assertNotIn(30.0, modes.values())
        self.assertEqual(2, len(modes))
