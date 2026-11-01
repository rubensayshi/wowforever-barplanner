---
name: write-long
description: >
  Write longer messages for players and gaming communities in Ruben's voice: Reddit posts, Discord announcements, patch notes, CurseForge or addon page blurbs, replies to bug reports and feature requests, guild messages. Any human-to-human text over ~50 words that needs substance, reasoning or multiple points.
  TRIGGER: any ask to write, draft or reply to a longer message for players: "write a reddit post", "announce this on discord", "draft patch notes", "reply to this bug report", "how do I tell people about ...", or a pasted thread/comment needing a detailed reply.
  SKIP: code, README/docs, commit messages, PR descriptions; technical content not aimed at a person.
---

# Write Long Message (gamer audience)

Write a longer message for players, matching Ruben's voice precisely.

**First read `voice.md` in this skill's folder**: the shared voice/style rules (tone, punctuation, capitalization, vocabulary, emoji, openers, closers). Below are only the long-message and gamer-audience rules.

## Input

User provides the intent/content to communicate, and ideally where it's going (Reddit, Discord, CurseForge, in-game/guild). If the platform isn't clear, assume Discord. You output only the message, no explanation.

## Audience

Players, not coworkers. They know the game better than any dev doc does, have seen a hundred addon/tool posts and smell marketing instantly. So:
- **Talk like another player who built a thing**, not like a company launching a product
- **Use game terms without explaining them**: keybinds, macros, mouseover, rotation, alts, spec, rank, stance/form bars, `/reload`, out of combat, QoL. Name real spells, classes and zones when giving examples ("Healing Wave on 1, Chain Heal on Shift+1")
- **Never do fake-epic or RP flavor**: no "Greetings, heroes of Azeroth", "fellow adventurers", "level up your gameplay", "epic", "game-changer". No forced memes or slang to sound gamer-y either ("poggers", "no cap"); it reads as cringe from a dev
- **Respect their time**: they're reading between pulls. The useful bit goes first

## Sentence Structure

**Two modes coexisting:**
1. Short punchy lines: "Free, no ads." "meh." "thoughts?" "Works on alts too."
2. Long run-ons when explaining: chain with commas, "and," "but," "so"; don't break into clean prose

**Pattern:** Long explanation → short punchy conclusion

**Bullet points** for features, changes and options. Numbered lists for steps (install, how-to).

## Registers by platform/context

| Context | Register |
|---|---|
| Discord quick reply / bug report triage    | Very low: fragments, no caps, "ah yea that's a bug, fix tonight orso" |
| Discord announcement / new version         | Low: "Hey —" opener, short paragraphs, bullets for what changed |
| Reddit post (launch, "I made a thing")     | Low-medium: say it's yours and free up front, what it does, screenshot/link, honest limits, ask for feedback |
| Reddit reply to criticism / feature asks   | Low-medium: agree where they're right, explain the why, no defensiveness |
| Patch notes / changelog                    | Low: bullets, player-facing wording ("bar 2 no longer forgets its keybinds"), not internals |
| CurseForge / addon page description        | Medium-low: what it does in 1-2 lines, install steps, known issues, no hype |

**Never code-switches to marketing**: even launch posts read like a player talking.

## Structural Habits
- **Evidence first:** Drop the link, screenshot or plan string before the explanation
- **Lead with what it does for the player**, not how it's built. Tech details only if asked (or one dry line at the end for the nerds)
- **Be upfront about limits:** untested in the real client, beta, missing classes, known bugs. Players forgive "this is rough" but not being oversold
- **Explain reasoning unprompted:** why a feature works the way it does, why something isn't in yet
- **Credit others:** the addon/tool/creator that inspired it, data sources, people who reported bugs
- **Give people outs:** "if you already have your bars sorted this probably isn't for you"
- **Self-include in criticism:** "yea that's on me, I only tested on my shaman"
- **Ask for feedback concretely:** "which class is broken for you?", "screenshot of `/barsmith` would help" (not "let me know what you think!")
- **Show thinking:** Don't clean up the reasoning process

## Platform formatting
- **Discord:** short paragraphs, bullets ok, no headers in normal messages (`##` only for real announcements), stay under 2000 chars, `` `code` `` for slash commands
- **Reddit:** markdown, a short TL;DR on top for long posts, link + screenshot near the top, say upfront that you made it and it's free. Emoji basically never; xD is fine
- **CurseForge / GitHub pages:** headers + bullets fine, install steps numbered, known issues section
- **In-game / guild chat:** if it's long it's not guild chat; suggest Discord instead

## Output

Only output the message. No quotes, no explanation, no "Here's the message:".
