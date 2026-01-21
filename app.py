import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from urllib.parse import urlparse

# Configuração da página
st.set_page_config(
    page_title="Certificados do Curso",
    page_icon="🎓",
    layout="centered"
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1E3A8A;
        padding-bottom: 20px;
    }
    .certificate-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 25px;
        margin: 20px 0;
        border-left: 5px solid #1E3A8A;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .email-input {
        margin-bottom: 20px;
    }
    .success-message {
        color: #059669;
        font-weight: bold;
        font-size: 18px;
    }
    .error-message {
        color: #DC2626;
        font-weight: bold;
    }
    .instructions {
        background-color: #EFF6FF;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 25px;
        border: 1px solid #BFDBFE;
    }
</style>
""", unsafe_allow_html=True)

# Título da aplicação
st.markdown("<h1 class='main-header'>🎓 Certificados do Curso</h1>", unsafe_allow_html=True)

# Instruções
st.markdown("""
<div class='instructions'>
    <h4>📋 Como acessar seu certificado:</h4>
    <ol>
        <li>Digite o <b>e-mail</b> que você utilizou na inscrição do curso</li>
        <li>Clique em <b>"Buscar Certificado"</b></li>
        <li>Se encontrado, clique no botão para visualizar ou baixar seu certificado</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# Configuração do Google Sheets
def setup_google_sheets():
    # Configuração do acesso ao Google Sheets (via JSON de credenciais)
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    # Em produção, use credenciais de serviço em variáveis de ambiente
    # Para desenvolvimento local, você pode carregar de um arquivo JSON
    
    try:
        # Tente pegar as credenciais do secrets do Streamlit
        secrets = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(secrets, scopes=scope)
    except:
        # Para desenvolvimento local (comente em produção)
        st.error("Configuração de credenciais não encontrada.")
        st.info("Configure as credenciais do Google Sheets nas secrets do Streamlit")
        return None
    
    return gspread.authorize(creds)

def load_data_from_sheets():
    """Carrega os dados da planilha do Google Sheets"""
    try:
        # ID da planilha (extraído do URL fornecido)
        SPREADSHEET_ID = "1yV510VPi5XtCzxlAXZbsqVWngsbOVEoMyIE0sjM7t0Y"
        
        client = setup_google_sheets()
        if not client:
            return None
        
        # Abre a planilha
        sheet = client.open_by_key(SPREADSHEET_ID)
        
        # Seleciona a primeira aba (worksheet)
        worksheet = sheet.get_worksheet(0)
        
        # Pega todos os registros
        records = worksheet.get_all_records()
        
        # Converte para DataFrame
        df = pd.DataFrame(records)
        
        # Limpa os nomes das colunas (remove espaços extras)
        df.columns = [col.strip() for col in df.columns]
        
        # Garante que os e-mails estão em minúsculas para busca case-insensitive
        if 'E-mail' in df.columns:
            df['E-mail'] = df['E-mail'].str.lower().str.strip()
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None

# Versão alternativa se houver problemas com a API
def load_data_from_csv_backup():
    """Carrega dados de backup local (útil para desenvolvimento)"""
    try:
        # Se quiser testar com dados locais, pode usar esta função
        # df = pd.read_csv("CERTIFICADOS - modelo planilha.csv")
        # return df
        
        st.info("Usando dados de demonstração...")
        # Dados de exemplo baseados no CSV fornecido
        data = {
            'Ord.': [2, 3],
            'Nome': ['Dayana Magalhães Cavalcante Nogueira', 'Dayane Vieira de andrade'],
            'E-mail': ['dayana.magalhaes@cogerh.com.br', 'dayane.andrade@cogerh.com.br'],
            'Link': [
                'https://drive.google.com/file/d/1eXkeqGycrc3H4QRT3Nmzu8EqYwpg4-vE/view?usp=drive_link',
                'https://drive.google.com/file/d/1XmZUbuTay38hZGqSIo0ZwWyFGkDGnEjw/view?usp=drive_link'
            ]
        }
        return pd.DataFrame(data)
    except:
        return None

def format_google_drive_link(link):
    """Formata o link do Google Drive para acesso direto ao arquivo"""
    try:
        # Se já for um link de visualização, mantém como está
        if '/view' in link:
            return link
        
        # Extrai o ID do arquivo do link do Drive
        parsed = urlparse(link)
        path_parts = parsed.path.split('/')
        
        for i, part in enumerate(path_parts):
            if part == 'd' and i+1 < len(path_parts):
                file_id = path_parts[i+1]
                return f"https://drive.google.com/file/d/{file_id}/view"
        
        return link
    except:
        return link

# Interface principal
def main():
    # Carrega os dados
    df = load_data_from_sheets()
    
    # Se não conseguir carregar do Sheets, tenta o backup
    if df is None or df.empty:
        df = load_data_from_csv_backup()
    
    if df is None:
        st.error("Não foi possível carregar os dados dos certificados.")
        st.info("Por favor, tente novamente mais tarde ou entre em contato com os organizadores.")
        return
    
    # Campo para entrada do e-mail
    st.markdown("<div class='email-input'>", unsafe_allow_html=True)
    email = st.text_input(
        "📧 Digite seu e-mail:",
        placeholder="exemplo@email.com",
        help="Insira o mesmo e-mail utilizado na inscrição do curso"
    ).strip().lower()
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Botão para buscar
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_button = st.button("🔍 Buscar Certificado", use_container_width=True, type="primary")
    
    # Busca o certificado
    if search_button:
        if not email:
            st.error("⚠️ Por favor, digite seu e-mail.")
        elif df.empty:
            st.error("📭 Nenhum certificado encontrado no banco de dados.")
        else:
            # Busca pelo e-mail (case-insensitive)
            result = df[df['E-mail'] == email]
            
            if not result.empty:
                # Pega o primeiro resultado (deve ser único)
                certificado = result.iloc[0]
                
                st.markdown("<div class='certificate-card'>", unsafe_allow_html=True)
                st.markdown(f"<h3>✅ Certificado Encontrado!</h3>", unsafe_allow_html=True)
                st.markdown(f"**Nome:** {certificado['Nome']}")
                st.markdown(f"**E-mail:** {certificado['E-mail']}")
                
                # Formata o link para visualização
                link_certificado = format_google_drive_link(certificado['Link'])
                
                # Botão para acessar o certificado
                st.markdown("---")
                st.markdown(f"""
                <a href="{link_certificado}" target="_blank">
                    <button style="
                        background-color: #1E3A8A;
                        color: white;
                        padding: 12px 24px;
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 16px;
                        font-weight: bold;
                        width: 100%;
                        text-align: center;">
                        📄 Visualizar Certificado
                    </button>
                </a>
                """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Instruções adicionais
                st.info("💡 **Dica:** Na página do Google Drive, clique em 'Download' (ícone de seta para baixo) para salvar seu certificado.")
            else:
                st.error("❌ Certificado não encontrado. Verifique se digitou o e-mail corretamente.")
                st.info("📧 Se o problema persistir, entre em contato com a organização do curso.")

    # Exibe informações sobre o total de certificados (opcional)
    with st.expander("ℹ️ Informações"):
        st.write(f"**Total de certificados disponíveis:** {len(df)}")
        
        if st.checkbox("Mostrar lista de e-mails cadastrados"):
            st.dataframe(df[['Nome', 'E-mail']].sort_values('Nome'), 
                        use_container_width=True,
                        hide_index=True)

# Rodapé
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6B7280; font-size: 14px;">
    <p>Em caso de problemas para acessar seu certificado, entre em contato com a organização do curso.</p>
    <p>Desenvolvido com Streamlit • Dados armazenados no Google Sheets</p>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
