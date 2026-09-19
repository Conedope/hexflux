# hexflux

A small, fully deterministic color utility for the command line. Parse colors
in several formats, convert between RGB / HSL / HSV, generate shades, tints
and display ramps, and compute WCAG 2.x contrast ratios — pure math, no UI.

```
Python 3.9+ · standard library only · zero runtime dependencies
```

## Install

```sh
pip install -e .
hexflux --version
```

## Usage

```
usage: hexflux [--json] COLOR
       hexflux [--json] COLOR1 COLOR2
       hexflux [--json] --shade AMOUNT COLOR
       hexflux [--json] --tint AMOUNT COLOR
       hexflux [--json] --ramp STEPS COLOR
       hexflux [--json] --invert COLOR
       hexflux [--json] --fg COLOR
```

### Flag summary

| Flag | Meaning |
|------|---------|
| `--shade AMOUNT COLOR` | mix COLOR toward black by AMOUNT (0.0–1.0) |
| `--tint AMOUNT COLOR` | mix COLOR toward white by AMOUNT (0.0–1.0) |
| `--ramp STEPS COLOR` | gradient from black through COLOR to white |
| `--invert COLOR` | invert COLOR on the RGB cube |
| `--fg COLOR` | pick white or black as an accessible foreground |
| `--json` | emit JSON instead of human text |
| `--version` / `--help` | version / help |

Accepted color forms: `#abc`, `#aabbcc`, `abc`, `aabbcc`, `0x…`,
`rgb(r,g,b)`, `rgba(r,g,b,a)` (with alpha), percentage channels, and
`hsl(h,s%,l%)` / `hsla(h,s%,l%,a)`.

Exit status: `0` success, `1` malformed color or value, `2` usage error.
A leading `#` is a shell comment, so quote colors that start with it.

## Examples (real output)

Inspect a color:

```console
$ hexflux '#3366ff'
hex: #3366ff
rgb: (51, 102, 255)
hsl: hsl(225, 100%, 60%)
hsv: hsv(225, 80%, 100%)
luminance: 0.1743
contrast vs white: 4.68
contrast vs black: 4.49
```

Contrast between two colors, with WCAG AA / AAA verdicts:

```console
$ hexflux '#ffffff' '#ff0000'
#ffffff vs #ff0000: contrast 4.00
AA (4.5): fail
AAA (7.0): fail
```

Pick an accessible foreground:

```console
$ hexflux --fg '#555555'
background: #555555
foreground: #ffffff
contrast: 7.46
AA (4.5): pass
AAA (7.0): pass
```

Shade, tint, ramp and invert:

```console
$ hexflux --shade 0.5 '#808080'
shade(0.5): #404040

$ hexflux --tint 0.5 '#808080'
tint(0.5): #c0c0c0

$ hexflux --ramp 5 '#3366ff'
ramp(5):
#000000
#1a3380
#3366ff
#99b2ff
#ffffff

$ hexflux --invert '#3366ff'
invert: #cc9900
```

Machine-readable output:

```console
$ hexflux --json '#ff0000'
{
  "contrast_black": 5.25,
  "contrast_white": 4.0,
  "hex": "#ff0000",
  "hsl": [
    0.0,
    1.0,
    0.5
  ],
  "hsv": [
    0.0,
    1.0,
    1.0
  ],
  "luminance": 0.2126,
  "rgb": [
    255,
    0,
    0
  ]
}
```

Errors go to stderr and set the exit status:

```console
$ hexflux '#zzz'; echo $?
hexflux: unsupported color form '#zzz'
1
```

## How WCAG contrast works (the short version)

WCAG 2.x defines *relative luminance* `L` for a color: each sRGB channel is
linearized, then weighted by its contribution to human brightness —

```
l = 0.2126·lin(r) + 0.7152·lin(g) + 0.0722·lin(b)
        lin(c) = c/12.92            if c ≤ 0.03928
               = ((c+0.055)/1.055)^2.4  otherwise
```

The *contrast ratio* between two colors is

```
contrast = (L₁ + 0.05) / (L₂ + 0.05)   with L₁ ≥ L₂
```

which ranges from 1 (identical) to 21 (black vs white). WCAG AA requires
`≥ 4.5` for normal text (`≥ 3` for large text); AAA requires `≥ 7`. hexflux
reports those exact numbers and, for `--fg`, chooses the white/black text that
clears the ratio — preferring white when both do.

## Development

```sh
python3 -m unittest discover -s tests -v
```

The test suite pins concrete values (e.g. `shade('#808080', 0.5) → #404040`,
white/black contrast `21.0`, mid-gray `#808080` luminance ≈ `0.2159`), and
drives the CLI through `subprocess` to verify output, JSON payloads and exit
codes.

## License

MIT © 2026 Conedope