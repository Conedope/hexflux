"""Core color math for hexflux: parsing, conversion, ramps and WCAG contrast.

Every function here is pure and deterministic; there is no state, no I/O and
no randomness.  RGB triples are ``(r, g, b)`` tuples of ints in ``[0, 255]``.
Hue is in degrees ``[0, 360)``; saturation / lightness / value are in ``[0, 1]``.
"""

_HEX_DIGITS = "0123456789abcdef"


def parse_hex(s):
    """Parse a hexadecimal color into a ``(r, g, b)`` tuple of 0-255 ints.

    Accepts ``#abc``, ``#aabbcc``, ``abc``/``aabbcc`` and ``0x...`` forms.
    Raises ``ValueError`` for anything else.
    """
    t = s.strip().lower()
    if not t:
        raise ValueError("empty color")
    if t.startswith("0x"):
        t = t[2:]
    elif t.startswith("#"):
        t = t[1:]
    if not t or len(t) not in (3, 6):
        raise ValueError("invalid hex color %r" % (s,))
    if any(c not in _HEX_DIGITS for c in t):
        raise ValueError("invalid hex digit in %r" % (s,))
    if len(t) == 3:
        t = "".join(c * 2 for c in t)
    return (int(t[0:2], 16), int(t[2:4], 16), int(t[4:6], 16))


def _looks_like_plain_hex(s):
    t = s.strip().lower()
    if t.startswith("0x"):
        t = t[2:]
    elif t.startswith("#"):
        t = t[1:]
    return (
        bool(t)
        and len(t) in (3, 6)
        and all(c in _HEX_DIGITS for c in t)
    )


def _split_function(s):
    i = s.find("(")
    if i < 0 or not s.endswith(")"):
        raise ValueError("unsupported color form %r" % (s,))
    name = s[:i].strip().lower()
    if not name or not name.isalpha():
        raise ValueError("malformed color function in %r" % (s,))
    parts = [p.strip() for p in s[i + 1:-1].split(",")]
    if any(p == "" for p in parts):
        raise ValueError("empty component in %r" % (s,))
    return name, parts


def _number(part):
    part = part.strip().lower()
    if part.endswith("%"):
        return float(part[:-1]), True
    return float(part), False


def _channel(part, maximum):
    value, is_pct = _number(part)
    if is_pct:
        value = value / 100.0 * maximum
    return min(maximum, max(0.0, value))


def _alpha(part):
    value, is_pct = _number(part)
    if is_pct:
        value = value / 100.0
    return min(1.0, max(0.0, value))


def parse_css(s):
    """Parse any supported color form into RGB.

    Returns ``(r, g, b)`` for hex / ``rgb()`` / ``hsl()`` forms and
    ``(r, g, b, a)`` for ``rgba()`` / ``hsla()`` forms.  Raises
    ``ValueError`` for malformed input.
    """
    s = s.strip()
    if not s:
        raise ValueError("empty color")
    if _looks_like_plain_hex(s):
        return parse_hex(s)
    name, parts = _split_function(s)
    if name == "rgb":
        if len(parts) != 3:
            raise ValueError("rgb() takes 3 components")
        return (round(_channel(parts[0], 255)),
                round(_channel(parts[1], 255)),
                round(_channel(parts[2], 255)))
    if name == "rgba":
        if len(parts) != 4:
            raise ValueError("rgba() takes 4 components")
        rgb = (round(_channel(p, 255)) for p in parts[:3])
        return tuple(rgb) + (round(_alpha(parts[3]), 4),)
    if name == "hsl":
        if len(parts) != 3:
            raise ValueError("hsl() takes 3 components")
        h_val, s_val, l_val = (_number(p) for p in parts)
        h = h_val[0] % 360.0
        sat = s_val[0] / 100.0 if s_val[1] else s_val[0]
        lum = l_val[0] / 100.0 if l_val[1] else l_val[0]
        return hsl_to_rgb(h, min(1.0, max(0.0, sat)),
                          min(1.0, max(0.0, lum)))
    if name == "hsla":
        if len(parts) != 4:
            raise ValueError("hsla() takes 4 components")
        rgb = parse_css("hsl(%s)" % ",".join(parts[:3]))
        return rgb + (round(_alpha(parts[3]), 4),)
    raise ValueError("unknown color function %r" % (name,))


def to_hex(r, g, b):
    """Render an RGB triple as a lowercase ``#rrggbb`` string."""
    if not all(isinstance(c, int) and 0 <= c <= 255 for c in (r, g, b)):
        raise ValueError("channels must be ints in [0, 255]")
    return "#%02x%02x%02x" % (r, g, b)


def rgb_to_hsl(r, g, b):
    """Convert RGB to ``(h, s, l)``; h in degrees, s and l in [0, 1]."""
    rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(rn, gn, bn), min(rn, gn, bn)
    l = (mx + mn) / 2.0
    d = mx - mn
    if d == 0.0:
        return (0.0, 0.0, l)
    s = d / (1.0 - abs(2.0 * l - 1.0))
    if mx == rn:
        h = ((gn - bn) / d) % 6.0
    elif mx == gn:
        h = (bn - rn) / d + 2.0
    else:
        h = (rn - gn) / d + 4.0
    return (h * 60.0 % 360.0, s, l)


def hsl_to_rgb(h, s, l):
    """Convert ``(h, s, l)`` back to an RGB triple."""
    h, s, l = float(h) % 360.0, float(s), float(l)
    c = (1.0 - abs(2.0 * l - 1.0)) * s
    x = c * (1.0 - abs((h / 60.0) % 2.0 - 1.0))
    m = l - c / 2.0
    sector = int(h / 60.0) % 6
    if sector == 0:
        r, g, b = c, x, 0.0
    elif sector == 1:
        r, g, b = x, c, 0.0
    elif sector == 2:
        r, g, b = 0.0, c, x
    elif sector == 3:
        r, g, b = 0.0, x, c
    elif sector == 4:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x
    return (round((r + m) * 255.0), round((g + m) * 255.0),
            round((b + m) * 255.0))


def rgb_to_hsv(r, g, b):
    """Convert RGB to ``(h, s, v)``; h in degrees, s and v in [0, 1]."""
    rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(rn, gn, bn), min(rn, gn, bn)
    v = mx
    d = mx - mn
    if mx == 0.0:
        return (0.0, 0.0, 0.0)
    s = d / mx
    if d == 0.0:
        return (0.0, 0.0, v)
    if mx == rn:
        h = ((gn - bn) / d) % 6.0
    elif mx == gn:
        h = (bn - rn) / d + 2.0
    else:
        h = (rn - gn) / d + 4.0
    return (h * 60.0 % 360.0, s, v)


def _linearize(channel):
    c = channel / 255.0
    if c <= 0.03928:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def luminance(*rgb):
    """WCAG 2.x relative luminance of an RGB color, in [0, 1].

    Accepts either ``luminance((r, g, b))`` or ``luminance(r, g, b)``.
    """
    if len(rgb) == 1:
        r, g, b = rgb[0]
    else:
        r, g, b = rgb
    return (0.2126 * _linearize(r) + 0.7152 * _linearize(g)
            + 0.0722 * _linearize(b))


def relative_luminance(rgb):
    """Inclusive alias of :func:`luminance` (WCAG 1.4.3 relative luminance)."""
    return luminance(rgb)


def contrast(rgb_a, rgb_b):
    """WCAG contrast ratio between two RGB colors (1..21)."""
    l1 = luminance(rgb_a)
    l2 = luminance(rgb_b)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def shade(rgb, amount):
    """Mix ``rgb`` toward black by ``amount`` in [0, 1]."""
    if not 0.0 <= amount <= 1.0:
        raise ValueError("amount must be in [0, 1]")
    return tuple(round(c * (1.0 - amount)) for c in rgb)


def tint(rgb, amount):
    """Mix ``rgb`` toward white by ``amount`` in [0, 1]."""
    if not 0.0 <= amount <= 1.0:
        raise ValueError("amount must be in [0, 1]")
    return tuple(round(c + (255 - c) * amount) for c in rgb)


def ramp(rgb, steps):
    """Return ``steps`` colors from black through ``rgb`` to white.

    The gradient includes both endpoints: the first color is black, the
    color itself sits at the midpoint, and the last color is white.
    """
    if not isinstance(steps, int) or steps < 2:
        raise ValueError("steps must be an int >= 2")
    color = tuple(rgb)
    result = []
    for step in range(steps):
        t = step / (steps - 1.0)
        if t <= 0.5:
            u = t * 2.0
            c = tuple(round(a + (b - a) * u)
                      for a, b in zip((0, 0, 0), color))
        else:
            u = (t - 0.5) * 2.0
            c = tuple(round(a + (b - a) * u)
                      for a, b in zip(color, (255, 255, 255)))
        result.append(c)
    return result


def invert(rgb):
    """Invert ``rgb`` on the RGB cube."""
    return tuple(255 - c for c in rgb)


def find_accessible_foreground(bg, min_ratio=4.5):
    """Pick white or black as an accessible foreground for background ``bg``.

    Returns the lighter candidate (white first) whenever it clears
    ``min_ratio``; otherwise falls back to the candidate with the better
    contrast ratio.
    """
    white, black = (255, 255, 255), (0, 0, 0)
    for candidate in (white, black):
        if contrast(bg, candidate) >= min_ratio:
            return candidate
    if contrast(bg, white) >= contrast(bg, black):
        return white
    return black