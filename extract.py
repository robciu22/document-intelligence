"""
Document Intelligence — Lokale KI-Dokumentenanalyse
Extrahiert strukturierte Informationen aus PDFs mit lokalem LLM (Ollama).
DSGVO-konform: keine Daten verlassen das Netzwerk.
"""

import pdfplumber
import ollama
import json
import argparse
import sys
from pathlib import Path


def extract_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
        return "\n\n".join(pages)


def extract_json(raw: str) -> dict:
    """Robuste JSON-Extraktion — findet JSON-Objekt auch mit Prefix-Text."""
    import re
    raw = raw.strip()
    if "```" in raw:
        for part in raw.split("```"):
            try:
                return json.loads(part.replace("json", "").strip())
            except Exception:
                continue
    try:
        return json.loads(raw)
    except Exception:
        pass
    match = re.search(r'\{[\s\S]*\}', raw)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {"raw_response": raw, "parse_error": "Kein valides JSON gefunden"}


def analyze_document(text: str, model: str = "llama3.2") -> dict:
    prompt = f"""Analysiere das folgende Geschäftsdokument und extrahiere strukturierte Informationen.
Antworte NUR mit validem JSON – keine weiteren Erklärungen, kein Markdown.
Alle Felder müssen einfache Strings oder Listen sein, keine verschachtelten Objekte.

Extrahiere folgende Felder (falls nicht vorhanden: null):
{{
  "dokumenttyp": "Rechnung | Vertrag | Angebot | Lieferschein | Brief | Sonstiges",
  "datum": "YYYY-MM-DD oder null",
  "absender": "Name des Absenders als einfacher String",
  "empfaenger": "Name des Empfängers als einfacher String",
  "betraege": [{{"bezeichnung": "...", "betrag": "...", "waehrung": "EUR"}}],
  "fristen": ["Zahlungsziel, Lieferdatum etc."],
  "schluessel_infos": ["wichtigste Punkte als Liste"],
  "zusammenfassung": "1-2 Sätze Kerninhalt"
}}

Dokument (max. 3000 Zeichen):
{text[:3000]}"""

    response = ollama.generate(model=model, prompt=prompt)
    return extract_json(response["response"])


def print_result(result: dict, pdf_path: str) -> None:
    print(f"\n{'='*60}")
    print(f"  Dokument: {Path(pdf_path).name}")
    print(f"{'='*60}")

    if "parse_error" in result:
        print(f"\n⚠️  Parse-Fehler: {result['parse_error']}")
        print(f"\nRohantwort:\n{result.get('raw_response', '')}")
        return

    icons = {
        "dokumenttyp": "📄", "datum": "📅", "absender": "📤",
        "empfaenger": "📥", "zusammenfassung": "💬"
    }

    for key, icon in icons.items():
        val = result.get(key)
        if val:
            print(f"\n{icon}  {key.capitalize()}: {val}")

    if result.get("betraege"):
        print("\n💶  Beträge:")
        for b in result["betraege"]:
            print(f"     • {b.get('bezeichnung','')}: {b.get('betrag','')} {b.get('waehrung','')}")

    if result.get("fristen"):
        print("\n⏰  Fristen:")
        for f in result["fristen"]:
            print(f"     • {f}")

    if result.get("schluessel_infos"):
        print("\n🔑  Schlüssel-Informationen:")
        for info in result["schluessel_infos"]:
            print(f"     • {info}")

    print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Intelligente Dokumentenanalyse mit lokalem LLM (DSGVO-konform)"
    )
    parser.add_argument("pdf_path", help="Pfad zur PDF-Datei")
    parser.add_argument("--model", default="llama3.2", help="Ollama-Modell (default: llama3.2)")
    parser.add_argument("--json", action="store_true", help="Nur JSON ausgeben")
    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"❌ Datei nicht gefunden: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    print(f"📄 Lese Dokument...")
    text = extract_text(args.pdf_path)
    print(f"✅ {len(text)} Zeichen extrahiert")
    print(f"🤖 Analysiere mit {args.model} (lokal, DSGVO-konform)...")

    result = analyze_document(text, args.model)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_result(result, args.pdf_path)


if __name__ == "__main__":
    main()
