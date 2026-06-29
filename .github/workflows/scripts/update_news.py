"""
update_news.py
Gira ogni notte via GitHub Actions.
Legge graph_data.json, cerca notizie per ogni startup, salva news_data.json.
"""

import json
import os
import datetime
from datapizza.agents import Agent
from datapizza.clients.anthropic import AnthropicClient
from datapizza.tools.duckduckgo import DuckDuckGoSearchTool

# ── carica il grafo esistente ──────────────────────────────────
with open("graph_data.json", "r", encoding="utf-8") as f:
    graph = json.load(f)

startups = [n for n in graph["nodes"] if n["type"] == "startup"]
print(f"Startup trovate nel grafo: {len(startups)}")

# ── configura agent ───────────────────────────────────────────
client = AnthropicClient(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    model="claude-sonnet-4-6"
)

agent = Agent(
    name="news_researcher",
    client=client,
    system_prompt="""Sei un analista di startup. Cerca le ultime notizie
sulla startup indicata e restituisci un riassunto conciso in italiano.
Includi: funding round, partnership, prodotti nuovi, cambi di management,
risultati finanziari. Massimo 150 parole. Solo fatti recenti (ultimi 30 giorni).""",
    tools=[DuckDuckGoSearchTool()]
)

# ── cerca notizie per ogni startup ────────────────────────────
news_items = []
today = datetime.date.today().isoformat()

for startup in startups:
    name = startup["label"]
    print(f"  Cerco notizie: {name}...")
    try:
        response = agent.run(
            f"Cerca le ultime notizie su {name} startup. "
            f"Riassumi in italiano cosa è successo negli ultimi 30 giorni."
        )
        news_items.append({
            "startup_id": startup["id"],
            "startup_name": name,
            "date": today,
            "summary": response.text.strip(),
            "has_news": True
        })
    except Exception as e:
        print(f"  ⚠ Errore per {name}: {e}")
        news_items.append({
            "startup_id": startup["id"],
            "startup_name": name,
            "date": today,
            "summary": "Nessuna notizia recente trovata.",
            "has_news": False
        })

# ── salva news_data.json ──────────────────────────────────────
output = {
    "updated_at": datetime.datetime.now().isoformat(),
    "news": news_items
}

with open("news_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✅ news_data.json aggiornato — {len(news_items)} startup monitorate")
