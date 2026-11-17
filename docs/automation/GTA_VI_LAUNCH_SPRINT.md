# ODEVI GTA VI — launch sprint

## Launch-week site content
- Public feed is `data/gta-news.json`; only `status: published` appears on the homepage.
- Short-form video feed is `data/gta-shorts.json`; it stays empty until we have owned, authorized or embeddable clips.
- The countdown points to 19 November 2026, as shown by Rockstar at the time of this update.

## Safe automatic scouting
The GitHub Actions workflow `.github/workflows/gta-vi-news-scout.yml` runs every six hours and can also be run manually. It searches Google News RSS for Rockstar Newswire items, follows the article redirect, and accepts only final URLs on Rockstar-owned domains.

New discoveries are written as `draft` entries. They do not appear publicly until an editor writes an original Portuguese summary and changes the status to `published`. This avoids auto-publishing unreviewed or incorrectly attributed material.

## What still requires credentials / human setup
- OpenAI API key is not configured. ChatGPT subscription and n8n assistant credits are not an OpenAI API key.
- Telegram bot and chat are not configured.
- The scout workflow uses GitHub Actions' built-in token; no third-party secret is required.
- Enable GitHub Actions for the repository if it is disabled, then run **ODEVI GTA VI News Scout** once manually to test. Scheduled runs follow every six hours.
- n8n is not required for this first launch-week scout. It can be connected later for AI writing and Telegram.

## Launch-day editorial checklist
1. Verify launch status from Rockstar and platform support.
2. Publish only official facts with direct sources.
3. Label rumours and community theories clearly; never treat them as official.
4. Publish only videos owned by ODEVI, authorized by creators, or embedded using platform-approved URLs.
5. Check countdown, mobile layout, links, social sharing metadata and accessibility on iPhone and desktop.

## Independence
ODEVI+ is an independent fan/community portal and is not affiliated with or endorsed by Rockstar Games. GTA and Grand Theft Auto are trademarks of their respective owners.
