"""Tests for hexflux.cli via subprocess."""

import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(args):
    return subprocess.run(
        [sys.executable, "-m", "hexflux.cli"] + list(args),
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


class InfoBlockTests(unittest.TestCase):
    def test_red_info_block(self):
        r = run(["#ff0000"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stderr, "")
        out = r.stdout
        self.assertIn("hex: #ff0000", out)
        self.assertIn("rgb: (255, 0, 0)", out)
        self.assertIn("hsl: hsl(0, 100%, 50%)", out)
        self.assertIn("hsv: hsv(0, 100%, 100%)", out)
        self.assertIn("luminance: 0.2126", out)
        self.assertIn("contrast vs white: 4.00", out)
        self.assertIn("contrast vs black: 5.25", out)

    def test_blue_info_block(self):
        r = run(["#3366ff"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("hex: #3366ff", r.stdout)
        self.assertIn("hsl: hsl(225, 100%, 60%)", r.stdout)
        self.assertIn("hsv: hsv(225, 80%, 100%)", r.stdout)

    def test_rgb_function_input(self):
        r = run(["rgb(51, 102, 255)"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("hex: #3366ff", r.stdout)

    def test_short_hex_input(self):
        r = run(["abc"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("hex: #aabbcc", r.stdout)


class ContrastTests(unittest.TestCase):
    def test_black_white(self):
        r = run(["#ffffff", "#000000"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("#ffffff vs #000000: contrast 21.00", r.stdout)
        self.assertIn("AA (4.5): pass", r.stdout)
        self.assertIn("AAA (7.0): pass", r.stdout)

    def test_aaaaaa_bbbbbb(self):
        r = run(["#aaaaaa", "#bbbbbb"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("contrast 1.21", r.stdout)
        self.assertIn("AA (4.5): fail", r.stdout)
        self.assertIn("AAA (7.0): fail", r.stdout)


class JsonTests(unittest.TestCase):
    def test_json_info(self):
        r = run(["--json", "#ff0000"])
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["hex"], "#ff0000")
        self.assertEqual(data["rgb"], [255, 0, 0])
        self.assertEqual(data["hsl"], [0.0, 1.0, 0.5])
        self.assertEqual(data["hsv"], [0.0, 1.0, 1.0])
        self.assertEqual(data["luminance"], 0.2126)
        self.assertEqual(data["contrast_white"], 4.0)
        self.assertEqual(data["contrast_black"], 5.25)

    def test_json_contrast(self):
        r = run(["--json", "#ffffff", "#000000"])
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["contrast"], 21.0)
        self.assertEqual(data["aa"], "pass")
        self.assertEqual(data["aaa"], "pass")


class TransformTests(unittest.TestCase):
    def test_shade(self):
        r = run(["--shade", "0.5", "#808080"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "shade(0.5): #404040")

    def test_tint(self):
        r = run(["--tint", "0.5", "#808080"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "tint(0.5): #c0c0c0")

    def test_invert(self):
        r = run(["--invert", "#3366ff"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "invert: #cc9900")

    def test_ramp(self):
        r = run(["--ramp", "5", "#808080"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout,
                         "ramp(5):\n"
                         "#000000\n#404040\n#808080\n#c0c0c0\n#ffffff\n")

    def test_json_shade(self):
        r = run(["--json", "--shade", "0.5", "#808080"])
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data, {
            "operation": "shade",
            "amount": 0.5,
            "color": "#808080",
            "result": "#404040",
        })


class FgTests(unittest.TestCase):
    def test_fg_mid_gray(self):
        r = run(["--fg", "#555555"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stderr, "")
        out = r.stdout
        self.assertIn("background: #555555", out)
        self.assertIn("foreground: #ffffff", out)
        self.assertIn("contrast: 7.46", out)
        self.assertIn("AA (4.5): pass", out)
        self.assertIn("AAA (7.0): pass", out)

    def test_fg_white_bg(self):
        r = run(["--fg", "#ffffff"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("foreground: #000000", r.stdout)


class ErrorTests(unittest.TestCase):
    def test_malformed_color_exit_1(self):
        r = run(["#zzz"])
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout, "")
        self.assertIn("hexflux:", r.stderr)

    def test_unknown_flag_exit_2(self):
        r = run(["--bogus", "#fff"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stderr)

    def test_missing_operand_exit_2(self):
        r = run(["--shade"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stderr)

    def test_bad_amount_exit_1(self):
        r = run(["--shade", "banana", "#fff"])
        self.assertEqual(r.returncode, 1)

    def test_bad_steps_exit_1(self):
        r = run(["--ramp", "1", "#fff"])
        self.assertEqual(r.returncode, 1)


class MetaTests(unittest.TestCase):
    def test_version(self):
        r = run(["--version"])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "hexflux 1.0.0")

    def test_help(self):
        r = run(["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage: hexflux", r.stdout)
        self.assertIn("--shade", r.stdout)
        self.assertIn("--fg", r.stdout)


if __name__ == "__main__":
    unittest.main()