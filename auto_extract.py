import os
import json
import requests
import anthropic

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

# English articles to scrape phrases from
ARTICLE_URLS = [
    "https://www.bbc.com/news",
    "https://www.theguardian.com/world",
]

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def fetch_article_text(url):
    """Fetch plain text content from a URL."""
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        # Simple text extraction (strip HTML tags)
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self.skip = False

            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style", "nav", "footer"):
                    self.skip = True

            def handle_endtag(self, tag):
                if tag in ("script", "style", "nav", "footer"):
                    self.skip = False

            def handle_data(self, data):
                if not self.skip and data.strip():
                    self.text.append(data.strip())

        extractor = TextExtractor()
        extractor.feed(response.text)
        return " ".join(extractor.text)[:3000]  # Limit to 3000 chars
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""


def extract_phrases_with_claude(text):
    """Use Claude API to extract useful English phrases from article text."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = f"""Extract 3-5 useful English phrases, idioms, or expressions from the following article text that would be valuable for vocabulary building.

For each phrase, provide:
- phrase: the exact phrase or expression
- meaning: a clear, concise explanation
- example: a natural example sentence (can be from the article or your own)
- category: one of [Idiom, Slang, Business, Casual, Academic]
- difficulty: one of [Beginner, Intermediate, Advanced]

Respond ONLY with a valid JSON array. No preamble, no markdown.

Article text:
{text}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    return json.loads(raw)


def get_existing_phrases():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    response = requests.post(url, headers=NOTION_HEADERS)
    response.raise_for_status()
    results = response.json().get("results", [])
    return {
        page["properties"]["Phrase"]["title"][0]["text"]["content"].lower()
        for page in results
        if page["properties"]["Phrase"]["title"]
    }


def add_phrase_to_notion(phrase_data):
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Phrase": {"title": [{"text": {"content": phrase_data["phrase"]}}]},
            "Meaning": {"rich_text": [{"text": {"content": phrase_data.get("meaning", "")}}]},
            "Example Sentence": {"rich_text": [{"text": {"content": phrase_data.get("example", "")}}]},
            "Category": {"select": {"name": phrase_data.get("category", "Casual")}},
            "Difficulty": {"select": {"name": phrase_data.get("difficulty", "Intermediate")}},
            "Status": {"select": {"name": "New"}},
        },
    }
    response = requests.post(url, headers=NOTION_HEADERS, json=payload)
    response.raise_for_status()


def notify_slack(added_phrases):
    if not added_phrases:
        return
    lines = [f"🤖 *Daily auto-extract: {len(added_phrases)} new phrase(s) added!*\n"]
    for p in added_phrases:
        lines.append(f"• *{p['phrase']}* — {p['meaning']}")
    requests.post(SLACK_WEBHOOK_URL, json={"text": "\n".join(lines)})


def main():
    existing = get_existing_phrases()
    all_added = []

    for url in ARTICLE_URLS:
        print(f"Fetching: {url}")
        text = fetch_article_text(url)
        if not text:
            continue

        print("Extracting phrases with Claude...")
        try:
            phrases = extract_phrases_with_claude(text)
        except Exception as e:
            print(f"Extraction failed: {e}")
            continue

        for phrase_data in phrases:
            if phrase_data["phrase"].lower() not in existing:
                add_phrase_to_notion(phrase_data)
                all_added.append(phrase_data)
                existing.add(phrase_data["phrase"].lower())
                print(f"✅ Added: {phrase_data['phrase']}")
            else:
                print(f"⏭️  Skipped: {phrase_data['phrase']}")

    notify_slack(all_added)
    print(f"\nDone! {len(all_added)} phrase(s) added.")


if __name__ == "__main__":
    main()
