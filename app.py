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
    layout="centered"
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


def analyze(text: str, model: str) -> dict:
    prompt = f"""Analysiere das folgende Geschäftsdokument und extrahiere strukturierte Informationen.
Antworte NUR mit validem JSON – keine weiteren Erklärungen, kein Markdown.

{{
  "dokumenttyp": "Rechnung | Vertrag | Angebot | Lieferschein | Brief | Sonstiges",
  "datum": "YYYY-MM-DD oder null",
  "absender": "Unternehmen oder Person",
  "empfaenger": "Unternehmen oder Person",
  "betraege": [{{"bezeichnung": "...", "betrag": "...", "waehrung": "EUR"}}],
  "fristen": ["Zahlungsziel, Lieferdatum etc."],
  "schluessel_infos": ["wichtigste Punkte als Liste"],
  "zusammenfassung": "1-2 Sätze Kerninhalt"
}}

Dokument:
{text[:3000]}"""

    response = ollama.generate(model=model, prompt=prompt)
    raw = response["response"].strip()
    if "```" in raw:
        raw = raw.split("```")[1].replace("json", "").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"raw_response": raw}


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
                st.metric("Dokumenttyp", result.get("dokumenttyp", "—"))
                st.metric("Datum", result.get("datum", "—"))
            with col2:
                st.metric("Absender", result.get("absender", "—"))
                st.metric("Empfänger", result.get("empfaenger", "—"))

            if result.get("zusammenfassung"):
                st.info(f"💬 **Zusammenfassung:** {result['zusammenfassung']}")

            if result.get("betraege"):
                st.markdown("**💶 Beträge:**")
                for b in result["betraege"]:
                    st.markdown(f"- {b.get('bezeichnung','')}: **{b.get('betrag','')} {b.get('waehrung','')}**")

            if result.get("fristen"):
                st.markdown("**⏰ Fristen:**")
                for f in result["fristen"]:
                    st.markdown(f"- {f}")

            if result.get("schluessel_infos"):
                st.markdown("**🔑 Schlüssel-Informationen:**")
                for info in result["schluessel_infos"]:
                    st.markdown(f"- {info}")

            with st.expander("🔧 JSON-Rohdaten"):
                st.json(result)
