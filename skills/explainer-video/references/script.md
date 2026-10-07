# Script

## Story

- **A tour of what exists.** For a video about someone's system, open with "This is my X, as it runs today", not a generic "Here's what an X is". Viewers came to see theirs.
- **Teach, don't report.** Cut operator minutiae: internal IDs, row counts, test-run evidence, legacy migration detail, retired hardware, protocol limits that were since removed. They read like an acceptance report and age badly.
- **One showcase beats a list.** A single real example followed end to end (the request, the work, the review, the result) explains more than a feature list.
- **No second recap.** Close with one view of how the parts fit, in a sentence or two.
- **A cut is subtraction.** When asked for a shorter version, remove whole topics rather than compressing every sentence; a 3-minute cut holds about 400 words.

## Claims that go wrong

Read each claim on the facts sheet against these. Each was a real correction from a reviewer.

- **Where it runs is not who can reach it.** "Runs on our own servers" is one claim; "not reachable from outside" is another and needs its own evidence.
- **A copy is not a backup unless it survives the same failure.** Redundancy and backups solve different problems: a mistake is copied too.
- **Arithmetic is not a guarantee.** A capacity calculation gives a ceiling, not measured throughput. An estimate is said as an estimate, or cut.
- **Today versus possible.** Anything not running yet gets its own visual treatment (dashed outline, a "possible addition" badge) and is said aloud as possible.
- **Where computation happens.** Say plainly what runs locally and what goes to an outside provider; viewers assume "self-hosted" means private and offline.
- **Representative screens.** When a screen shows a different but typical instance of the thing narrated (another run of the same job), note it in the result.

## Caption and spoken text

Each segment is `(id, caption, spoken)`; give `(id, text)` when they are the same.

- **caption** is what viewers read: digits, units and symbols (`3 servers`, `40 ms`, `p99`).
- **spoken** is what the voice receives: numbers spelled the way they should be said (`three servers`, `forty milliseconds`), acronyms spaced when they should be spelled (`A P I`).
- Both must have the same sentences in the same order: captions are timed sentence by sentence from the spoken alignment, and `assemble` stops if the counts differ.
- Names the voice mispronounces go in `pronunciations.json` as aliases (`"nginx" → "engine X"`), applied locally before each request, so captions keep the real spelling.

## Length

Natural narration runs about 150 to 165 words per minute, plus pauses. `python -m kit audio` prints the measured rate. If the video runs long, cut words; the kit never speeds audio up, because sped-up voices sound rushed and break the timestamps.
