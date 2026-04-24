import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Konfigurasi Halaman
st.set_page_config(page_title="Wind Rose OSO University", layout="wide")

st.title("📊 Wind Rose Analysis Dashboard")
st.markdown("Aplikasi web berbasis Python untuk analisis data angin (IoT & Kelautan).")

# --- SIDEBAR ---
st.sidebar.header("Panduan")
template_csv = "Arah_Angin_deg,Kecepatan_Angin_ms\n45,2.5\n180,5.0\n225,8.5"
st.sidebar.download_button(
    label="📥 Download Template CSV",
    data=template_csv,
    file_name="template_angin.csv",
    mime="text/csv"
)

# --- UPLOAD FILE ---
uploaded_file = st.file_uploader("Unggah file CSV Anda", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success(f"Berhasil memuat: {uploaded_file.name}")
        
        # Deteksi Kolom Otomatis
        all_cols = df.columns.tolist()
        def find_col(keys, targets):
            for c in keys:
                if any(t in c.lower() for t in targets): return c
            return keys

        col_arah = st.selectbox("Kolom Arah (Deg):", all_cols, index=all_cols.index(find_col(all_cols, ['arah', 'deg', 'dir'])))
        col_speed = st.selectbox("Kolom Kecepatan (m/s):", all_cols, index=all_cols.index(find_col(all_cols, ['kecepatan', 'speed', 'ms'])))

        # Pembersihan Data
        df[col_arah] = pd.to_numeric(df[col_arah], errors='coerce')
        df[col_speed] = pd.to_numeric(df[col_speed], errors='coerce')
        df = df.dropna(subset=[col_arah, col_speed])

        # Binning & Plotting
        bins =
        labels = ['0-2 m/s', '2-4 m/s', '4-6 m/s', '6-8 m/s', '>8 m/s']
        df['Speed Range'] = pd.cut(df[col_speed], bins=bins, labels=labels)
        
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        df['Direction_Bin'] = ((df[col_arah] + 11.25) % 360 // 22.5).astype(int)
        df['Arah'] = df['Direction_Bin'].apply(lambda x: directions[x])

        df_plot = df.groupby(['Arah', 'Speed Range']).size().reset_index(name='Freq')
        df_plot['Persentase (%)'] = (df_plot['Freq'] / df_plot['Freq'].sum()) * 100

        fig = px.bar_polar(
            df_plot, r="Persentase (%)", theta="Arah", color="Speed Range",
            color_discrete_sequence=px.colors.sequential.Plasma_r,
            category_orders={"Arah": directions, "Speed Range": labels},
            template="plotly_white"
        )
        
        fig.update_layout(polar=dict(angularaxis=dict(direction='clockwise', rotation=90)))
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Silakan unggah file untuk memulai.")
