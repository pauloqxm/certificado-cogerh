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
# Estilo corporativo (CSS)
# =========================
st.markdown(
    """
<style>
/* --- Layout base --- */
.block-container{
    padding-top: 1.2rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 900px !important;
}
section[data-testid="stSidebar"] { display: none; }

/* --- Brand bar / header --- */
.brandbar{
    border-radius: 14px;
    padding: 18px 18px;
    background: linear-gradient(90deg, #0B1F4B 0%, #143A8B 45%, #0B1F4B 100%);
    box-shadow: 0 10px 22px rgba(0,0,0,.08);
    margin-bottom: 18px;
}
.brandbar .topline{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:12px;
}
.brandbar .title{
    color:#fff;
    font-weight: 800;
    font-size: 22px;
    letter-spacing: .2px;
    margin: 0;
    line-height: 1.1;
}
.brandbar .subtitle{
    color: rgba(255,255,255,.85);
    margin: 6px 0 0 0;
    font-size: 14px;
}
.badge{
    background: rgba(255,255,255,.12);
    border: 1px solid rgba(255,255,255,.18);
    color:#fff;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 12px;
    white-space: nowrap;
}

/* --- Cards / containers --- */
.card{
    background: #ffffff;
    border: 1px solid rgba(15,23,42,.10);
    border-radius: 14px;
    padding: 1px 18px;
    box-shadow: 0 8px 18px rgba(2,6,23,.05);
    margin: 12px 0;
}
.card h3{
    margin: 0 0 10px 0;
    font-size: 18px;
}
.hr{
    height: 1px;
    background: rgba(15,23,42,.10);
    border: none;
    margin: 12px 0;
}

/* --- Info box (instruções) --- */
.infobox{
    background: #F8FAFC;
    border: 1px solid rgba(15,23,42,.10);
    border-radius: 14px;
    padding: 16px 16px;
    margin-bottom: 12px;
}
.infobox .kicker{
    font-weight: 700;
    color: #0B1F4B;
    font-size: 14px;
    margin-bottom: 8px;
}
.infobox ol{
    margin: 0;
    padding-left: 18px;
    color: rgba(15,23,42,.85);
}

/* --- Certificado card --- */
.cert{
    border-left: 6px solid #143A8B;
}
.pill{
    display:inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    background: rgba(20,58,139,.10);
    border: 1px solid rgba(20,58,139,.18);
    color: #143A8B;
    font-weight: 700;
}
.meta{
    color: rgba(15,23,42,.82);
    font-size: 14px;
    line-height: 1.35;
}

/* --- Botões Streamlit --- */
.stButton>button{
    width: 100%;
    border-radius: 12px !important;
    padding: 12px 14px !important;
    font-weight: 800 !important;
}
div[data-testid="stForm"] button{
    border-radius: 12px !important;
}

/* --- Inputs --- */
label{
    font-weight: 700 !important;
}
.stTextInput input, .stSelectbox div[data-baseweb="select"]{
    border-radius: 12px !important;
}

/* --- Footer --- */
.footer{
    text-align:center;
    color: rgba(15,23,42,.55);
    font-size: 12.5px;
    margin-top: 18px;
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================
# Helpers
# =========================
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(normalize_email(email)))


def format_google_drive_link(link: str) -> str:
    """
    Mantém links /view. Se vier link com /d/<id> ou compartilhamento,
    tenta extrair o file_id.
    """
    try:
        link = str(link).strip()
        if not link:
            return link

        if "/view" in link:
            return link

        parsed = urlparse(link)
        parts = [p for p in parsed.path.split("/") if p]

        # padrões comuns:
        # /file/d/<id>/view
        # /d/<id>
        for i, part in enumerate(parts):
            if part == "d" and i + 1 < len(parts):
                file_id = parts[i + 1]
                return f"https://drive.google.com/file/d/{file_id}/view"

        # fallback: tenta achar um segmento com cara de ID
        for p in parts:
            if len(p) >= 20 and all(c.isalnum() or c in "-_" for c in p):
                return f"https://drive.google.com/file/d/{p}/view"

        return link
    except Exception:
        return str(link)


@st.cache_data(ttl=300, show_spinner=False)
def load_data_from_sheets() -> pd.DataFrame:
    """
    Carrega dados do Google Sheets como CSV.
    Cacheado por 5 min pra ficar rápido e evitar stress no Google.
    """
    SPREADSHEET_ID = "1yV510VPi5XtCzxlAXZbsqVWngsbOVEoMyIE0sjM7t0Y"
    csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv"

    try:
        r = requests.get(csv_url, timeout=15)
        if r.status_code != 200:
            return load_backup_data()

        try:
            content = r.content.decode("utf-8")
        except UnicodeDecodeError:
            content = r.content.decode("latin-1")

        df = pd.read_csv(StringIO(content))
        df.columns = [str(c).strip() for c in df.columns]

        # Normalizações
        if "E-mail" in df.columns:
            df["E-mail"] = df["E-mail"].astype(str).map(normalize_email)

        if "Data" in df.columns:
            # tenta dd/mm/yy e dd/mm/yyyy
            dt = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
            df["Data"] = dt

        # garantir strings nas colunas texto
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str)

        # remove linhas vazias clássicas
        if "E-mail" in df.columns:
            df = df[df["E-mail"].astype(str).str.strip() != ""]

        return df.reset_index(drop=True)

    except Exception:
        return load_backup_data()


def load_backup_data() -> pd.DataFrame:
    data = {
        "Ord.": [2, 3],
        "Data": ["21/01/26", "08/01/26"],
        "Evento": [
            "Oficina: Uso de IA no apoio à elaboração e padronização de Atas e Relatórios na COGERH",
            "Oficina: Uso de IA no apoio à elaboração e padronização de Atas e Relatórios na COGERH",
        ],
        "Nome": ["Dayana Magalhães Cavalcante Nogueira", "Dayane Vieira de Andrade"],
        "E-mail": ["dayana.magalhaes@cogerh.com.br", "dayane.andrade@cogerh.com.br"],
        "Link": [
            "https://drive.google.com/file/d/1eXkeqGycrc3H4QRT3Nmzu8EqYwpg4-vE/view?usp=drive_link",
            "https://drive.google.com/file/d/1XmZUbuTay38hZGqSIo0ZwWyFGkDGnEjw/view?usp=drive_link",
        ],
    }
    df = pd.DataFrame(data)
    df["E-mail"] = df["E-mail"].map(normalize_email)
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    return df


def format_date_br(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return ""
        return value.strftime("%d/%m/%Y")
    try:
        dt = pd.to_datetime(value, errors="coerce", dayfirst=True)
        if pd.isna(dt):
            return str(value)
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(value)


def safe_col(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns and not df[col].empty


# =========================
# UI
# =========================
def header():
    st.markdown(
        """
<div class="brandbar">
  <div class="topline">
    <div>
      <p class="title">Portal de Certificados</p>
      <p class="subtitle">COGERH • Validação e acesso rápido aos certificados de eventos</p>
    </div>
    <div class="badge">Ambiente oficial</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def instructions():
    st.markdown(
        """
<div class="infobox">
  <div class="kicker">Como acessar seu certificado</div>
  <ol>
    <li>Digite o e-mail usado na inscrição.</li>
    <li>Se quiser, filtre por evento e data.</li>
    <li>Clique em “Buscar certificado”.</li>
    <li>Abra o arquivo e faça o download no Google Drive.</li>
    <li>Se não aparecer, o certificado pode não ter sido emitido ainda. Fale com a gerência realizadora.</li>
  </ol>
</div>
""",
        unsafe_allow_html=True,
    )


def search_form(df: pd.DataFrame):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Consulta de certificado")

    with st.form("search_form", clear_on_submit=False):
        email = st.text_input(
            "E-mail do participante",
            placeholder="exemplo@cogerh.com.br",
            help="Use o mesmo e-mail informado na inscrição.",
        )
        email_norm = normalize_email(email)

        col_a, col_b = st.columns(2)

        evento_selecionado = "Todos"
        if safe_col(df, "Evento"):
            eventos = sorted([e for e in df["Evento"].dropna().unique().tolist() if str(e).strip()])
            with col_a:
                evento_selecionado = st.selectbox(
                    "Evento (opcional)",
                    ["Todos"] + eventos,
                )
        else:
            with col_a:
                st.selectbox("Evento (opcional)", ["Indisponível"], disabled=True)

        data_selecionada = "Todas"
        if safe_col(df, "Data") and pd.api.types.is_datetime64_any_dtype(df["Data"]):
            datas = df["Data"].dropna()
            datas_disp = sorted(datas.dt.strftime("%d/%m/%Y").unique().tolist())
            with col_b:
                data_selecionada = st.selectbox("Data (opcional)", ["Todas"] + datas_disp)
        else:
            with col_b:
                st.selectbox("Data (opcional)", ["Indisponível"], disabled=True)

        submitted = st.form_submit_button("Buscar certificado", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
    return submitted, email_norm, evento_selecionado, data_selecionada


def render_certificates(resultado: pd.DataFrame):
    for _, cert in resultado.iterrows():
        nome = str(cert.get("Nome", "")).strip()
        email = str(cert.get("E-mail", "")).strip()
        evento = str(cert.get("Evento", "")).strip()
        data_br = format_date_br(cert.get("Data"))
        link_raw = cert.get("Link", "")
        link = format_google_drive_link(str(link_raw))

        st.markdown('<div class="card cert">', unsafe_allow_html=True)
        st.markdown('<span class="pill">Certificado disponível</span>', unsafe_allow_html=True)
        st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

        if nome:
            st.markdown(f"<div class='meta'><b>Participante</b><br>{nome}</div>", unsafe_allow_html=True)
        if email:
            st.markdown(f"<div class='meta'><b>E-mail</b><br>{email}</div>", unsafe_allow_html=True)
        if evento:
            st.markdown(f"<div class='meta'><b>Evento</b><br>{evento}</div>", unsafe_allow_html=True)
        if data_br:
            st.markdown(f"<div class='meta'><b>Data</b><br>{data_br}</div>", unsafe_allow_html=True)

        st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

        if link and str(link).strip() and link != "nan":
            st.link_button("Abrir certificado no Google Drive", link, use_container_width=True)
            with st.expander("Como baixar"):
                st.write("Abra o link e clique no ícone de download (seta para baixo) no topo do Google Drive.")
        else:
            st.warning("Link do certificado não disponível.")

        st.markdown("</div>", unsafe_allow_html=True)


def main():
    header()
    instructions()

    with st.spinner("Carregando base de certificados..."):
        df = load_data_from_sheets()

    # Guard rails
    required_cols = {"E-mail", "Link"}
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"A base está sem coluna obrigatória: {', '.join(missing)}.")
        st.stop()

    submitted, email, evento_sel, data_sel = search_form(df)

    if submitted:
        if not email:
            st.error("Digite um e-mail para consultar.")
            st.stop()
        if not is_valid_email(email):
            st.error("Esse e-mail parece inválido. Confere e tenta de novo.")
            st.stop()
        if df.empty:
            st.error("Base vazia. Nenhum certificado disponível no momento.")
            st.stop()

        resultado = df[df["E-mail"] == email].copy()

        if resultado.empty:
            st.error("Nenhum certificado encontrado para este e-mail.")
            st.info(
                "Dica rápida: confirme se é o mesmo e-mail da inscrição. "
                "Se estiver certo, pode ser que o certificado ainda não tenha sido emitido."
            )
            st.stop()

        # filtros opcionais
        if evento_sel != "Todos" and "Evento" in resultado.columns:
            resultado = resultado[resultado["Evento"] == evento_sel]

        if data_sel != "Todas" and "Data" in resultado.columns and pd.api.types.is_datetime64_any_dtype(resultado["Data"]):
            dt = pd.to_datetime(data_sel, errors="coerce", dayfirst=True)
            if not pd.isna(dt):
                resultado = resultado[resultado["Data"] == dt]

        if resultado.empty:
            st.warning("Nada encontrado com esses filtros.")
            # mostra um resumo do que existe para o e-mail
            base_user = df[df["E-mail"] == email].copy()
            st.info(f"Constam {len(base_user)} registro(s) para este e-mail. Ajuste os filtros e tente novamente.")
            with st.expander("Ver eventos disponíveis para este e-mail"):
                for _, c in base_user.head(8).iterrows():
                    st.write(f"- {str(c.get('Evento','')).strip()} • {format_date_br(c.get('Data'))}".strip())
            st.stop()

        render_certificates(resultado)

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    with st.expander("Sobre os certificados"):
        st.write("Os certificados são disponibilizados em PDF após validação/registro da participação no evento.")
        st.write("Se o certificado não aparecer, o mais comum é: e-mail diferente do cadastro ou emissão ainda pendente.")

    st.markdown(
        """
<div class="footer">
  COGERH • Companhia de Gestão dos Recursos Hídricos do Ceará
</div>
""",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
