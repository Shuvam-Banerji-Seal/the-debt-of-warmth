# The Calendar of Cindermere

*The following is the reckoning used in the Clay March, in Ond, and in every ledger that hopes to be taken seriously. The cantons count by tides and the Weald-born refuse to count at all.*

---

## The year

A year is **365 days**: twelve months of **thirty days** each, followed by **five holy days** that belong to no month and no week. The twelve months are gathered into four seasons of three months each. A week is **six days** long.

### The months

| Number | Month | Season | Meaning and work |
|---|---|---|---|
| 1 | Fasten | the Thaw | Winter loosening; repairs, no planting |
| 2 | Brook | the Thaw | The frost breaks; the Gyle rises |
| 3 | Silt | the Thaw | Planting; muddy roads; eel traps; birth month |
| 4 | Grow | the Grow | Barley and peas; washing; bees |
| 5 | Hay | the Grow | Haymaking; flax; first kiln preparation |
| 6 | Kiln | the Grow | The great firing; lead-glaze work |
| 7 | Glean | the Reap | Reaping; first bread of the new grain |
| 8 | Rook | the Reap | Flocks; gleaning; the last of the ale |
| 9 | Rot | the Reap | Leaf-fall; rot; the silt thickens in houses |
| 10 | Fell | the Still | Slaughter; pigs killed; first hard frost |
| 11 | Tallow | the Still | Candle-making; deep winter; winter fever |
| 12 | Wold | the Still | Longest nights; names of the dead spoken |

**The seasons:** the **Thaw** (Fasten, Brook, Silt), the **Grow** (Grow, Hay, Kiln), the **Reap** (Glean, Rook, Rot), the **Still** (Fell, Tallow, Wold). A clay-marcher says *in the Thaw*, *in the Grow*, *at the Reap*, *in the Still*, and rarely names a month unless a debt is attached to it.

### The six days of the week

In order: **Milkday, Sund, Tideday, Gloamday, Roodday, Stillday**. Milkday is the first day of work; Stillday is the day of rest in the March and the day of the household account in Ond. Because a month is thirty days and a week is six, **every month begins on a Milkday**. This is deliberate, and it is how a clerk checks a copy of the Ledger without doing sums.

### The five holy days

These come after Wold 30 and before the next Fasten. They are outside the week; the weekday sequence resumes at Milkday afterwards.

1. **Ashenday** — the First Crack remembered. Bells are rung at dawn and no staple is set.
2. **the Naming** — the names of the household dead are spoken aloud once each. The cantons observe it at low water.
3. **the Reckoning** — debts are settled or carried forward with the tenth added. The Factors of Ond read the Ledger in the Cinder Quays.
4. **the Sealing** — the great feast of the Mending, when the year's dead are repaired together in the House at Ond. It is the holiest day in the world.
5. **the Hush** — a day of silence for the un-Mended. No work, no bells, no names. In the March the grey silt is swept out of every house on the morning after, and not before.

---

## Era naming

Years are counted in the **Ashen Reckoning (AR)**, from the year of the First Mending. Events before it are said to be *before the Ash*, or, in the schools, **the Unreckoned**. The current year is **AR 431**. The Reckoning is divided into ages that the schools use and the March ignores:

- **Age of Farriers** — AR 1–83
- **Mending Peace** — AR 84–230
- **Broken Century** — AR 231–329
- **Sealed Age** — AR 330–431 (the present age)

A person in Kilnwick says *this year* or *the year the bridge went* and only uses AR when speaking to an Ond clerk.

---

## The mapping rule

**Day 1 is the day Wren Sedge is born in Kilnwick: Silt 9, AR 431, a Tideday.** It is the same night, in another world, that Nell Rill goes down the cellar stair in Cauldwick. The two dates are not the same season and are not meant to be; the correspondence is of events, not weather. Every Day N after that is one day later in Cindermere reckoning, with no gaps and no skipped days.

### Computing any later date

Let N be the day number, N 1 or greater.

1. **Year:** Y = 431 + floor((N-1) / 365).
2. **Day of year:** r = ((N-1) mod 365) + 1.
3. If r is 1 through 360, the ordinary calendar applies:
   - month number M = floor((r-1) / 30) + 1, giving the month from the table above;
   - day of month D = ((r-1) mod 30) + 1;
   - weekday index = (D-1) mod 6, where 0 Milkday, 1 Sund, 2 Tideday, 3 Gloamday, 4 Roodday, 5 Stillday.
4. If r is 361 through 365, the date is one of the five holy days: 361 Ashenday, 362 Naming, 363 Reckoning, 364 Sealing, 365 Hush. It has no weekday.

**Working backwards** from a date (Y, M, D) in an ordinary month:

N = (Y-431) times 365 + (M-1) times 30 + D.

For a holy day h (1 Ashenday through 5 Hush) in year Y:

N = (Y-431) times 365 + 360 + h.

**Worked example.** Day 366: Y = 431 + floor(365/365) = 432; r = 1; M = 1; D = 1; weekday index 0, so Day 366 is Fasten 1, AR 432, Milkday. Day 60 is Hay 8, AR 431, Sund. Day 1 is Silt 9, AR 431, Tideday. Each of the first sixty days is set out below so the rule can be checked by hand.

---

## The first sixty days

| Day | In-world date | Weekday | Season and work |
|---|---|---|---|
| 1 | Silt 9, AR 431 | Tideday | Thaw; planting; river high after a wet Brook |
| 2 | Silt 10, AR 431 | Gloamday | Thaw; barley goes in on the higher ground |
| 3 | Silt 11, AR 431 | Roodday | Thaw; the clay pits begin to drain |
| 4 | Silt 12, AR 431 | Stillday | Thaw; household account, no heavy work |
| 5 | Silt 13, AR 431 | Milkday | Thaw; oxen shod at Veyford |
| 6 | Silt 14, AR 431 | Sund | Thaw; the Gyle falls a little |
| 7 | Silt 15, AR 431 | Tideday | Thaw; birds scared off the new grain |
| 8 | Silt 16, AR 431 | Gloamday | Thaw; washing begins again at the bank |
| 9 | Silt 17, AR 431 | Roodday | Thaw; kiln-wasters carted out |
| 10 | Silt 18, AR 431 | Stillday | Thaw; the Hearthrite prayer said at the threshold |
| 11 | Silt 19, AR 431 | Milkday | Thaw; the road to Clayholt passable |
| 12 | Silt 20, AR 431 | Sund | Thaw; eel traps set below the bluff |
| 13 | Silt 21, AR 431 | Tideday | Thaw; first peas sown |
| 14 | Silt 22, AR 431 | Gloamday | Thaw; the river–road mended for a day's wage |
| 15 | Silt 23, AR 431 | Roodday | Thaw; salt sacks come up from Saltham |
| 16 | Silt 24, AR 431 | Stillday | Thaw; a quiet day, the washing line still |
| 17 | Silt 25, AR 431 | Milkday | Thaw; the midwife goes to Barrow Wick |
| 18 | Silt 26, AR 431 | Sund | Thaw; the kiln repaired against Kiln month |
| 19 | Silt 27, AR 431 | Tideday | Thaw; the last of the winter pottage eaten |
| 20 | Silt 28, AR 431 | Gloamday | Thaw; turnips lifted from the pits |
| 21 | Silt 29, AR 431 | Roodday | Thaw; the Gyle muddy and rising again |
| 22 | Silt 30, AR 431 | Stillday | Thaw; month's end, the account written down |
| 23 | Grow 1, AR 431 | Milkday | Grow; the new month; oxen to the plough |
| 24 | Grow 2, AR 431 | Sund | Grow; barley hoed |
| 25 | Grow 3, AR 431 | Tideday | Grow; the boat goes down to Veyford |
| 26 | Grow 4, AR 431 | Gloamday | Grow; bees in the clay hedges |
| 27 | Grow 5, AR 431 | Roodday | Grow; flax sown |
| 28 | Grow 6, AR 431 | Stillday | Grow; the household silt swept and burnt |
| 29 | Grow 7, AR 431 | Milkday | Grow; whey and green cheese made |
| 30 | Grow 8, AR 431 | Sund | Grow; washing dried stiff in the wind |
| 31 | Grow 9, AR 431 | Tideday | Grow; the river road dusty for the first time |
| 32 | Grow 10, AR 431 | Gloamday | Grow; turnip tops cut for greens |
| 33 | Grow 11, AR 431 | Roodday | Grow; eel nets mended |
| 34 | Grow 12, AR 431 | Stillday | Grow; a quiet day |
| 35 | Grow 13, AR 431 | Milkday | Grow; clay dug for the first firing |
| 36 | Grow 14, AR 431 | Sund | Grow; the boats go down with pots |
| 37 | Grow 15, AR 431 | Tideday | Grow; oxen shod again |
| 38 | Grow 16, AR 431 | Gloamday | Grow; the midwife called out at Mire End |
| 39 | Grow 17, AR 431 | Roodday | Grow; salt bread baked |
| 40 | Grow 18, AR 431 | Stillday | Grow; the washing line empty |
| 41 | Grow 19, AR 431 | Milkday | Grow; peas gathered |
| 42 | Grow 20, AR 431 | Sund | Grow; the old kiln oiled |
| 43 | Grow 21, AR 431 | Tideday | Grow; children sent to the river bank |
| 44 | Grow 22, AR 431 | Gloamday | Grow; the Gyle low enough to ford |
| 45 | Grow 23, AR 431 | Roodday | Grow; the reeve counts the road-work days |
| 46 | Grow 24, AR 431 | Stillday | Grow; a quiet day |
| 47 | Grow 25, AR 431 | Milkday | Grow; barley ear shows |
| 48 | Grow 26, AR 431 | Sund | Grow; the boat from Veyford brings a groat's worth of iron |
| 49 | Grow 27, AR 431 | Tideday | Grow; washing in the sun |
| 50 | Grow 28, AR 431 | Gloamday | Grow; the flax ripens |
| 51 | Grow 29, AR 431 | Roodday | Grow; the last hay of the old year used |
| 52 | Grow 30, AR 431 | Stillday | Grow; month's end, ledger-ruled paper folded away |
| 53 | Hay 1, AR 431 | Milkday | Grow; scythes ground at the smithy |
| 54 | Hay 2, AR 431 | Sund | Grow; the first hay cut |
| 55 | Hay 3, AR 431 | Tideday | Grow; hay carted before the rain |
| 56 | Hay 4, AR 431 | Gloamday | Grow; the clay seam at Clayholt opened |
| 57 | Hay 5, AR 431 | Roodday | Grow; flax pulled and steeped |
| 58 | Hay 6, AR 431 | Stillday | Grow; a quiet day, the ovens banked |
| 59 | Hay 7, AR 431 | Milkday | Grow; hay stacked, the kiln ready |
| 60 | Hay 8, AR 431 | Sund | Grow; pots stacked and the kiln swept ready for the firing |
