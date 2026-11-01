# Using this kit

Copy this folder into your local BrandGuard repo (for example `design/brandguard-latest/`). Give Codex CODEX-PROMPT.md, adjusting the relative path to BRAND-KIT.md if needed.

- BRAND-KIT.md: latest design/behavior specification.
- CODEX-PROMPT.md: compact implementation prompt.
- reference.html: current standalone frontend; open visually rather than reading its embedded image data into model context.
- assets/silver-waves.jpg: exact approved recreated background.
- assets/wave-renderer-reference.js: current wave renderer for adaptation.

The standalone reference uses local demo data and redirects real auth to the original app. These are preview limitations to replace with the local repo's real integrations, not features to preserve. The admin-password UI currently demonstrates required-field behavior only; backend verification must be implemented/reused securely in the target repo.

Latest signup requirement supersedes earlier Creator-only audits. This kit retains animated waves, not the previously requested static variant.
