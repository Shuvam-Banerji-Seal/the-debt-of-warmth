TASK: WRITE SCENE $k of $total, CHAPTER $n: file `book/chapters/$chdir/scene-$kk.tex`

Read first:
- book/chapters/$chdir/meta.json and book/chapters/$chdir/plan.md (your plan for this scene: "$scene_title")
- design/STYLE-REFERENCE.md and bible/voice.md (the binding voice; re-read both every time)
- memory/state.md
- $prev_text
- The character sheets (characters/<slug>.md) of everyone in this scene, especially their Voice & Manner
- Any bible or memory/places.md entries this scene touches

Then write the complete scene as LaTeX body text in `book/chapters/$chdir/scene-$kk.tex`, following AGENTS.md section 4 and design/AUTHOR-API.md:
- Length: at least $min_words words, aiming for about $target words. Dramatise fully: dialogue, action, interiority, setting and consequence. Earn every paragraph; never pad.
- $opening
- Index the first mention in this scene of every named person, place and lore term with \person{} \place{} \lore{}.
- Continue seamlessly from where the previous text stops. Do not recap and do not add a heading.
- Prose must be beautiful, rustic and metaphorical, with varied rhythm and concrete senses.
- If the scene is long, write it in two or three parts: create the file with the first part, then append the next parts. Check the result with `wc -w`.

Write only this one scene. Reply with one line: the word count.
