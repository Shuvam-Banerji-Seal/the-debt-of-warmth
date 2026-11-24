TASK: PLAN CHAPTER $n (book/chapters/$chdir/)

You are about to write Chapter $n of an endless saga. First rebuild your memory. Read, in this order:
1. design/STYLE-REFERENCE.md, bible/voice.md, bible/premise.md and bible/magic.md
2. memory/state.md (the present moment)
3. plan/next.md, plan/arcs.md, plan/threads.md
4. memory/story-so-far.md
5. Recent chapter summaries: $prev_summaries
6. The end of the previous chapter: $last_scene
7. The character sheets (characters/*.md) of everyone likely to appear, and characters/_minor.md
8. Whatever bible files and memory/places.md entries the chapter touches

Then create two files:

A) `book/chapters/$chdir/meta.json`: valid JSON following design/templates/chapter-meta.json exactly.
   - "number": $n
   - "days": "start" must be $day_rule. **Every single day in the range will be on the page**, opened by its own \daymark and lived for at least 800 words: no day skipped or summarised. A normal chapter spans 1 to 3 days. A "passage" chapter ("mode": "passage") spans at most 7 days, each still fully present.
   - Plan 4 to 8 scenes, each with "target_words" between 2200 and 4500. Every scene must have a real dramatic purpose. The chapter totals at least 12,000 words.
   - "characters": slugs of everyone on stage (existing sheets, or new slugs you will create when closing the chapter).
   - "arc": the current arc from plan/arcs.md (number, title, subtitle).
   - A fresh in-world epigraph that resonates with the chapter.

B) `book/chapters/$chdir/plan.md`: a detailed beat sheet. For each scene: day and time, place, who is present, the beats in order, the emotional turn, the sensory anchors, which threads (by ID) advance, what foreshadowing is planted or paid off, and the exact last image. End with how the chapter's final moment pulls into the next chapter.

The chapter must move the story: at least one meaningful change, one thread advanced, and texture of daily life (work, food, weather, bodies, money, faith). Across chapters, keep the balance the saga needs: danger and violence, training and honest growth of power (tracked in memory/state.md, consistent with bible/magic.md), relationships, mystery and the pull of the past life. Do not end the story or any arc prematurely. Reply with one line: the chapter title.
