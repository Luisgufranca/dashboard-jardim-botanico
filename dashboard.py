import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Monitoramento Jardim Botânico", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('jardim_botanico_db.CSV', sep=';', skiprows=8, decimal=',', encoding='latin1')
    
    # nomea mais praticos
    cols = ['data', 'hora', 'precipitacao', 'pressao', 'pressao_max', 'pressao_min', 
            'radiacao', 'temp_ar', 'temp_orvalho', 'temp_max', 'temp_min', 
            'temp_orvalho_max', 'temp_orvalho_min', 'umidade_max', 'umidade_min', 
            'umidade', 'vento_dir', 'vento_rajada', 'vento_vel', 'extra']
    df.columns = cols[:len(df.columns)]
    
    # juntando data e hora
    df['datetime'] = pd.to_datetime(df['data'].str.replace('/', '-') + ' ' + df['hora'].str[:2] + ':00:00')
    
    # garante que o que é número seja lido como número
    numeric_cols = ['precipitacao', 'temp_ar', 'temp_max', 'temp_min', 'umidade', 'vento_rajada', 'vento_vel']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df.dropna(subset=['datetime'])

data = load_data()

# sidebar
st.sidebar.header("Configurações")

# escolha das datas
date_range = st.sidebar.date_input(
    "Escolha o período", 
    value=[data['datetime'].min().date(), data['datetime'].max().date()]
)

# trava o código se não escolher as duas datas
if len(date_range) != 2:
    st.sidebar.warning("Selecione o início e o fim.")
    st.stop()

start_date, end_date = date_range
df_filtered = data[(data['datetime'].dt.date >= start_date) & (data['datetime'].dt.date <= end_date)]

# sliders para definir o que é "muito quente" ou "muita chuva"
temp_threshold = st.sidebar.slider("Aviso de calor (°C)", 30, 45, 35)
precip_threshold = st.sidebar.slider("Aviso de chuva (mm/h)", 5, 50, 10)

# head
c_tit, c_map = st.columns([2, 1])

with c_tit:
    st.title("⛈️ Painel do Tempo")
    st.write(f"Dados da estação do Jardim Botânico entre {start_date.strftime('%d/%m/%Y')} e {end_date.strftime('%d/%m/%Y')}")

with c_map:
    # mostra onde fica a estação no mapa
    st.map(pd.DataFrame({'lat': [-30.0536], 'lon': [-51.1747]}), zoom=12)

st.divider()
n1, n2, n3, n4 = st.columns(4)
n1.metric("Maior Temperatura", f"{df_filtered['temp_max'].max()}°C")
n2.metric("Chuva Total", f"{df_filtered['precipitacao'].sum():.1f} mm")
n3.metric("Vento mais forte", f"{df_filtered['vento_rajada'].max()} m/s")
n4.metric("Horas de calor", len(df_filtered[df_filtered['temp_ar'] > temp_threshold]))

# parte grafica
st.subheader("Gráficos de acompanhamento")
t1, t2, t3 = st.tabs(["Temperatura", "Chuva", "Outros"])

with t1:
    f_temp = px.line(df_filtered, x='datetime', y=['temp_min', 'temp_ar', 'temp_max'],
                       title="Temperaturas (Mínima, Média e Máxima)")
    st.plotly_chart(f_temp, use_container_width=True)

with t2:
    f_precip = px.bar(df_filtered, x='datetime', y='precipitacao', title="Volume de chuva por hora")
    st.plotly_chart(f_precip, use_container_width=True)

with t3:
    f_corr = px.scatter(df_filtered, x='temp_ar', y='umidade', color='vento_vel', title="Relação Calor x Umidade")
    st.plotly_chart(f_corr, use_container_width=True)

# tabela de alertas
st.divider()
st.subheader("⚠️ Momentos de alerta")

# filtra a tabela só com o que passou dos limites que você escolheu
alertas = df_filtered[(df_filtered['precipitacao'] >= precip_threshold) | (df_filtered['temp_ar'] >= temp_threshold)]

if not alertas.empty:
    st.dataframe(alertas[['datetime', 'temp_ar', 'precipitacao', 'vento_rajada']].sort_values(by='datetime', ascending=False))
    
    # botão para baixar esses dados de alerta
    csv = alertas.to_csv(index=False).encode('utf-8')
    st.download_button("Baixar lista de alertas (CSV)", data=csv, file_name="alertas.csv")
else:
    st.success("Tudo calmo no período selecionado!")