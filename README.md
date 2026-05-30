# 📚 Vocab Bot

English vocabulary builder that syncs phrases to Notion and notifies via Slack.

## How it works

| Trigger | Action |
|--------|--------|
| `phrases.json` updated & pushed | Syncs new phrases to Notion + Slack notification |
| Every day at 9:00 AM JST | Auto-extracts phrases from English articles → Notion + Slack |

## Setup

### 1. GitHub Secrets
Go to your repo → Settings → Secrets and variables → Actions, and add:

| Secret | How to get it |
|--------|--------------|
| `NOTION_TOKEN` | [Notion integrations page](https://www.notion.so/my-integrations) → Create integration → copy Internal Integration Token |
| `NOTION_DATABASE_ID` | Open your Notion database → copy the ID from the URL (the 32-char string after the last `/`) |
| `SLACK_WEBHOOK_URL` | [Slack API](https://api.slack.com/apps) → Create App → Incoming Webhooks → copy URL |
| `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com/) → API Keys |

### 2. Connect Notion Integration to your database
In Notion: open your Phrase Bank database → ··· menu → Connections → add your integration.

### 3. Add phrases manually
Edit `phrases.json` and push:
```json
[
  {
    "phrase": "your phrase here",
    "meaning": "what it means",
    "example": "example sentence",
    "category": "Idiom",
    "difficulty": "Intermediate"
  }
]
```

### 4. Trigger daily extract manually (optional)
GitHub → Actions tab → "Daily phrase auto-extract" → Run workflow
