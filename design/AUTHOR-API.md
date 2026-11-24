# Author API: what you may use in scene files

Scene files are body text compiled inside the book class `design/chronicle.cls`. Only the following markup is supported. Anything else may break the build, and the orchestrator will hand the error back to you to fix.

## Text
| Markup | Use |
|---|---|
| blank line | new paragraph |
| `\emph{...}` / `\textit{...}` | emphasis, foreign words, ship names, inner voice |
| `\textsc{...}` | small capitals (signs, shouted titles) |
| `\textbf{...}` | almost never |
| `---` or `—` | em dash |
| “ ” ‘ ’ | typographic quotes (preferred); `` ``like this'' `` also works |
| `\ldots` or … | ellipsis |

## Story devices
| Macro | Prints as |
|---|---|
| `\dropcap{W}{hen the}` | a decorated red capital, then small caps. Use it **only** as the first thing in scene 1 of a chapter, and make that first paragraph at least three lines long (a one-line paragraph collides with the capital). |
| `\scenebreak` | a centred fleuron between sections of a scene |
| `\memory{...}` | italic, for remembered words from the past life |
| `\sound{...}` | small caps, for bells, horns or shouted names |
| `\inscription{...}` | spaced capitals, for carved or engraved words |
| `\letterhand{...}` | an indented italic block, for letters and notes |
| `\begin{verseblock} line one\\ line two \end{verseblock}` | songs, prayers, verse; `\\` ends a line |

## Index (required)
| Macro | Effect |
|---|---|
| `\person{Name}` | prints Name; indexes it under Persons |
| `\person[Canonical Name]{shown text}` | prints the shown text, indexes under the canonical name |
| `\place{Name}`, `\place[Canonical]{shown}` | Places index |
| `\lore{term}`, `\lore[Canonical]{shown}` | Lore, Powers & Things index (spells, ranks, artefacts, institutions, creatures, customs) |

Wrap the **first mention in each scene** of every named person, place and lore term. Do not wrap later mentions in the same scene.

## Forbidden in scene files
`\chapter`, `\section`, `\documentclass`, `\usepackage`, `\begin{document}`, `\input`, `\newcommand`, `\def`, `%` comments, `$...$` math, `\newpage`, and any macro not listed above.
