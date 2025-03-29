import os
import json
import requests
from bs4 import BeautifulSoup

CACHE_DIR = "discord_bot/candidate_cache"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1355371572843516095/GmadF7Zd3QdI66f21Rriuf1xb2tHVeD4UIQ2YlFkdc24gv-J-k3r8CTa3z0XaM09-DUh"

PARTY_CONFIG = {
    "PPC": {
        "pages": [
            "https://www.peoplespartyofcanada.ca/candidates",
            "https://www.peoplespartyofcanada.ca/candidates?f6ad6c7a_page=2",
            "https://www.peoplespartyofcanada.ca/candidates?f6ad6c7a_page=3",
        ],
        "container": "div.collection-item-10.w-dyn-item.w-col-3[role='listitem']",
        "name": "div.social-media-card-content h3"
    },
    "Conservative": {
        "pages": ["https://www.conservative.ca/candidates/"],
        "container": "div.card-wrapper",
        "name": "h3.name-header"
    },
    "Green": {
        "pages": ["https://www.greenparty.ca/en/candidates/"],
        "container": "article.gpc-post-card",
        "name": "h2.gpc-post-card-heading a"
    },
    "Liberal": {
        "pages": ["https://liberal.ca/your-liberal-candidates/"],
        "container": "article.person__item-container",
        "name": "h2.person__name"
    },
    "NDP": {
        "pages": ["https://www.ndp.ca/team"],
        "container": "div.civics-inner-text",
        "name": "div.campaign-civics-list-title.civic-name"
    },
}

def get_candidate_names(page_url, container_sel, name_sel):
    try:
        r = requests.get(page_url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        containers = soup.select(container_sel)
        names = set()
        for c in containers:
            name_el = c.select_one(name_sel)
            if name_el:
                name = name_el.get_text(strip=True)
                if name:
                    names.add(name)
        return names
    except Exception as e:
        print(f"[!] Error scraping {page_url}: {e}")
        return set()

def send_discord_ping(new_names, party, update_type="new"):
    if not DISCORD_WEBHOOK_URL:
        print("[!] No Discord webhook URL set.")
        return

    if update_type == "new":
        message = f"🗳️ **New {party} Candidate(s) Detected:**\n" + "\n".join(f"- {name}" for name in sorted(new_names))
    else:
        message = f"✅ No new {party} candidates found."

    payload = {"content": message}
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code not in (200, 204):
            print(f"[!] Discord webhook failed: {r.status_code} {r.text}")
        else:
            print(f"📣 Sent update to Discord ({update_type})")
    except Exception as e:
        print(f"[!] Failed to send Discord message: {e}")

def check_party(party, config):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"{party.lower()}_names.json")

    current_names = set()
    for page in config["pages"]:
        names = get_candidate_names(page, config["container"], config["name"])
        current_names.update(names)

    if not current_names:
        print(f"[!] No names found for {party}, skipping.")
        return

    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            old_names = set(json.load(f))
    else:
        old_names = set()

    new_names = current_names - old_names
    if new_names:
        print(f"\n🔔 New {party} candidate(s) detected:")
        for name in sorted(new_names):
            print(f" - {name} ({party})")
        send_discord_ping(new_names, party, update_type="new")
    else:
        print(f"✅ No new {party} candidates.")
        send_discord_ping([], party, update_type="none")

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(sorted(current_names), f, ensure_ascii=False, indent=2)

def main():
    for party, config in PARTY_CONFIG.items():
        print(f"\n--- Checking {party} ---")
        check_party(party, config)

if __name__ == "__main__":
    main()
