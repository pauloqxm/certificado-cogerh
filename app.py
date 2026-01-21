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
        font-weight: bold;
    }
    .filter-section {
        background-color: #F3F4F6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Título da aplicação
st.markdown("<h1 class='main-header'>🎓 Certificados de Eventos COGERH</h1>", unsafe_allow_html=True)

def load_data_from_sheets():
    """Carrega os dados da planilha do Google Sheets"""
    try:
        # ID da planilha
        SPREADSHEET_ID = "1yV510VPi5XtCzxlAXZbsqVWngsbOVEoMyIE0sjM7t0Y"
        
        # URL para exportar como CSV
        csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv"
        
        response = requests.get(csv_url)
        
        if response.status_code == 200:
            # Tenta diferentes encodings para resolver problemas de caracteres especiais
            try:
                # Primeiro tenta UTF-8
                content = response.content.decode('utf-8')
            except UnicodeDecodeError:
                # Se falhar, tenta latin-1
                content = response.content.decode('latin-1')
            
            # Converte para DataFrame
            df = pd.read_csv(StringIO(content))
            
            # Limpa os nomes das colunas
            df.columns = [col.strip() for col in df.columns]
            
            # Garante que os e-mails estão em minúsculas
            if 'E-mail' in df.columns:
                df['E-mail'] = df['E-mail'].astype(str).str.lower().str.strip()
            
            # Converte Data para datetime se existir
            if 'Data' in df.columns:
                try:
                    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%y', errors='coerce')
                except:
                    pass  # Mantém como string se não conseguir converter
            
            # Converte todas as colunas de texto para string com encoding correto
            text_columns = df.select_dtypes(include=['object']).columns
            for col in text_columns:
                df[col] = df[col].astype(str)
            
            return df
            
        else:
            st.warning("⚠️ Não foi possível acessar a planilha online.")
            return load_backup_data()
            
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar dados: {str(e)}")
        return load_backup_data()

def load_backup_data():
    """Carrega dados de exemplo para demonstração"""
    # Dados de exemplo com encoding correto
    data = {
        'Ord.': [2, 3],
        'Data': ['21/01/26', '08/01/26'],
        'Evento': [
            'Oficina: Uso de IA no apoio à elaboração e padronização de Atas e Relatórios na COGERH',
            'Oficina: Uso de IA no apoio à elaboração e padronização de Atas e Relatórios na COGERH'
        ],
        'Nome': ['Dayana Magalhães Cavalcante Nogueira', 'Dayane Vieira de andrade'],
        'E-mail': ['dayana.magalhaes@cogerh.com.br', 'dayane.andrade@cogerh.com.br'],
        'Link': [
            'https://drive.google.com/file/d/1eXkeqGycrc3H4QRT3Nmzu8EqYwpg4-vE/view?usp=drive_link',
            'https://drive.google.com/file/d/1XmZUbuTay38hZGqSIo0ZwWyFGkDGnEjw/view?usp=drive_link'
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Garante encoding correto
    if 'E-mail' in df.columns:
        df['E-mail'] = df['E-mail'].str.lower().str.strip()
    
    # Converte Data para datetime
    try:
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%y')
    except:
        pass
    
    return df

def format_google_drive_link(link):
    """Formata o link do Google Drive para acesso direto"""
    try:
        link = str(link)
        # Se já for um link de visualização, mantém como está
        if '/view' in link:
            return link
        
        # Extrai o ID do arquivo
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
    # Instruções
    st.markdown("""
    <div class='instructions'>
        <h4>📋 Como acessar seu certificado:</h4>
        <ol>
            <li>Digite o <b>e-mail</b> que você utilizou na inscrição</li>
            <li>Se desejar, selecione o <b>evento</b> e/ou <b>data</b> específicos</li>
            <li>Clique em <b>"Buscar Certificado"</b></li>
            <li>Se encontrado, clique no botão para visualizar ou baixar</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # Carrega os dados
    with st.spinner("Carregando dados dos certificados..."):
        df = load_data_from_sheets()
    
    # Filtros
    st.markdown("<div class='filter-section'>", unsafe_allow_html=True)
    
    # Campo para e-mail
    email = st.text_input(
        "📧 **Digite seu e-mail:**",
        placeholder="exemplo@cogerh.com.br",
        help="Insira o mesmo e-mail utilizado na inscrição"
    ).strip().lower()
    
    # Filtro por Evento
    evento_selecionado = "Todos os Eventos"
    if 'Evento' in df.columns and not df['Evento'].empty:
        eventos = ['Todos os Eventos'] + sorted(df['Evento'].dropna().unique().tolist())
        evento_selecionado = st.selectbox(
            "🎯 **Filtrar por Evento (opcional):**",
            eventos,
            help="Selecione um evento específico"
        )
    
    # Filtro por Data
    data_selecionada_str = "Todas as Datas"
    if 'Data' in df.columns and not df['Data'].empty:
        # Converte datas para formato de exibição
        if pd.api.types.is_datetime64_any_dtype(df['Data']):
            datas_unicas = df['Data'].dropna().dt.strftime('%d/%m/%Y').unique()
        else:
            datas_unicas = df['Data'].dropna().unique()
        
        if len(datas_unicas) > 0:
            datas_display = ['Todas as Datas'] + sorted(datas_unicas.tolist())
            data_selecionada_str = st.selectbox(
                "📅 **Filtrar por Data (opcional):**",
                datas_display,
                help="Selecione uma data específica"
            )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Botão para buscar
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_button = st.button("🔍 **Buscar Certificado**", use_container_width=True, type="primary")
    
    # Busca o certificado
    if search_button:
        if not email:
            st.error("⚠️ Por favor, digite seu e-mail.")
        elif df.empty:
            st.error("📭 Nenhum certificado encontrado no banco de dados.")
        else:
            # Filtra por e-mail
            resultado = df[df['E-mail'] == email].copy()
            
            if resultado.empty:
                st.error("❌ Certificado não encontrado para este e-mail.")
                st.info("""
                **Verifique:**
                - Se digitou o e-mail corretamente
                - Se o e-mail é o mesmo usado na inscrição
                - Se o certificado já foi emitido
                
                **Caso o problema persista, entre em contato com a organização do evento.**
                """)
            else:
                # Aplica filtros adicionais
                if evento_selecionado != 'Todos os Eventos':
                    resultado = resultado[resultado['Evento'] == evento_selecionado]
                
                if data_selecionada_str != 'Todas as Datas' and 'Data' in resultado.columns:
                    if pd.api.types.is_datetime64_any_dtype(resultado['Data']):
                        data_filtro = pd.to_datetime(data_selecionada_str, format='%d/%m/%Y')
                        resultado = resultado[resultado['Data'] == data_filtro]
                    else:
                        resultado = resultado[resultado['Data'] == data_selecionada_str]
                
                if resultado.empty:
                    st.warning("⚠️ Nenhum certificado encontrado com os filtros selecionados.")
                    
                    # Mostra quais certificados o usuário tem
                    certificados_usuario = df[df['E-mail'] == email]
                    if not certificados_usuario.empty:
                        st.info(f"ℹ️ Você possui {len(certificados_usuario)} certificado(s) registrado(s) para este e-mail.")
                        
                        for _, cert in certificados_usuario.head(5).iterrows():  # Limita a 5 para não poluir
                            evento = cert.get('Evento', 'Evento não especificado')
                            data_evento = ""
                            if 'Data' in cert and pd.notna(cert['Data']):
                                if isinstance(cert['Data'], pd.Timestamp):
                                    data_evento = cert['Data'].strftime('%d/%m/%Y')
                                else:
                                    data_evento = str(cert['Data'])
                            
                            if data_evento:
                                st.write(f"• **{evento}** - {data_evento}")
                            else:
                                st.write(f"• **{evento}**")
                else:
                    # Exibe cada certificado encontrado
                    for idx, certificado in resultado.iterrows():
                        st.markdown("<div class='certificate-card'>", unsafe_allow_html=True)
                        st.markdown(f"<h3>✅ Certificado Encontrado!</h3>", unsafe_allow_html=True)
                        
                        # Formata a data
                        data_formatada = ""
                        if 'Data' in certificado and pd.notna(certificado['Data']):
                            if isinstance(certificado['Data'], pd.Timestamp):
                                data_formatada = certificado['Data'].strftime('%d/%m/%Y')
                            else:
                                data_formatada = str(certificado['Data'])
                        
                        # Exibe informações
                        st.markdown(f"**Nome:** {certificado.get('Nome', '')}")
                        st.markdown(f"**E-mail:** {certificado.get('E-mail', '')}")
                        
                        if 'Evento' in certificado and pd.notna(certificado['Evento']):
                            st.markdown(f"**Evento:** {certificado['Evento']}")
                        
                        if data_formatada:
                            st.markdown(f"**Data:** {data_formatada}")
                        
                        # Link do certificado
                        if 'Link' in certificado and pd.notna(certificado['Link']):
                            link_certificado = format_google_drive_link(str(certificado['Link']))
                            
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
                                    text-align: center;
                                    margin: 10px 0;">
                                    📄 Visualizar Certificado
                                </button>
                            </a>
                            """, unsafe_allow_html=True)
                            
                            # Instruções
                            with st.expander("💡 Como baixar o certificado"):
                                st.markdown("""
                                1. Clique no botão **"Visualizar Certificado"**
                                2. Na página do Google Drive, clique no ícone de **Download** (seta para baixo) no canto superior
                                3. Selecione o local para salvar o arquivo
                                4. Pronto! Seu certificado está salvo
                                """)
                        else:
                            st.warning("Link do certificado não disponível.")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
    
    # Informações adicionais
    st.markdown("---")
    with st.expander("ℹ️ Informações sobre os certificados"):
        st.markdown("""
        **Sobre os certificados:**
        - São emitidos após a participação nos eventos
        - Contém nome do participante, evento e data
        - São disponibilizados em formato PDF
        - Podem ser baixados e impressos
        
        **Em caso de problemas:**
        - Verifique se digitou o e-mail corretamente
        - Confirme se o certificado já foi emitido
        - Entre em contato com a organização do evento
        """)

# Rodapé
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6B7280; font-size: 14px;">
    <p>COGERH - Companhia de Gestão dos Recursos Hídricos do Ceará</p>
    <p>Desenvolvido com Streamlit • Dados atualizados automaticamente</p>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
