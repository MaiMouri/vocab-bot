import os
import json
import requests
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
import re

# Download required NLTK data
nltk.download("punkt")
nltk.download("punkt_tab")
nltk.download("stopwords")
if False:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

nltk.download("punkt")
nltk.download("punkt_tab")
nltk.download("stopwords")
if False:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

# News sources for scraping
ARTICLE_URLS = [
    "https://www.bbc.com/news",
    "https://www.theguardian.com/world",
]

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# Common English words (basic TOEFL level) - if a word is NOT in this list, it's more advanced
COMMON_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "is", "are", "was", "were", "be", "been", "have", "has", "do", "does", "did",
    "can", "could", "will", "would", "should", "may", "might", "must",
    "about", "after", "before", "between", "from", "into", "through", "during",
    "above", "below", "up", "down", "out", "off", "over", "under",
    "again", "further", "then", "once", "very", "just", "also", "only", "same", "such",
    "no", "nor", "not", "own", "than", "too", "what", "which", "who", "when", "where",
    "why", "how", "all", "each", "every", "both", "few", "more", "most", "some", "any",
    "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "me",
    "him", "her", "us", "them", "my", "your", "his", "her", "its", "our", "their",
    "what", "which", "who", "whom", "whose", "here", "there", "there", "get", "got",
    "make", "made", "take", "took", "come", "came", "go", "went", "know", "knew",
    "think", "thought", "say", "said", "tell", "told", "ask", "asked", "work", "worked",
    "want", "wanted", "need", "needed", "feel", "felt", "try", "tried", "use", "used",
    "find", "found", "give", "gave", "tell", "told", "see", "saw", "seem", "seemed",
    "help", "helped", "talk", "talked", "turn", "turned", "start", "started", "show",
    "showed", "hear", "heard", "let", "left", "put", "putting", "mean", "meant", "keep",
    "kept", "meet", "met", "run", "ran", "pay", "paid", "sit", "sat", "stand", "stood",
    "lose", "lost", "fall", "fell", "cut", "cut", "reach", "reached", "kill", "killed",
    "remain", "remained", "suggest", "suggested", "raise", "raised", "live", "lived",
    "believe", "believed", "hold", "held", "bring", "brought", "happen", "happened",
    "write", "wrote", "provide", "provided", "sit", "sat", "stand", "stood", "lose",
    "lost", "pay", "paid", "meet", "met", "include", "included", "continue", "continued",
    "set", "set", "learn", "learned", "change", "changed", "lead", "led", "understand",
    "understood", "watch", "watched", "follow", "followed", "stop", "stopped", "create",
    "created", "speak", "spoke", "read", "read", "allow", "allowed", "add", "added",
    "spend", "spent", "grow", "grew", "open", "opened", "walk", "walked", "win", "won",
    "offer", "offered", "remember", "remembered", "love", "loved", "consider", "considered",
    "appear", "appeared", "buy", "bought", "wait", "waited", "serve", "served", "die",
    "died", "send", "sent", "expect", "expected", "build", "built", "stay", "stayed",
    "fall", "fell", "cut", "cut", "reach", "reached", "kill", "killed", "remain", "remained",
    "suggest", "suggested", "raise", "raised", "live", "lived", "believe", "believed",
    "hold", "held", "bring", "brought", "happen", "happened", "write", "wrote", "provide",
    "provided", "person", "man", "woman", "child", "boy", "girl", "day", "year", "time",
    "week", "month", "hour", "minute", "second", "week", "world", "place", "country",
    "city", "town", "house", "home", "room", "door", "window", "wall", "floor", "roof",
    "street", "road", "water", "food", "money", "work", "business", "job", "school",
    "book", "paper", "word", "language", "story", "reason", "result", "problem",
    "question", "answer", "idea", "thought", "feeling", "heart", "hand", "foot", "head",
    "eye", "ear", "nose", "mouth", "face", "body", "life", "death", "love", "hate",
    "good", "bad", "new", "old", "young", "big", "small", "high", "low", "long", "short",
    "fast", "slow", "hot", "cold", "warm", "cool", "bright", "dark", "light", "heavy",
    "light", "easy", "difficult", "hard", "soft", "strong", "weak", "happy", "sad",
    "angry", "afraid", "free", "clear", "dark", "deep", "full", "empty", "live", "dead",
    "true", "false", "right", "wrong", "real", "possible", "probable", "different",
    "similar", "same", "equal", "different", "better", "worse", "best", "worst", "one",
    "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "hundred",
    "thousand", "million", "first", "second", "third", "last", "next", "last", "many",
    "few", "several", "many", "less", "little", "much", "more", "most", "all", "other",
    "another", "such", "same", "certain", "sure", "able", "possible", "important",
    "serious", "common", "public", "private", "social", "political", "economic",
    "medical", "legal", "physical", "mental", "human", "natural", "general", "special",
    "normal", "unusual", "typical", "unusual", "wonderful", "terrible", "excellent",
    "poor", "rich", "poor", "cheap", "expensive", "east", "west", "north", "south",
    "usually", "sometimes", "always", "never", "often", "rarely", "suddenly",
    "slowly", "quickly", "gradually", "carefully", "easily", "definitely", "probably",
    "certainly", "perhaps", "maybe"
}


def fetch_article_text(url):
    """Fetch plain text content from a URL."""
    nltk.download("punkt")
nltk.download("punkt_tab")
nltk.download("stopwords")
if False:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self.skip = False

            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style", "nav", "footer", "aside"):
                    self.skip = True

            def handle_endtag(self, tag):
                if tag in ("script", "style", "nav", "footer", "aside"):
                    self.skip = False

            def handle_data(self, data):
                if not self.skip and data.strip():
                    self.text.append(data.strip())

        extractor = TextExtractor()
        extractor.feed(response.text)
        return " ".join(extractor.text)[:5000]
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""


def extract_advanced_words(text):
    """Extract advanced English words (NOT in common word list)."""
    nltk.download("punkt")
nltk.download("punkt_tab")
nltk.download("stopwords")
if False:
        tokens = word_tokenize(text.lower())
        stop_words = set(stopwords.words('english'))
        
        # Filter: only words not in common list, not stopwords, length > 3
        advanced = [
            word for word in tokens 
            if (len(word) > 3 
                and word.isalpha() 
                and word not in COMMON_WORDS 
                and word not in stop_words
                and not word.startswith("'"))
        ]
        
        # Count frequency and get top words
        word_freq = Counter(advanced)
        return word_freq.most_common(10)
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


def get_word_definition(word):
    """Simple definition lookup - could integrate with API later."""
    # For now, return a placeholder; could use free API
    return f"Advanced English word"


def add_phrase_to_notion(phrase, meaning):
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Phrase": {"title": [{"text": {"content": phrase}}]},
            "Meaning": {"rich_text": [{"text": {"content": meaning}}]},
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
    lines = [f"🤖 **Daily auto-extract: {len(added_phrases)} new advanced words!**\n"]
    for phrase, count in added_phrases:
        lines.append(f"• **{phrase}** (appeared {count} times)")
    requests.post(DISCORD_WEBHOOK_URL, json={"content": "\n".join(lines)})


def main():
    existing = get_existing_phrases()
    all_added = []

    for url in ARTICLE_URLS:
        print(f"Fetching: {url}")
        text = fetch_article_text(url)
        if not text:
            continue

        print("Extracting advanced words...")
        words = extract_advanced_words(text)

        for word, count in words[:5]:  # Take top 5
            if word.lower() not in existing:
                meaning = get_word_definition(word)
                add_phrase_to_notion(word, meaning)
                all_added.append((word, count))
                existing.add(word.lower())
                print(f"✅ Added: {word}")
            else:
                print(f"⏭️  Skipped: {word}")

    notify_discord(all_added)
    print(f"\nDone! {len(all_added)} word(s) added.")


if __name__ == "__main__":
    main()
