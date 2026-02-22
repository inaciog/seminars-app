This folder stores the plain HTML fallback mirror for seminars data.

The app regenerates all files after key data mutations.

## Files

- **index.html** — Entry point with links to the main files.
- **recovery.html** — Human-readable backup for emergency recovery. Contains full seminar content (title, abstract, speaker, room, logistics), speaker bios, speaker suggestions, and links to uploaded files. Use this to recover information if the app stops working.
- **changelog.html** — Technical/audit tracking: semester plans, slots, suggestions, seminars, files, and recent activity.
- **files/** — Copies of all uploaded files (CVs, papers, etc.) for recovery.

## Git push

Set `FALLBACK_MIRROR_GIT_ENABLED=true` in `.env` to commit and push this folder to GitHub after each update.
