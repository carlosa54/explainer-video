# Capturing real screens

Real screenshots of the user's apps (dashboards, task pages, pull requests) are proof that a diagram is true. Capture them **read-only**: the video shows the system, it does not exercise it.

## Logins

The user signs in; you never handle their credentials.

1. Ask the user to launch a browser in their own desktop session with a remote-debugging port and a throwaway profile, then sign in to each app:
   ```sh
   open -na "Google Chrome" --args --user-data-dir="$PWD/build/browser-profile" \
     --remote-debugging-port=9333 --no-first-run --window-size=1920,1080 "https://app.example/…"
   ```
   On Linux, run `google-chrome` with the same flags.
2. Attach over CDP to `127.0.0.1:9333` with your browser tool (Playwright `connect_over_cdp`, an agent-browser `connect 9333`, or similar) and confirm the open tabs with `curl -s 127.0.0.1:9333/json/list`.
3. Disconnect when done, and tell the user they can close the window.

A browser that an agent launches from a background job often has no visible window, or closes when the agent relaunches it. Once the user is looking at a window, leave it alone: a "close and relaunch" step shuts the window they are signing in to.

## What read-only allows

- Allowed: switching tabs, opening existing pages, changing a dashboard's time range, opening a form and cancelling it, reading page text to confirm what a screen shows.
- Not allowed: submitting forms, starting tasks or workflows, changing settings or defaults, merging, deleting.
- If a shot needs a state that doesn't exist (a busy queue, a failed run), ask the user to create it; don't create it yourself.

## Taking good shots

- A 1920×1080 window captured at device pixel ratio 2 gives crisp 3840-wide images that survive a 3× camera zoom.
- Pick time ranges that have data: a 24-hour panel that only has data for the last few hours looks broken, so the 1-hour view is the better shot.
- Read the page text alongside the shot, so the narration quotes real numbers ("from 3.4 s to 0.7 s") rather than guessing from pixels.
- Check every shot for secrets, tokens, personal data, and internal hostnames or IPs before it goes in the video. Crop or blur in the image; a spotlight that dims a region does not hide it.
- Copy the shots into the project's `screens/` immediately: scratch directories get cleaned up.
- Record what each shot shows and when it was taken (for example "metrics dashboard, last hour, captured 14:40"), for the result notes.
