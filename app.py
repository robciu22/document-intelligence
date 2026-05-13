"""
Document Intelligence — Streamlit Web-Interface
"""

import streamlit as st
import pdfplumber
import ollama
import json
import tempfile
from pathlib import Path

st.set_page_config(
    page_title="Document Intelligence",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Document Intelligence")
st.markdown("**Lokale KI-Dokumentenanalyse — DSGVO-konform, keine Cloud**")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Einstellungen")
    model = st.selectbox(
        "Ollama-Modell",
        ["llama3.2", "llama3.1:8b", "qwen3:8b"],
        index=0
    )
    st.markdown("---")
    st.markdown("**Wie es funktioniert:**")
    st.markdown("""
    1. PDF hochladen
    2. Lokales LLM analysiert den Inhalt
    3. Strukturierte Infos werden extrahiert

    ✅ Keine Daten verlassen deinen Rechner
    ✅ Funktioniert ohne Internet
    ✅ DSGVO-konform
    """)


def extract_text(pdf_file) -> str:
    with pdfplumber.open(pdf_file) as pdf:
        pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
        return "\n\n".join(pages)


def extract_json(raw: str) -> dict:
    """Robuste JSON-Extraktion — findet JSON-Objekt auch mit Prefix-Text."""
    raw = raw.strip()
    # Markdown code blocks entfernen
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            candidate = part.replace("json", "").strip()
            try:
                return json.loads(candidate)
            except Exception:
                continue
    # Direkt versuchen
    try:
        return json.loads(raw)
    except Exception:
        pass
    # JSON-Objekt mit Regex suchen
    import re
    match = re.search(r'\{[\s\S]*\}', raw)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {"raw_response": raw}


def safe_str(val) -> str:
    """Wandelt dict-Werte sicher in String um."""
    if val is None or val in ("null", "None", ""):
        return "—"
    if isinstance(val, dict):
        return val.get("name") or val.get("value") or str(val)
    return str(val)


def analyze(text: str, model: str) -> dict:
    prompt = f"""Analysiere das folgende Geschäftsdokument und extrahiere strukturierte Informationen.
Antworte NUR mit validem JSON – keine weiteren Erklärungen, kein Markdown.
Alle Felder müssen einfache Strings oder Listen sein, keine verschachtelten Objekte.

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

Dokument:
{text[:3000]}"""

    response = ollama.generate(model=model, prompt=prompt)
    return extract_json(response["response"])


uploaded = st.file_uploader(
    "PDF-Dokument hochladen",
    type=["pdf"],
    help="Rechnung, Vertrag, Angebot — jedes Geschäftsdokument"
)

if uploaded:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    with st.spinner("📄 Text wird extrahiert..."):
        text = extract_text(tmp_path)
    st.success(f"✅ {len(text)} Zeichen aus {uploaded.name} extrahiert")

    with st.expander("📝 Extrahierter Rohtext (Vorschau)"):
        st.text(text[:800] + "..." if len(text) > 800 else text)

    if st.button("🤖 Dokument analysieren", type="primary"):
        with st.spinner(f"Analysiere mit {model} (lokal)..."):
            result = analyze(text, model)

        st.markdown("---")
        st.subheader("📊 Analyseergebnis")

        if "raw_response" in result and len(result) == 1:
            st.warning("LLM-Antwort konnte nicht als JSON geparst werden:")
            st.code(result["raw_response"])
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Dokumenttyp", safe_str(result.get("dokumenttyp")))
                st.metric("Datum", safe_str(result.get("datum")))
            with col2:
                st.metric("Absender", safe_str(result.get("absender")))
                st.metric("Empfänger", safe_str(result.get("empfaenger")))

            if result.get("zusammenfassung"):
                st.info(f"💬 **Zusammenfassung:** {result['zusammenfassung']}")

            betraege = [b for b in result.get("betraege", [])
                        if b.get("betrag") and b.get("betrag") not in (None, "null", "None")]
            if betraege:
                st.markdown("**💶 Beträge:**")
                for b in betraege:
                    st.markdown(f"- {b.get('bezeichnung','')}: **{b.get('betrag','')} {b.get('waehrung','')}**")

            fristen = [f for f in result.get("fristen", []) if f and f not in (None, "null", "None")]
            if fristen:
                st.markdown("**⏰ Fristen:**")
                for f in fristen:
                    st.markdown(f"- {f}")

            infos = [i for i in result.get("schluessel_infos", []) if i and i not in (None, "null", "None")]
            if infos:
                st.markdown("**🔑 Schlüssel-Informationen:**")
                for info in infos:
                    st.markdown(f"- {info}")

            with st.expander("🔧 JSON-Rohdaten"):
                st.json(result)
