import re
from io import StringIO
from urllib.parse import urlparse

import pandas as pd
import requests
import streamlit as st


# =========================
# Configuração da página
# =========================
st.set_page_config(
    page_title="Portal de Certificados | COGERH",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# =========================
# CSS Corporativo
# =========================
st.markdown("""
<style>
.block-container{
    max-width: 900px !important;
    padding-top: 1.2rem !important;
}

/* Header */
.brandbar{
    border-radius: 14px;
    padding: 18px;
    background: linear-gradient(90deg, #0B1F4B, #143A8B);
    margin-bottom: 20px;
}
.brandbar h1{
    color: #fff;
    font-size: 22px;
    margin: 0;
}
.brandbar p{
    color: rgba(255,255,255,.85);
    margin: 6px 0 0 0;
    font-size: 14px;
}

/* Cards */
.card{
    background: #fff;
    border: 1px solid rgba(15,23,42,.1);
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 16px;
    box-shadow: 0 6px 18px rgba(0,0,0,.05);
}

/* Certificado */
.cert{
    border-left: 6px solid #ff4b4b;
}

/* Botões */
.stButton>button,
a[data-testid="stLinkButton"] button{
    background-color: #ff4b4b !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
    border: none !important;
    padding: 12px !important;
}

a[data-testid="stLinkButton"] button:hover{
    background-color: #e63e3e !important;
}

/* Footer */
.footer{
    text-align: center;
    color: rgba(0,0,0,.55);
    font-size: 12.5px;
    margin-top: 30px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# Utilidades
# =========================
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def normalize_email(email):
    return (email or "").strip().lower()


def is_valid_email(email):
    return bool(EMAIL_RE.match(normalize_email(email)))


def format_google_drive_link(link):
    try:
        link = str(link)
        if "/view" in link:
            return link

        parsed = urlparse(link)
        parts = parsed.path.split("/")

        for i, p in enumerate(parts):
            if p == "d" and i + 1 < len(parts):
                return f"https://drive.google.com/file/d/{parts[i+1]}/view"

        return link
    except:
        return link


@st.cache_data(ttl=300)
def load_data_from_sheets():
    SPREADSHEET_ID = "1yV510VPi5XtCzxlAXZbsqVWngsbOVEoMyIE0sjM7t0Y"
    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv"

    try:
        r = requests.get(csv_url, timeout=15)
        if r.status_code != 200:
            return pd.DataFrame()

        try:
            content = r.content.decode("utf-8")
        except UnicodeDecodeError:
            content = r.content.decode("latin-1")

        df = pd.read_csv(StringIO(content))
        df.columns = [c.strip() for c in df.columns]

        if "E-mail" in df.columns:
            df["E-mail"] = df["E-mail"].astype(str).apply(normalize_email)

        if "Data" in df.columns:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)

        return df

    except:
        return pd.DataFrame()


def format_date(value):
    if isinstance(value, pd.Timestamp):
        return value.strftime("%d/%m/%Y")
    return ""


# =========================
# App
# =========================
def main():

    # Header
    st.markdown("""
    <div class="brandbar">
        <h1>Portal de Certificados</h1>
        <p>COGERH • Consulta e download de certificados oficiais</p>
    </div>
    """, unsafe_allow_html=True)

    # Instruções
    st.markdown("""
    <div class="card">
        <b>Como funciona</b>
        <ol>
            <li>Informe o e-mail usado na inscrição</li>
            <li>Opcionalmente filtre por evento ou data</li>
            <li>Clique em Buscar certificado</li>
            <li>Abra o arquivo e faça o download</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    df = load_data_from_sheets()

    # Formulário
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Consulta de certificado")

    with st.form("form_busca"):
        email = st.text_input("E-mail do participante")
        email = normalize_email(email)

        col1, col2 = st.columns(2)

        eventos = ["Todos"]
        if "Evento" in df.columns:
            eventos += sorted(df["Evento"].dropna().unique().tolist())

        with col1:
            evento_sel = st.selectbox("Evento (opcional)", eventos)

        datas = ["Todas"]
        if "Data" in df.columns:
            datas += sorted(df["Data"].dropna().dt.strftime("%d/%m/%Y").unique().tolist())

        with col2:
            data_sel = st.selectbox("Data (opcional)", datas)

        buscar = st.form_submit_button("Buscar certificado", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Resultado
    if buscar:
        if not email or not is_valid_email(email):
            st.error("Informe um e-mail válido.")
            return

        resultado = df[df["E-mail"] == email].copy()

        if evento_sel != "Todos":
            resultado = resultado[resultado["Evento"] == evento_sel]

        if data_sel != "Todas":
            resultado = resultado[resultado["Data"].dt.strftime("%d/%m/%Y") == data_sel]

        if resultado.empty:
            st.warning("Nenhum certificado encontrado para este e-mail.")
            return

        for _, cert in resultado.iterrows():
            st.markdown('<div class="card cert">', unsafe_allow_html=True)

            st.markdown(f"**Nome:** {cert.get('Nome','')}")
            st.markdown(f"**E-mail:** {cert.get('E-mail','')}")
            st.markdown(f"**Evento:** {cert.get('Evento','')}")
            st.markdown(f"**Data:** {format_date(cert.get('Data'))}")

            link = format_google_drive_link(cert.get("Link", ""))

            if link:
                st.link_button("Baixar certificado", link, use_container_width=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="footer">
        COGERH • Companhia de Gestão dos Recursos Hídricos do Ceará
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
