import os
import requests
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.theguardian.com/world/rss",
]

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

COMMON_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "is", "are", "was", "were", "be", "been", "have", "has", "do", "does",
    "did", "can", "could", "will", "would", "should", "may", "might", "must",
    "about", "after", "before", "from", "into", "through", "this", "that", "these",
    "those", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "its", "our", "their", "what", "which", "who",
    "when", "where", "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "some", "any", "here", "there", "get", "got", "make", "made", "take",
    "took", "come", "came", "go", "went", "know", "think", "say", "said", "tell",
    "told", "ask", "see", "saw", "look", "want", "need", "feel", "try", "use",
    "find", "give", "help", "also", "just", "very", "only", "then", "than", "so",
    "not", "one", "two", "first", "last", "new", "old", "good", "bad", "big",
    "small", "year", "time", "day", "way", "man", "woman", "people", "world",
    "life", "work", "while", "however", "because", "since", "still", "even",
    "much", "many", "well", "now", "back", "per", "mr", "ms", "according",
    "including", "number", "part", "used", "called", "among", "around", "against",
    "without", "within", "along", "across", "like", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten", "hundred", "thousand", "million",
    "billion", "percent", "high", "low", "long", "short", "another", "other",
    "rather", "quite", "already", "always", "never", "often", "away", "down",
    "home", "left", "right", "next", "later", "early", "late", "over", "under",
    "again", "same", "such", "own", "too", "also", "news", "said", "says",
    "view", "hide", "search", "show", "more", "home", "sign", "skip", "menu",
    "share", "read", "watch", "listen", "live", "click", "open", "close",
}


def get_article_urls_from_rss(rss_url, max_articles=3):
    try:
        response = requests.get(rss_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        root = ET.fromstring(response.content)
        urls = []
        for item in root.findall('.//item')[:max_articles]:
            link = item.find('link')
            if link is not None and link.text:
                urls.append(link.text.strip())
        return urls
    except Exception as e:
        print(f"RSS fetch failed {rss_url}: {e}")
        return []


def fetch_article_text(url):
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        # Remove non-content elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'figure']):
            tag.decompose()
        # Extract paragraph text only
        paragraphs = soup.find_all('p')
        text = ' '.join(p.get_text() for p in paragraphs)
        return text[:5000]
    except Exception as e:
        print(f"Article fetch failed {url}: {e}")
        return ""


def extract_advanced_words(text):
    try:
        tokens = word_tokenize(text.lower())
        stop_words = set(stopwords.words('english'))
        advanced = [
            word for word in tokens
            if (len(word) > 6
                and word.isalpha()
                and word not in COMMON_WORDS
                and word not in stop_words)
        ]
        return Counter(advanced).most_common(15)
    except Exception as e:
        print(f"Extraction failed: {e}")
        return []


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


def add_phrase_to_notion(phrase):
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Phrase": {"title": [{"text": {"content": phrase}}]},
            "Meaning": {"rich_text": [{"text": {"content": ""}}]},
            "Category": {"select": {"name": "Academic"}},
            "Difficulty": {"select": {"name": "Advanced"}},
            "Status": {"select": {"name": "New"}},
        },
    }
    response = requests.post(url, headers=NOTION_HEADERS, json=payload)
    response.raise_for_status()


def notify_discord(added_phrases):
    if not added_phrases:
        return
    lines = [f"📚 **Daily vocab: {len(added_phrases)} new words added to Notion!**\n"]
    for phrase, _ in added_phrases:
        lines.append(f"• **{phrase}**")
    requests.post(DISCORD_WEBHOOK_URL, json={"content": "\n".join(lines)})


def main():
    existing = get_existing_phrases()
    all_added = []

    for rss_url in RSS_FEEDS:
        print(f"Fetching RSS: {rss_url}")
        article_urls = get_article_urls_from_rss(rss_url)
        print(f"Found {len(article_urls)} articles")

        for url in article_urls:
            print(f"Fetching article: {url}")
            text = fetch_article_text(url)
            if not text:
                continue

            print(f"Extracted {len(text)} chars")
            words = extract_advanced_words(text)
            print(f"Top words: {[w for w, _ in words[:10]]}")

            for word, count in words[:3]:
                if word.lower() not in existing:
                    add_phrase_to_notion(word)
                    all_added.append((word, count))
                    existing.add(word.lower())
                    print(f"✅ Added: {word}")
                else:
                    print(f"⏭️  Skipped: {word}")

    notify_discord(all_added)
    print(f"\nDone! {len(all_added)} word(s) added.")


if __name__ == "__main__":
    main()
