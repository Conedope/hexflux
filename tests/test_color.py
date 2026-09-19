"""Tests for hexflux.color (pure math)."""

import unittest

from hexflux.color import (
    contrast,
    find_accessible_foreground,
    hsl_to_rgb,
    invert,
    luminance,
    parse_css,
    parse_hex,
    ramp,
    relative_luminance,
    rgb_to_hsl,
    rgb_to_hsv,
    shade,
    tint,
    to_hex,
)


class ParseHexTests(unittest.TestCase):
    def test_short_hash(self):
        self.assertEqual(parse_hex("#abc"), (0xaa, 0xbb, 0xcc))

    def test_long_hash(self):
        self.assertEqual(parse_hex("#aabbcc"), (0xaa, 0xbb, 0xcc))

    def test_no_prefix(self):
        self.assertEqual(parse_hex("aabbcc"), (0xaa, 0xbb, 0xcc))

    def test_zero_x_prefix(self):
        self.assertEqual(parse_hex("0xaabbcc"), (0xaa, 0xbb, 0xcc))
        self.assertEqual(parse_hex("0XFF0000"), (255, 0, 0))

    def test_short_expansion(self):
        self.assertEqual(parse_hex("#336"), (0x33, 0x33, 0x66))
        self.assertEqual(parse_hex("f0f"), (0xff, 0x00, 0xff))

    def test_known_values(self):
        self.assertEqual(parse_hex("#ff0000"), (255, 0, 0))
        self.assertEqual(parse_hex("#3366ff"), (51, 102, 255))
        self.assertEqual(parse_hex("#FFFFFF"), (255, 255, 255))

    def test_bad_forms(self):
        for bad in ("", "#", "12", "abcde", "aabbccd", "#gggggg", "##fff", "0x"):
            with self.assertRaises(ValueError):
                parse_hex(bad)


class ParseCssTests(unittest.TestCase):
    def test_hex_forms(self):
        self.assertEqual(parse_css("#ffffff"), (255, 255, 255))
        self.assertEqual(parse_css("abc"), (0xaa, 0xbb, 0xcc))
        self.assertEqual(parse_css("0xff0000"), (255, 0, 0))

    def test_rgb_integers(self):
        self.assertEqual(parse_css("rgb(1, 2, 3)"), (1, 2, 3))
        self.assertEqual(parse_css("rgb(255, 0, 128)"), (255, 0, 128))

    def test_rgb_percentages(self):
        self.assertEqual(parse_css("rgb(100%, 0%, 0%)"), (255, 0, 0))
        self.assertEqual(parse_css("rgb(50%, 50%, 50%)"), (128, 128, 128))

    def test_rgba(self):
        self.assertEqual(parse_css("rgba(0, 0, 255, 0.5)"), (0, 0, 255, 0.5))
        self.assertEqual(parse_css("rgba(0, 0, 255, 50%)"), (0, 0, 255, 0.5))

    def test_hsl(self):
        self.assertEqual(parse_css("hsl(0, 100%, 50%)"), (255, 0, 0))
        self.assertEqual(parse_css("hsl(120, 100%, 50%)"), (0, 255, 0))
        self.assertEqual(parse_css("hsl(240, 100%, 50%)"), (0, 0, 255))
        self.assertEqual(parse_css("hsl(225, 100%, 60%)"), (51, 102, 255))

    def test_hsla(self):
        self.assertEqual(parse_css("hsla(240, 100%, 50%, 0.25)"),
                         (0, 0, 255, 0.25))

    def test_bad_forms(self):
        for bad in ("", "nope(1)", "rgb(1, 2)", "rgb(1, 2, 3, 4)",
                    "hsl(0, 50)", "rgba(1, 2, 3)"):
            with self.assertRaises(ValueError):
                parse_css(bad)


class ToHexTests(unittest.TestCase):
    def test_output(self):
        self.assertEqual(to_hex(0xff, 0, 0), "#ff0000")
        self.assertEqual(to_hex(51, 102, 255), "#3366ff")
        self.assertEqual(to_hex(0, 0, 0), "#000000")
        self.assertEqual(to_hex(255, 255, 255), "#ffffff")
        self.assertTrue(to_hex(255, 255, 255).islower())

    def test_errors(self):
        with self.assertRaises(ValueError):
            to_hex(256, 0, 0)
        with self.assertRaises(ValueError):
            to_hex(-1, 0, 0)


class HslTests(unittest.TestCase):
    def test_exact_primaries(self):
        self.assertEqual(rgb_to_hsl(255, 0, 0), (0.0, 1.0, 0.5))
        self.assertEqual(rgb_to_hsl(0, 255, 0), (120.0, 1.0, 0.5))
        self.assertEqual(rgb_to_hsl(0, 0, 255), (240.0, 1.0, 0.5))

    def test_exact_blue(self):
        self.assertEqual(rgb_to_hsl(51, 102, 255), (225.0, 1.0, 0.6))
        self.assertEqual(hsl_to_rgb(225.0, 1.0, 0.6), (51, 102, 255))

    def test_gray(self):
        h, s, l = rgb_to_hsl(128, 128, 128)
        self.assertEqual((h, s), (0.0, 0.0))
        self.assertAlmostEqual(l, 128 / 255.0)

    def test_red_round_trip(self):
        self.assertEqual(hsl_to_rgb(0.0, 1.0, 0.5), (255, 0, 0))

    def test_hsl_round_trips(self):
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (51, 102, 255), (0, 255, 255), (255, 255, 0),
            (255, 0, 255), (128, 128, 0), (64, 128, 192),
        ]
        for color in colors:
            h, s, l = rgb_to_hsl(*color)
            self.assertEqual(hsl_to_rgb(h, s, l), color)


class HsvTests(unittest.TestCase):
    def test_exact_primaries(self):
        self.assertEqual(rgb_to_hsv(255, 0, 0), (0.0, 1.0, 1.0))
        self.assertEqual(rgb_to_hsv(0, 255, 0), (120.0, 1.0, 1.0))
        self.assertEqual(rgb_to_hsv(0, 0, 255), (240.0, 1.0, 1.0))

    def test_exact_blue(self):
        self.assertEqual(rgb_to_hsv(51, 102, 255), (225.0, 0.8, 1.0))

    def test_black_and_gray(self):
        self.assertEqual(rgb_to_hsv(0, 0, 0), (0.0, 0.0, 0.0))
        h, s, v = rgb_to_hsv(128, 128, 128)
        self.assertEqual((h, s), (0.0, 0.0))
        self.assertAlmostEqual(v, 128 / 255.0)


class LuminanceContrastTests(unittest.TestCase):
    def test_luminance_known(self):
        self.assertAlmostEqual(luminance((255, 255, 255)), 1.0)
        self.assertEqual(luminance((0, 0, 0)), 0.0)
        self.assertAlmostEqual(luminance((128, 128, 128)), 0.2159,
                               delta=0.0002)
        self.assertAlmostEqual(luminance((255, 0, 0)), 0.2126, places=4)

    def test_relative_luminance_alias(self):
        self.assertEqual(relative_luminance((128, 128, 128)),
                         luminance((128, 128, 128)))

    def test_contrast_black_white(self):
        self.assertAlmostEqual(contrast((0, 0, 0), (255, 255, 255)), 21.0)

    def test_contrast_white_red(self):
        expected = (1.0 + 0.05) / (0.2126 + 0.05)
        self.assertAlmostEqual(contrast((255, 255, 255), (255, 0, 0)),
                               expected, delta=0.01)
        self.assertAlmostEqual(contrast((255, 255, 255), (255, 0, 0)),
                               4.0, delta=0.01)

    def test_contrast_symmetric(self):
        a, b = (51, 102, 255), (128, 128, 0)
        self.assertEqual(contrast(a, b), contrast(b, a))


class ShadeTintTests(unittest.TestCase):
    def test_shade_exact(self):
        self.assertEqual(shade((128, 128, 128), 0.5), (64, 64, 64))
        self.assertEqual(to_hex(*shade((128, 128, 128), 0.5)), "#404040")
        self.assertEqual(shade((255, 255, 255), 1.0), (0, 0, 0))
        self.assertEqual(shade((255, 0, 0), 0.0), (255, 0, 0))

    def test_tint_exact(self):
        self.assertEqual(tint((128, 128, 128), 0.5), (192, 192, 192))
        self.assertEqual(to_hex(*tint((128, 128, 128), 0.5)), "#c0c0c0")
        self.assertEqual(tint((0, 0, 0), 1.0), (255, 255, 255))
        self.assertEqual(tint((0, 0, 0), 0.0), (0, 0, 0))

    def test_amount_validation(self):
        with self.assertRaises(ValueError):
            shade((0, 0, 0), 1.5)
        with self.assertRaises(ValueError):
            tint((0, 0, 0), -0.1)


class RampTests(unittest.TestCase):
    def test_ramp_length(self):
        self.assertEqual(len(ramp((128, 128, 128), 5)), 5)

    def test_ramp_exact_gray(self):
        self.assertEqual(
            ramp((128, 128, 128), 5),
            [(0, 0, 0), (64, 64, 64), (128, 128, 128),
             (192, 192, 192), (255, 255, 255)],
        )

    def test_ramp_endpoints(self):
        result = ramp((255, 0, 0), 3)
        self.assertEqual(result[0], (0, 0, 0))
        self.assertEqual(result[1], (255, 0, 0))
        self.assertEqual(result[2], (255, 255, 255))

    def test_ramp_steps_validation(self):
        with self.assertRaises(ValueError):
            ramp((0, 0, 0), 1)
        with self.assertRaises(ValueError):
            ramp((0, 0, 0), 0)


class InvertTests(unittest.TestCase):
    def test_invert(self):
        self.assertEqual(invert((255, 0, 0)), (0, 255, 255))
        self.assertEqual(invert((0, 0, 0)), (255, 255, 255))
        self.assertEqual(invert((255, 255, 255)), (0, 0, 0))
        self.assertEqual(invert(invert((51, 102, 255))), (51, 102, 255))


class AccessibleForegroundTests(unittest.TestCase):
    def test_mid_gray_picks_white(self):
        self.assertEqual(find_accessible_foreground((102, 102, 102)),
                         (255, 255, 255))

    def test_white_bg_picks_black(self):
        self.assertEqual(find_accessible_foreground((255, 255, 255)),
                         (0, 0, 0))

    def test_black_bg_picks_white(self):
        self.assertEqual(find_accessible_foreground((0, 0, 0)),
                         (255, 255, 255))

    def test_808080_picks_black(self):
        self.assertEqual(find_accessible_foreground((128, 128, 128)),
                         (0, 0, 0))

    def test_min_ratio_argument(self):
        self.assertEqual(
            find_accessible_foreground((128, 128, 128), min_ratio=3.0),
            (255, 255, 255))


if __name__ == "__main__":
    unittest.main()