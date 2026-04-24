import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- KONFIGURASI HALAMAN ---
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

# --- FUNGSI BANTU ---
def find_column(columns, keywords):
    for col in columns:
        if any(k in col.lower() for k in keywords):
            return col
    return None

# --- MAIN PROCESS ---
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success(f"Berhasil memuat: {uploaded_file.name}")

        if df.empty:
            st.warning("File kosong.")
            st.stop()

        all_cols = df.columns.tolist()

        # --- DETEKSI KOLOM ---
        default_arah = find_column(all_cols, ['arah', 'deg', 'direction'])
        default_speed = find_column(all_cols, ['kecepatan', 'speed', 'ms'])

        col_arah = st.selectbox(
            "Kolom Arah (derajat):",
            all_cols,
            index=all_cols.index(default_arah) if default_arah in all_cols else 0
        )

        col_speed = st.selectbox(
            "Kolom Kecepatan (m/s):",
            all_cols,
            index=all_cols.index(default_speed) if default_speed in all_cols else 0
        )

        # --- CLEANING DATA ---
        df[col_arah] = pd.to_numeric(df[col_arah], errors='coerce')
        df[col_speed] = pd.to_numeric(df[col_speed], errors='coerce')

        df = df.dropna(subset=[col_arah, col_speed])

        if df.empty:
            st.error("Data tidak valid setelah dibersihkan.")
            st.stop()

        # --- BINNING KECEPATAN ---
        bins = [0, 2, 4, 6, 8, np.inf]
        labels = ['0-2 m/s', '2-4 m/s', '4-6 m/s', '6-8 m/s', '>8 m/s']

        df['Speed Range'] = pd.cut(
            df[col_speed],
            bins=bins,
            labels=labels,
            include_lowest=True
        )

        # --- BINNING ARAH (16 arah mata angin) ---
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                      'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

        df['Direction_Bin'] = ((df[col_arah] + 11.25) % 360 // 22.5).astype(int)
        df['Arah'] = df['Direction_Bin'].apply(lambda x: directions[x])

        # --- AGREGASI DATA ---
        df_plot = df.groupby(['Arah', 'Speed Range']).size().reset_index(name='Freq')

        total = df_plot['Freq'].sum()
        df_plot['Persentase (%)'] = (df_plot['Freq'] / total) * 100

        # --- VISUALISASI ---
        fig = px.bar_polar(
            df_plot,
            r="Persentase (%)",
            theta="Arah",
            color="Speed Range",
            color_discrete_sequence=px.colors.sequential.Plasma_r,
            category_orders={
                "Arah": directions,
                "Speed Range": labels
            },
            template="plotly_white"
        )

        fig.update_layout(
            polar=dict(
                angularaxis=dict(
                    direction='clockwise',
                    rotation=90
                )
            ),
            title="Wind Rose Diagram"
        )

        st.plotly_chart(fig, use_container_width=True)

        # --- PREVIEW DATA ---
        with st.expander("Lihat Data"):
            st.dataframe(df.head())

    except Exception as e:
        st.error(f"Terjadi error: {e}")

else:
    st.info("Silakan unggah file CSV untuk memulai.")
