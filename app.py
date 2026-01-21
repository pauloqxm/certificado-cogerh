import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlparse
from io import StringIO

# Configuração da página
st.set_page_config(
    page_title="Certificados COGERH",
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
    .stButton>button {
        width: 100%;
        background-color: #1E3A8A;
        color: white;
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

def load_data_from_sheets():
    """Carrega os dados da planilha do Google Sheets (modo público)"""
    try:
        # ID da planilha (extraído do URL fornecido)
        SPREADSHEET_ID = "1yV510VPi5XtCzxlAXZbsqVWngsbOVEoMyIE0sjM7t0Y"
        
        # Tenta acessar como CSV público (se a planilha estiver pública)
        # Primeiro, tenta o formato CSV
        csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv"
        
        response = requests.get(csv_url)
        
        if response.status_code == 200:
            # Converte o CSV para DataFrame
            df = pd.read_csv(StringIO(response.text))
            
            # Limpa os nomes das colunas
            df.columns = [col.strip() for col in df.columns]
            
            # Garante que os e-mails estão em minúsculas para busca case-insensitive
            if 'E-mail' in df.columns:
                df['E-mail'] = df['E-mail'].astype(str).str.lower().str.strip()
            
            st.success(f"✅ Dados carregados com sucesso! Total de {len(df)} certificados.")
            return df
        else:
            st.warning("⚠️ Não foi possível acessar a planilha como CSV público.")
            return load_backup_data()
            
    except Exception as e:
        st.warning(f"⚠️ Não foi possível acessar a planilha online: {e}")
        return load_backup_data()

def load_backup_data():
    """Carrega dados de backup ou exemplo"""
    st.info("ℹ️ Usando dados de demonstração. Para usar sua planilha, publique-a como CSV público.")
    
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
    
    df = pd.DataFrame(data)
    
    # Garante que os e-mails estão em minúsculas
    if 'E-mail' in df.columns:
        df['E-mail'] = df['E-mail'].str.lower().str.strip()
    
    return df

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
    with st.spinner("Carregando dados dos certificados..."):
        df = load_data_from_sheets()
    
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
                link_certificado = format_google_drive_link(str(certificado['Link']))
                
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
                with st.expander("💡 Como baixar seu certificado"):
                    st.markdown("""
                    1. Clique em **"Visualizar Certificado"**
                    2. No Google Drive, clique no ícone de **Download** (seta para baixo) no canto superior direito
                    3. Escolha onde salvar o arquivo PDF
                    4. Pronto! Você pode imprimir ou compartilhar seu certificado
                    """)
            else:
                st.error("❌ Certificado não encontrado. Verifique se digitou o e-mail corretamente.")
                
                # Sugestões para o usuário
                st.markdown("""
                **Possíveis causas:**
                - E-mail digitado incorretamente
                - Certificado ainda não foi gerado
                - E-mail diferente do usado na inscrição
                
                **Solução:** Entre em contato com a organização do curso.
                """)

    # Seção administrativa (opcional)
    with st.expander("📊 Visualizar todos os certificados"):
        st.write(f"**Total de certificados disponíveis:** {len(df)}")
        
        if st.checkbox("Mostrar lista completa"):
            # Cria uma cópia para exibição
            display_df = df.copy()
            if 'Link' in display_df.columns:
                display_df['Link'] = display_df['Link'].apply(lambda x: '🔗' if pd.notna(x) else '❌')
            
            st.dataframe(display_df[['Nome', 'E-mail', 'Link']].sort_values('Nome'), 
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Nome": "Nome",
                            "E-mail": "E-mail",
                            "Link": "Certificado"
                        })
    
    # Instruções para publicar a planilha (para administradores)
    with st.expander("⚙️ Para administradores - Como publicar a planilha"):
        st.markdown("""
        **Para que o aplicativo funcione com sua planilha:**
        
        1. **Compartilhe a planilha como pública:**
           - Vá em **Arquivo → Compartilhar → Compartilhar com outras pessoas**
           - Em **"Conceder acesso"**, selecione **"Qualquer pessoa com o link"**
           - Escolha **"Visualizador"**
        
        2. **Publicar como CSV:**
           - Vá em **Arquivo → Publicar na web**
           - Selecione a aba (geralmente "Sheet1")
           - Escolha **"Valores separados por vírgula (.csv)"**
           - Clique em **"Publicar"**
        
        3. **Atualizar o código:**
           - No código Python, substitua o `SPREADSHEET_ID` pelo ID da sua planilha
           - O ID é a parte do URL: `https://docs.google.com/spreadsheets/d/SEU_ID_AQUI/edit`
        """)

# Rodapé
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6B7280; font-size: 14px;">
    <p>Em caso de problemas para acessar seu certificado, entre em contato com a organização do curso.</p>
    <p>Desenvolvido com Streamlit • Dados atualizados automaticamente</p>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
