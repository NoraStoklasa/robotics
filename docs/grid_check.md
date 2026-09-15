# Grid Check

## Grid
- Shape: `(40, 40)`
- Unique values: `[0, 1]`
- Metadata: `40 rows x 40 cols`
- Resolution: `0.1 m/cell`
- Encoding: `0 = free`, `1 = obstacle`

## Conversion
- 1600-cell round-trip failures: `0`
- World-coordinate sweep failures/out-of-bounds: `0`

## Starts
| ID | World `(x, y)` | Grid `(row, col)` | In bounds | Free cell |
|---|---:|---:|---|---|
| A | `(-1.45, 0.00)` | `(20, 5)` | True | True |
| B | `(0.00, -1.45)` | `(34, 20)` | True | True |
| C | `(1.45, 0.90)` | `(11, 34)` | True | True |

## Station Observe Positions
| ID | World `(x, y)` | Grid `(row, col)` | In bounds | Free cell |
|---|---:|---:|---|---|
| S1 | `(-1.42, 1.25)` | `(7, 5)` | True | True |
| S2 | `(-0.65, 0.57)` | `(14, 13)` | True | True |
| S3 | `(1.15, 1.42)` | `(5, 31)` | True | True |
| S4 | `(0.37, 0.45)` | `(15, 23)` | True | True |
| S5 | `(1.42, -0.55)` | `(25, 34)` | True | True |
| S6 | `(0.55, -0.82)` | `(28, 25)` | True | True |
| S7 | `(-0.95, -1.42)` | `(34, 10)` | True | True |
| S8 | `(-0.87, -0.45)` | `(24, 11)` | True | True |

## Overlay
- Generated overlay: `docs/data/grid_overlay.png`
- Manually compared with `maps/world_layout.png`.
