import json
import os
import requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def get_existing_phrases():
    """Fetch all existing phrases from Notion to avoid duplicates."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    response = requests.post(url, headers=HEADERS)
    response.raise_for_status()
    results = response.json().get("results", [])
    return {
        page["properties"]["Phrase"]["title"][0]["text"]["content"].lower()
        for page in results
        if page["properties"]["Phrase"]["title"]
    }


def add_phrase_to_notion(phrase_data):
    """Add a single phrase to the Notion database."""
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Phrase": {
                "title": [{"text": {"content": phrase_data["phrase"]}}]
            },
            "Meaning": {
                "rich_text": [{"text": {"content": phrase_data.get("meaning", "")}}]
            },
            "Example Sentence": {
                "rich_text": [{"text": {"content": phrase_data.get("example", "")}}]
            },
            "Category": {
                "select": {"name": phrase_data.get("category", "Casual")}
            },
            "Difficulty": {
                "select": {"name": phrase_data.get("difficulty", "Intermediate")}
            },
            "Status": {
                "select": {"name": "New"}
            },
        },
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()


def notify_slack(added_phrases):
    """Send a Slack notification with the newly added phrases."""
    if not added_phrases:
        return
    lines = [f"📚 *{len(added_phrases)} new phrase(s) added to Notion Vocab Bank!*\n"]
    for p in added_phrases:
        lines.append(f"• *{p['phrase']}* — {p['meaning']}")
    payload = {"text": "\n".join(lines)}
    requests.post(SLACK_WEBHOOK_URL, json=payload)


def main():
    with open("phrases.json", "r") as f:
        phrases = json.load(f)

    existing = get_existing_phrases()
    added = []

    for phrase_data in phrases:
        if phrase_data["phrase"].lower() not in existing:
            add_phrase_to_notion(phrase_data)
            added.append(phrase_data)
            print(f"✅ Added: {phrase_data['phrase']}")
        else:
            print(f"⏭️  Skipped (already exists): {phrase_data['phrase']}")

    notify_slack(added)
    print(f"\nDone! {len(added)} phrase(s) added.")


if __name__ == "__main__":
    main()
