import os
import json
import glob
from datetime import datetime, timezone
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Le modèle officiel demandé par Google
model_name = "gemini-3.8-flash"

# 1. Scanner les documents du coffre
context_data = ""
for folder in ["01_Inbox", "02_Strategic_Core", "03_Operations"]:
    files = glob.glob(f"{folder}/**/*.md", recursive=True) + glob.glob(f"{folder}/*.md")
    for fpath in files[:5]:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                context_data += f"\n--- Document : {fpath} ---\n" + f.read()[:2000]
        except Exception:
            pass

now_iso = datetime.now(timezone.utc).isoformat()
now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
uuid_str = f"usr-node-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

system_prompt = f"""Tu es le Conseil d'Administration Autonome "Life OS" composé de :
- Tech Lead : Excellence technique, PySpark, Databricks, Big Data.
- Directeur Stratégie : Roadmap carrière, opportunités, visa USA/Canada, vision 1M$.
- Coach Bio-Rythme : Sommeil, sport, récupération, énergie vitale.
- Secrétaire Exécutif : Arbitrage strict des conflits d'agenda et synthèse.

Génère la décision exécutive et le plan d'action du jour au format Markdown STRICT avec ce frontmatter YAML :

---
uuid: "{uuid_str}"
created_at: {now_iso}
entity_type: "operation_log"
domain: "Life_OS_Governance"
lifecycle_state: "active"
security_classification: "restricted_personal"
actors:
  primary: "Secretary_Arbitrage"
  contributors: ["Tech_Lead", "Coach_Bio-Rythme", "Directeur_Strategie"]
---

# Synthèse Opérationnelle & Décision du Jour

## Arbitrages du Conseil
[Décisions fermes et justification d'arbitrage pour la journée]

## Actions Immédiates
- [ ] Action 1
- [ ] Action 2
- [ ] Action 3
"""

user_query = f"Contexte extrait du coffre :\n{context_data if context_data else 'Revue quotidienne des priorités.'}\n\nRends les arbitrages du jour."

# 2. Appel direct avec gemini-3.8-flash
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
payload = {
    "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_query}"}]}]
}

resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
decision_text = ""

if resp.status_code == 200:
    decision_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    if decision_text.startswith("```markdown"):
        decision_text = decision_text[len("```markdown"):].strip()
    if decision_text.startswith("```"):
        decision_text = decision_text[len("```"):].strip()
    if decision_text.endswith("```"):
        decision_text = decision_text[:-3].strip()
else:
    decision_text = f"# Erreur API Gemini : {resp.status_code}\n{resp.text}"

# 3. Écrire la décision dans 04_Executive_Decisions
os.makedirs("04_Executive_Decisions", exist_ok=True)
out_path = f"04_Executive_Decisions/decision_{now_str}.md"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(decision_text)

# 4. Envoyer le briefing sur Telegram
summary_lines = [l for l in decision_text.splitlines() if not l.startswith("---") and not l.startswith("uuid:") and not l.startswith("created_at:") and l.strip()][:15]
summary_text = "\n".join(summary_lines)

msg = f"🏛️ **Conseil d'Administration Life OS (Rapport Cloud)**\n\n{summary_text}\n\n✅ *Note archivée automatiquement dans votre coffre Obsidian !*"

tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
requests.post(tg_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
