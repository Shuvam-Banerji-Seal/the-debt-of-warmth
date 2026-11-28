# The reckoning of days in Sarn

*The Court counts everything. It counts embers, deductions, returns and the years of a debt. It does not count the days a man is warm, which is the one count that matters to him. This file is the rule by which the days in the books are named.*

---

## I. The year

A Sarnish year has **365 days**: twelve months of thirty days, followed by five days outside the months called **the Five Cold Days**, or simply **the Five**. No day is ever added to make the sky agree with the slate. The Court teaches that the Warm holds the seasons in their places, and that the thaw has come in Ilmen for eight hundred years. The Keldish surveyors, who have counted both, do not say so in front of an assessor.

The months, in order, with the Grathic glosses that are used everywhere:

| No. | Month | Gloss | Days of the year |
|---|---|---|---|
| 1 | **Ilmen** | the thaw, the river rising | 1–30 |
| 2 | **Silt** | mud; the Breaking | 31–60 |
| 3 | **Seed** | planting | 61–90 |
| 4 | **Reed** | reed-cutting | 91–120 |
| 5 | **Tallow** | lambing | 121–150 |
| 6 | **Ember** | the kiln month, short fierce summer | 151–180 |
| 7 | **Grain** | harvest | 181–210 |
| 8 | **Smoke** | the second firing | 211–240 |
| 9 | **Frost** | first frosts | 241–270 |
| 10 | **Bone** | hunting and repair | 271–300 |
| 11 | **Ash** | the dark | 301–330 |
| 12 | **Stone** | deep winter, river ice | 331–360 |

The Five follow Stone and belong to no month:

| Ordinal | Name | Observance |
|---|---|---|
| 361 | **Kindling** | Every hearth in Sarn is lit from the Hearth-flame. Collectors take the year's first measure. |
| 362 | **Weighing** | The year's measures are read aloud. The rich learn how whole they are; Low Kiln learns its deduction. |
| 363 | **the Long Night** | No fire after dusk. People sit in the dark and tell the stories of the Return. |
| 364 | **the Remembering** | Names of the dead are spoken. Whole returns are announced in a clean voice. |
| 365 | **the Last Day** | Bread is baked. The grey Ash in the corners is **not** swept away. It is burnt the next morning. |

Other named days:

- **Account-day**, the tenth, twentieth and thirtieth of every month. In Grath these are also market-days; the slate is read at the Cross before the pigs are weighed.
- **the Opening of the Slates**, Ilmen 1. The Court opens the new year's accounts. The first thin returns of the year are announced at the Weighing, not now.
- **the Hearth Drawing**, Stone 12. The first collection of the year; a collector may draw from the dying and from the newly born on the same day.
- **the Fish Blessing**, Ilmen 15. The hearth-maids bless the weirs and the eel traps. In Sill this is done at the Weir, one league upriver. The date is reconciled to the day-count in §III (Day 44, Ilmen 15, Y.H. 813, the Fish Blessing at the Weir); the older Reed 15 gloss was a planting marker and is retired.

### Weeks

A week is a **tend**, ten days long. Every month contains three whole tends: days 1–10, 11–20 and 21–30. The tenth day of each tend is Account-day. The tend-days are Firstday, Secondday, Thirdday, Fourthday, Fifthday, Sixthday, Seventhday, Eighthday, Ninthday and Tenthday.

**The Five are outside the tend.** They have names, not tend-days, and no market is held during them. On Ilmen 1 the count begins again at Firstday. This is why Account-days in the first weeks of a year fall on Ilmen 10, 20 and 30, and why there are three Account-days in the last ten days of Stone before the Five interrupt them.

### Eras

Years are numbered from the lighting of the Hearth: **Y.H. 1** onward. Earlier years are **B.H.**, before the Hearth; the temple calls them the Broken Years and the Keldish call them the Long Want. Scholars use informal names for stretches of the past — the Quiet Centuries (Y.H. 120–300), the Glaze Ages (300–420), the Bowl Years (420–560), the Ash Times (650–700) and the Settlement (after 747). The present year, **Y.H. 812**, is called the Thin Year in Low Kiln, after the Long Cold.

---

## II. The mapping rule

**Day 1 is the day Corin is born in the new world. Its exact in-world date is the seventh day of Stone in the year 812 of the Hearth — Stone 7, Y.H. 812 — a Seventhday, with the Ilm under ice.**

From that day forward, let *N* be the story's day number. Compute:

> *t* = 336 + *N* − 1
>
> *y* = (*t* mod 365) + 1  — the Sarnish day of the year, where 1 = Ilmen 1 and 365 = the Last Day.
>
> *Y* = 812 + floor(*t* / 365)  — the year of the Hearth.

Then:

- If *y* ≤ 360: the month is floor((*y* − 1) / 30) + 1, and the day of the month is ((*y* − 1) mod 30) + 1. The tend-day is ((day of month − 1) mod 10) + 1.
- If *y* is 361 to 365: the date is Kindling, Weighing, the Long Night, the Remembering or the Last Day, in that order, in year *Y*. There is no tend-day.

**Worked examples.** Day 24: *t* = 359, *y* = 360, *Y* = 812 → Stone 30, Tenthday, Y.H. 812. Day 30: *t* = 365, *y* = 1, *Y* = 813 → Ilmen 1, Firstday, Y.H. 813. Day 100: *t* = 435, *y* = 70, *Y* = 813 → Seed 10, Tenthday, Y.H. 813. Day 365: *t* = 700, *y* = 336, *Y* = 813 → Stone 6, Sixthday, Y.H. 813, the day before the first birthday.

For any day not in a month, write the name of the holy day and the year; do not invent a date for the Five. For all other days, write the month, the day of the month and the year, in that order, as *14 Ilmen, Y.H. 813*.

---

## III. The first sixty days

*Days 1–24 are in Stone of Y.H. 812. Day 25–29 are the Five. The era turns on Day 30, which is Ilmen 1 of Y.H. 813. Days 30–59 are Ilmen; Day 60 is Silt 1.*

The second era turns on Day 395, which is Ilmen 1 of Y.H. 814, Firstday. Days 390–394 are the five holy days of Y.H. 813 — Kindling, Weighing, the Long Night, the Remembering and the Last Day — with names and no tend-day and no market. Day 396 is Ilmen 2, Secondday; Day 404 is Ilmen 10, Tenthday, the new year's first Account-day and market. The tend restarts at Firstday on Ilmen 1; the year turned in Chapter 114 with nothing signed, and the first arithmetic of Y.H. 814 was not brought into a day that had not earned it.

| Day | In-world date | Tend-day or holy day | Note |
|---|---|---|---|
| 1 | Stone 7, Y.H. 812 | Seventhday | Corin born in Low Kiln; the stone at his belly is already going cold |
| 2 | Stone 8, Y.H. 812 | Eighthday | |
| 3 | Stone 9, Y.H. 812 | Ninthday | |
| 4 | Stone 10, Y.H. 812 | Tenthday | Account-day and the last market before the Five |
| 5 | Stone 11, Y.H. 812 | Firstday | |
| 6 | Stone 12, Y.H. 812 | Secondday | The Hearth Drawing |
| 7 | Stone 13, Y.H. 812 | Thirdday | |
| 8 | Stone 14, Y.H. 812 | Fourthday | |
| 9 | Stone 15, Y.H. 812 | Fifthday | |
| 10 | Stone 16, Y.H. 812 | Sixthday | |
| 11 | Stone 17, Y.H. 812 | Seventhday | |
| 12 | Stone 18, Y.H. 812 | Eighthday | |
| 13 | Stone 19, Y.H. 812 | Ninthday | |
| 14 | Stone 20, Y.H. 812 | Tenthday | Account-day |
| 15 | Stone 21, Y.H. 812 | Firstday | |
| 16 | Stone 22, Y.H. 812 | Secondday | |
| 17 | Stone 23, Y.H. 812 | Thirdday | |
| 18 | Stone 24, Y.H. 812 | Fourthday | |
| 19 | Stone 25, Y.H. 812 | Fifthday | |
| 20 | Stone 26, Y.H. 812 | Sixthday | |
| 21 | Stone 27, Y.H. 812 | Seventhday | |
| 22 | Stone 28, Y.H. 812 | Eighthday | |
| 23 | Stone 29, Y.H. 812 | Ninthday | |
| 24 | Stone 30, Y.H. 812 | Tenthday | Account-day; the last market of the year |
| 25 | Kindling, Y.H. 812 | — | The year-fire lit from the Hearth |
| 26 | Weighing, Y.H. 812 | — | The year's measures read aloud in Slate Row |
| 27 | the Long Night, Y.H. 812 | — | No fire after dusk |
| 28 | the Remembering, Y.H. 812 | — | Names of the dead spoken |
| 29 | the Last Day, Y.H. 812 | — | Bread baked; ash left in the corners |
| 30 | Ilmen 1, Y.H. 813 | Firstday | Opening of the Slates; the ice still holds |
| 31 | Ilmen 2, Y.H. 813 | Secondday | |
| 32 | Ilmen 3, Y.H. 813 | Thirdday | |
| 33 | Ilmen 4, Y.H. 813 | Fourthday | |
| 34 | Ilmen 5, Y.H. 813 | Fifthday | |
| 35 | Ilmen 6, Y.H. 813 | Sixthday | |
| 36 | Ilmen 7, Y.H. 813 | Seventhday | |
| 37 | Ilmen 8, Y.H. 813 | Eighthday | |
| 38 | Ilmen 9, Y.H. 813 | Ninthday | |
| 39 | Ilmen 10, Y.H. 813 | Tenthday | Account-day |
| 40 | Ilmen 11, Y.H. 813 | Firstday | |
| 41 | Ilmen 12, Y.H. 813 | Secondday | |
| 42 | Ilmen 13, Y.H. 813 | Thirdday | |
| 43 | Ilmen 14, Y.H. 813 | Fourthday | |
| 44 | Ilmen 15, Y.H. 813 | Fifthday | The Fish Blessing at the Weir |
| 45 | Ilmen 16, Y.H. 813 | Sixthday | |
| 46 | Ilmen 17, Y.H. 813 | Seventhday | |
| 47 | Ilmen 18, Y.H. 813 | Eighthday | |
| 48 | Ilmen 19, Y.H. 813 | Ninthday | |
| 49 | Ilmen 20, Y.H. 813 | Tenthday | Account-day |
| 50 | Ilmen 21, Y.H. 813 | Firstday | |
| 51 | Ilmen 22, Y.H. 813 | Secondday | |
| 52 | Ilmen 23, Y.H. 813 | Thirdday | |
| 53 | Ilmen 24, Y.H. 813 | Fourthday | |
| 54 | Ilmen 25, Y.H. 813 | Fifthday | |
| 55 | Ilmen 26, Y.H. 813 | Sixthday | |
| 56 | Ilmen 27, Y.H. 813 | Seventhday | |
| 57 | Ilmen 28, Y.H. 813 | Eighthday | |
| 58 | Ilmen 29, Y.H. 813 | Ninthday | |
| 59 | Ilmen 30, Y.H. 813 | Tenthday | Account-day; the river begins to stir under the ice |
| 60 | Silt 1, Y.H. 813 | Firstday | Mud; the Breaking may come at any time |

Days continue by the same rule without gap. There is no leap day, no missing day and no year without a Last Day. A passage chapter must give every day its own dated entry; a day is a small vessel and will not be poured into another.
