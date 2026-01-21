import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlparse
from io import StringIO

# Configuração da página
st.set_page_config(
    page_title="Certificados do Curso",
    page_icon="🎓",
    layout="wide"
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
    """Carrega os dados da planilha do Google Sheets (modo público)"""
    try:
        # ID da planilha
        SPREADSHEET_ID = "1yV510VPi5XtCzxlAXZbsqVWngsbOVEoMyIE0sjM7t0Y"
        
        # Tenta acessar como CSV público
        csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv"
        
        response = requests.get(csv_url)
        
        if response.status_code == 200:
            # Converte o CSV para DataFrame com encoding correto para português
            df = pd.read_csv(StringIO(response.text), encoding='utf-8')
            
            # Limpa os nomes das colunas
            df.columns = [col.strip() for col in df.columns]
            
            # Garante que os e-mails estão em minúsculas para busca case-insensitive
            if 'E-mail' in df.columns:
                df['E-mail'] = df['E-mail'].astype(str).str.lower().str.strip()
            
            # Garante que a coluna Data está no formato correto
            if 'Data' in df.columns:
                # Tenta converter para datetime, mantendo o formato original se não conseguir
                try:
                    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%y', errors='coerce')
                except:
                    pass
            
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
    
    # Garante que os e-mails estão em minúsculas
    if 'E-mail' in df.columns:
        df['E-mail'] = df['E-mail'].str.lower().str.strip()
    
    # Converte Data para datetime
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%y')
    
    return df

def format_google_drive_link(link):
    """Formata o link do Google Drive para acesso direto ao arquivo"""
    try:
        # Se já for um link de visualização, mantém como está
        if '/view' in link:
            return link
        
        # Extrai o ID do arquivo do link do Drive
        parsed = urlparse(str(link))
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
    
    # Cria duas colunas para o layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Instruções
        st.markdown("""
        <div class='instructions'>
            <h4>📋 Como acessar seu certificado:</h4>
            <ol>
                <li>Digite o <b>e-mail</b> que você utilizou na inscrição</li>
                <li>Escolha o <b>evento</b> (opcional)</li>
                <li>Clique em <b>"Buscar Certificado"</b></li>
                <li>Se encontrado, clique no botão para visualizar</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        # Campo para entrada do e-mail
        st.markdown("<div class='email-input'>", unsafe_allow_html=True)
        email = st.text_input(
            "📧 Digite seu e-mail:",
            placeholder="exemplo@cogerh.com.br",
            help="Insira o mesmo e-mail utilizado na inscrição do evento"
        ).strip().lower()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Filtros por Evento e Data
        st.markdown("<div class='filter-section'>", unsafe_allow_html=True)
        st.markdown("**🔍 Filtros opcionais:**")
        
        # Filtro por Evento
        if 'Evento' in df.columns:
            eventos = ['Todos os Eventos'] + sorted(df['Evento'].dropna().unique().tolist())
            evento_selecionado = st.selectbox(
                "Selecione o Evento:",
                eventos,
                help="Filtre por um evento específico"
            )
        else:
            evento_selecionado = 'Todos os Eventos'
        
        # Filtro por Data (se a coluna existir e for datetime)
        if 'Data' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Data']):
            datas_disponiveis = df['Data'].dropna().unique()
            if len(datas_disponiveis) > 0:
                datas_formatadas = ['Todas as Datas'] + sorted(datas_disponiveis)
                # Converter datetime para string para exibição
                datas_display = ['Todas as Datas'] + sorted([d.strftime('%d/%m/%Y') for d in datas_disponiveis])
                data_selecionada_str = st.selectbox(
                    "Selecione a Data:",
                    datas_display,
                    help="Filtre por uma data específica"
                )
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Botão para buscar
        search_button = st.button("🔍 Buscar Certificado", use_container_width=True, type="primary")
    
    with col2:
        # Espaço para resultados
        st.markdown("### 📄 Resultado da Busca")
        
        # Busca o certificado
        if search_button:
            if not email:
                st.error("⚠️ Por favor, digite seu e-mail.")
            elif df.empty:
                st.error("📭 Nenhum certificado encontrado no banco de dados.")
            else:
                # Filtra por e-mail primeiro
                resultado = df[df['E-mail'] == email].copy()
                
                # Aplica filtros adicionais
                if evento_selecionado != 'Todos os Eventos':
                    resultado = resultado[resultado['Evento'] == evento_selecionado]
                
                if 'data_selecionada_str' in locals() and data_selecionada_str != 'Todas as Datas':
                    # Converter a string de volta para datetime para comparação
                    data_selecionada = pd.to_datetime(data_selecionada_str, format='%d/%m/%Y')
                    resultado = resultado[resultado['Data'] == data_selecionada]
                
                if not resultado.empty:
                    # Pega o primeiro resultado
                    certificado = resultado.iloc[0]
                    
                    st.markdown("<div class='certificate-card'>", unsafe_allow_html=True)
                    st.markdown(f"<h3>✅ Certificado Encontrado!</h3>", unsafe_allow_html=True)
                    
                    # Formata a data para exibição
                    data_formatada = ""
                    if 'Data' in certificado and pd.notna(certificado['Data']):
                        if isinstance(certificado['Data'], pd.Timestamp):
                            data_formatada = certificado['Data'].strftime('%d/%m/%Y')
                        else:
                            data_formatada = str(certificado['Data'])
                    
                    # Exibe todas as informações
                    st.markdown(f"**Nome:** {certificado['Nome']}")
                    st.markdown(f"**E-mail:** {certificado['E-mail']}")
                    if 'Evento' in certificado and pd.notna(certificado['Evento']):
                        st.markdown(f"**Evento:** {certificado['Evento']}")
                    if data_formatada:
                        st.markdown(f"**Data:** {data_formatada}")
                    
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
                    
                    # Instruções para baixar
                    with st.expander("💡 Como baixar seu certificado"):
                        st.markdown("""
                        1. Clique em **"Visualizar Certificado"**
                        2. No Google Drive, clique no ícone de **Download** (seta para baixo)
                        3. Escolha onde salvar o arquivo PDF
                        4. Pronto! Você pode imprimir ou compartilhar
                        """)
                else:
                    st.error("❌ Certificado não encontrado com os filtros selecionados.")
                    
                    # Mostra quais certificados o usuário tem
                    certificados_usuario = df[df['E-mail'] == email]
                    if not certificados_usuario.empty:
                        st.info(f"ℹ️ Você possui {len(certificados_usuario)} certificado(s) registrado(s):")
                        
                        for _, cert in certificados_usuario.iterrows():
                            data_evento = ""
                            if 'Data' in cert and pd.notna(cert['Data']):
                                if isinstance(cert['Data'], pd.Timestamp):
                                    data_evento = cert['Data'].strftime('%d/%m/%Y')
                                else:
                                    data_evento = str(cert['Data'])
                            
                            with st.container():
                                st.markdown(f"**• {cert['Evento'] if 'Evento' in cert else 'Evento'}" + 
                                          f" - {data_evento if data_evento else ''}**")
                    else:
                        st.markdown("""
                        **Possíveis causas:**
                        - E-mail digitado incorretamente
                        - Certificado ainda não foi gerado
                        - E-mail diferente do usado na inscrição
                        
                        **Solução:** Entre em contato com a organização do evento.
                        """)
    
    # Seção para visualizar todos os certificados (removido a seção administrativa)
    st.markdown("---")
    st.markdown("### 📊 Visualizar todos os certificados")
    
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        # Filtro por evento para visualização geral
        if 'Evento' in df.columns:
            eventos_geral = ['Todos'] + sorted(df['Evento'].dropna().unique().tolist())
            filtro_evento_geral = st.selectbox(
                "Filtrar por Evento:",
                eventos_geral,
                key='filtro_evento_geral'
            )
        else:
            filtro_evento_geral = 'Todos'
    
    with col_filtro2:
        # Filtro por data para visualização geral
        if 'Data' in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df['Data']):
                datas_geral = ['Todas'] + sorted(df['Data'].dropna().dt.strftime('%d/%m/%Y').unique().tolist())
            else:
                datas_geral = ['Todas'] + sorted(df['Data'].dropna().unique().tolist())
            filtro_data_geral = st.selectbox(
                "Filtrar por Data:",
                datas_geral,
                key='filtro_data_geral'
            )
        else:
            filtro_data_geral = 'Todas'
    
    with col_filtro3:
        # Busca por nome
        busca_nome = st.text_input(
            "Buscar por Nome:",
            placeholder="Digite parte do nome...",
            key='busca_nome'
        )
    
    # Aplica filtros
    df_filtrado = df.copy()
    
    if filtro_evento_geral != 'Todos' and 'Evento' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Evento'] == filtro_evento_geral]
    
    if filtro_data_geral != 'Todas' and 'Data' in df_filtrado.columns:
        if pd.api.types.is_datetime64_any_dtype(df_filtrado['Data']):
            # Converte a string de volta para datetime
            data_filtro = pd.to_datetime(filtro_data_geral, format='%d/%m/%Y')
            df_filtrado = df_filtrado[df_filtrado['Data'] == data_filtro]
        else:
            df_filtrado = df_filtrado[df_filtrado['Data'] == filtro_data_geral]
    
    if busca_nome and 'Nome' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Nome'].str.contains(busca_nome, case=False, na=False)]
    
    # Exibe a tabela filtrada
    st.write(f"**Resultados:** {len(df_filtrado)} certificado(s)")
    
    # Prepara DataFrame para exibição
    df_display = df_filtrado.copy()
    
    # Formata a coluna Data para exibição
    if 'Data' in df_display.columns and pd.api.types.is_datetime64_any_dtype(df_display['Data']):
        df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
    
    # Cria coluna de ação com links
    if 'Link' in df_display.columns:
        df_display['Ação'] = df_display['Link'].apply(
            lambda x: f'<a href="{format_google_drive_link(str(x))}" target="_blank">🔗 Visualizar</a>'
        )
    
    # Seleciona colunas para exibir
    colunas_exibir = []
    for col in ['Data', 'Evento', 'Nome', 'E-mail', 'Ação']:
        if col in df_display.columns:
            colunas_exibir.append(col)
    
    if colunas_exibir:
        # Exibe como HTML para manter os links clicáveis
        st.write(df_display[colunas_exibir].to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.warning("Nenhuma coluna disponível para exibição.")

# Rodapé
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6B7280; font-size: 14px;">
    <p>Em caso de problemas para acessar seu certificado, entre em contato com a organização do evento.</p>
    <p>Desenvolvido com Streamlit • COGERH • Dados atualizados automaticamente</p>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
