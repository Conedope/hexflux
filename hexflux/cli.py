"""Command-line interface for hexflux.

Usage::

    hexflux '#3366ff'
    hexflux '#ffffff' '#ff0000'
    hexflux --shade 0.5 '#808080'
    hexflux --tint 0.5 '#808080'
    hexflux --ramp 5 '#808080'
    hexflux --invert '#3366ff'
    hexflux --fg '#555555'
    hexflux --json '#ff0000'
"""

import json
import sys

from hexflux import __version__
from hexflux.color import (
    contrast,
    find_accessible_foreground,
    hsl_to_rgb,
    invert,
    luminance,
    parse_css,
    ramp,
    rgb_to_hsl,
    rgb_to_hsv,
    shade,
    tint,
    to_hex,
)

USAGE = """\
usage: hexflux [--json] COLOR
       hexflux [--json] COLOR1 COLOR2
       hexflux [--json] --shade AMOUNT COLOR
       hexflux [--json] --tint AMOUNT COLOR
       hexflux [--json] --ramp STEPS COLOR
       hexflux [--json] --invert COLOR
       hexflux [--json] --fg COLOR
"""

HELP = """\
{usage}
A deterministic color utility: parse and convert colors, build shades, tints
and display ramps, and compute WCAG 2.x contrast ratios.

Options:
  --json                    emit JSON on stdout
  --version                 print the version and exit
  -h, --help                print this help and exit

Flag summary:
  --shade AMOUNT COLOR      mix COLOR toward black by AMOUNT (0.0-1.0)
  --tint AMOUNT COLOR       mix COLOR toward white by AMOUNT (0.0-1.0)
  --ramp STEPS COLOR        gradient from black through COLOR to white
  --invert COLOR            invert COLOR on the RGB cube
  --fg COLOR                pick white or black as an accessible foreground

Accepted color forms:
  #abc, #aabbcc, abc, aabbcc, 0x..., rgb(r,g,b), rgba(r,g,b,a),
  percentage channels, hsl(h,s%,l%), hsla(h,s%,l%,a).

Exit status:
  0  success
  1  malformed color or value
  2  usage error (unknown or missing arguments)

Examples:
  hexflux '#3366ff'
  hexflux '#ffffff' '#ff0000'
  hexflux --shade 0.5 '#808080'
  hexflux --fg '#555555'
  hexflux --json '#ff0000'
""".format(usage=USAGE)

_ARITY = {"--shade": 2, "--tint": 2, "--ramp": 2, "--invert": 1, "--fg": 1}


def _num(x):
    rounded = round(x, 1)
    if rounded == int(rounded):
        return str(int(rounded))
    return "%.1f" % rounded


def _pct(x):
    return _num(x * 100.0) + "%"


def _fmt_hsl(h, s, l):
    return "hsl(%s, %s, %s)" % (_num(h), _pct(s), _pct(l))


def _fmt_hsv(h, s, v):
    return "hsv(%s, %s, %s)" % (_num(h), _pct(s), _pct(v))


def _ratio(x):
    return "%.2f" % x


def _lum(x):
    return "%.4f" % x


def _pass_fail(ratio, threshold):
    return "pass" if ratio >= threshold else "fail"


def _emit_json(data):
    sys.stdout.write(json.dumps(data, sort_keys=True, indent=2) + "\n")


def _parse_amount(text):
    try:
        value = float(text)
    except ValueError:
        raise ValueError("invalid amount %r" % (text,))
    if not 0.0 <= value <= 1.0:
        raise ValueError("amount must be between 0 and 1")
    return value


def _parse_steps(text):
    try:
        value = int(text)
    except ValueError:
        raise ValueError("invalid steps %r" % (text,))
    if value < 2:
        raise ValueError("steps must be >= 2")
    return value


def _cmd_info(text, as_json):
    color = parse_css(text)
    r, g, b = color[:3]
    h, s, l = rgb_to_hsl(r, g, b)
    hv, sv, v = rgb_to_hsv(r, g, b)
    lum = luminance(r, g, b)
    cw = contrast(color, (255, 255, 255))
    cb = contrast(color, (0, 0, 0))
    if as_json:
        _emit_json({
            "hex": to_hex(r, g, b),
            "rgb": [r, g, b],
            "hsl": [round(h, 6), round(s, 6), round(l, 6)],
            "hsv": [round(hv, 6), round(sv, 6), round(v, 6)],
            "luminance": round(lum, 4),
            "contrast_white": round(cw, 2),
            "contrast_black": round(cb, 2),
        })
    else:
        sys.stdout.write(
            "hex: %s\n"
            "rgb: (%d, %d, %d)\n"
            "hsl: %s\n"
            "hsv: %s\n"
            "luminance: %s\n"
            "contrast vs white: %s\n"
            "contrast vs black: %s\n"
            % (to_hex(r, g, b), r, g, b, _fmt_hsl(h, s, l),
               _fmt_hsv(hv, sv, v), _lum(lum), _ratio(cw), _ratio(cb)))
    return 0


def _cmd_contrast(a_text, b_text, as_json):
    ca, cb = parse_css(a_text), parse_css(b_text)
    ratio = contrast(ca, cb)
    aa = _pass_fail(ratio, 4.5)
    aaa = _pass_fail(ratio, 7.0)
    if as_json:
        _emit_json({
            "color1": to_hex(*ca[:3]),
            "color2": to_hex(*cb[:3]),
            "contrast": round(ratio, 2),
            "aa": aa,
            "aaa": aaa,
        })
    else:
        sys.stdout.write(
            "%s vs %s: contrast %s\n"
            "AA (4.5): %s\n"
            "AAA (7.0): %s\n"
            % (to_hex(*ca[:3]), to_hex(*cb[:3]), _ratio(ratio), aa, aaa))
    return 0


def _cmd_mix(text_amount, operation, text_color, as_json):
    amount = _parse_amount(text_amount)
    color = parse_css(text_color)
    name = operation[2:]
    result = shade(color, amount) if operation == "--shade" else tint(color, amount)
    if as_json:
        _emit_json({
            "operation": name,
            "amount": amount,
            "color": to_hex(*color[:3]),
            "result": to_hex(*result),
        })
    else:
        sys.stdout.write("%s(%s): %s\n"
                         % (name, _num(amount), to_hex(*result)))
    return 0


def _cmd_ramp(text_steps, text_color, as_json):
    steps = _parse_steps(text_steps)
    color = parse_css(text_color)
    result = ramp(color, steps)
    if as_json:
        _emit_json({
            "operation": "ramp",
            "steps": steps,
            "color": to_hex(*color[:3]),
            "result": [to_hex(*c) for c in result],
        })
    else:
        sys.stdout.write("ramp(%d):\n" % steps)
        for c in result:
            sys.stdout.write(to_hex(*c) + "\n")
    return 0


def _cmd_invert(text_color, as_json):
    color = parse_css(text_color)
    result = invert(color)
    if as_json:
        _emit_json({
            "operation": "invert",
            "color": to_hex(*color[:3]),
            "result": to_hex(*result),
        })
    else:
        sys.stdout.write("invert: %s\n" % to_hex(*result))
    return 0


def _cmd_fg(text_bg, as_json):
    bg = parse_css(text_bg)
    fg = find_accessible_foreground(bg)
    ratio = contrast(bg, fg)
    aa = _pass_fail(ratio, 4.5)
    aaa = _pass_fail(ratio, 7.0)
    if as_json:
        _emit_json({
            "background": to_hex(*bg[:3]),
            "foreground": to_hex(*fg),
            "contrast": round(ratio, 2),
            "aa": aa,
            "aaa": aaa,
        })
    else:
        sys.stdout.write(
            "background: %s\n"
            "foreground: %s\n"
            "contrast: %s\n"
            "AA (4.5): %s\n"
            "AAA (7.0): %s\n"
            % (to_hex(*bg[:3]), to_hex(*fg), _ratio(ratio), aa, aaa))
    return 0


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    emit_json = False
    op = None
    tokens = []

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("-h", "--help"):
            sys.stdout.write(HELP)
            return 0
        if arg == "--version":
            sys.stdout.write("hexflux %s\n" % __version__)
            return 0
        if arg == "--json":
            emit_json = True
        elif arg in _ARITY:
            op = arg
        elif arg.startswith("-") and arg != "-":
            sys.stderr.write(USAGE)
            sys.stderr.write("hexflux: unknown option %r\n" % arg)
            return 2
        else:
            tokens.append(arg)
        i += 1

    if op is not None and len(tokens) != _ARITY[op]:
        sys.stderr.write(USAGE)
        sys.stderr.write("hexflux: option %s takes %d argument(s)\n"
                         % (op, _ARITY[op]))
        return 2

    try:
        if op is None:
            if len(tokens) == 1:
                return _cmd_info(tokens[0], emit_json)
            if len(tokens) == 2:
                return _cmd_contrast(tokens[0], tokens[1], emit_json)
            sys.stderr.write(USAGE)
            sys.stderr.write("hexflux: expected one or two colors\n")
            return 2
        if op == "--shade":
            return _cmd_mix(tokens[0], "--shade", tokens[1], emit_json)
        if op == "--tint":
            return _cmd_mix(tokens[0], "--tint", tokens[1], emit_json)
        if op == "--ramp":
            return _cmd_ramp(tokens[0], tokens[1], emit_json)
        if op == "--invert":
            return _cmd_invert(tokens[0], emit_json)
        if op == "--fg":
            return _cmd_fg(tokens[0], emit_json)
    except ValueError as err:
        sys.stderr.write("hexflux: %s\n" % err)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())