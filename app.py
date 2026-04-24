import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ==============================
# KONFIGURASI HALAMAN
# ==============================
st.set_page_config(page_title="Wind Rose Dashboard", layout="wide")

st.title("🌬️ Wind Rose Analysis Dashboard")
st.markdown("Analisis data arah & kecepatan angin (IoT / Kelautan / Lingkungan)")

# ==============================
# SIDEBAR
# ==============================
st.sidebar.header("📘 Panduan")

template_csv = """Timestamp,Arah_Angin_deg,Kecepatan_Angin_ms
2025-10-27 00:00:00,259.9,3.38
2025-10-27 01:00:00,222.92,4.79
"""

st.sidebar.download_button(
    label="📥 Download Template CSV",
    data=template_csv,
    file_name="template_wind.csv",
    mime="text/csv"
)

# ==============================
# UPLOAD FILE
# ==============================
uploaded_file = st.file_uploader("Upload file CSV", type=["csv"])

# ==============================
# FUNGSI UTILITAS
# ==============================
def detect_column(columns, keywords):
    for col in columns:
        if any(k in col.lower() for k in keywords):
            return col
    return None

def clean_data(df, col_dir, col_spd):
    df[col_dir] = pd.to_numeric(df[col_dir], errors='coerce')
    df[col_spd] = pd.to_numeric(df[col_spd], errors='coerce')
    df = df.dropna(subset=[col_dir, col_spd])
    return df

def create_wind_bins(df, col_spd):
    bins = [0, 2, 4, 6, 8, np.inf]
    labels = ['0-2 m/s', '2-4 m/s', '4-6 m/s', '6-8 m/s', '>8 m/s']

    df['Speed Range'] = pd.cut(
        df[col_spd],
        bins=bins,
        labels=labels,
        include_lowest=True
    )
    return df, labels

def create_direction_bins(df, col_dir):
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

    df['Direction_Bin'] = ((df[col_dir] + 11.25) % 360 // 22.5).astype(int)
    df['Arah'] = df['Direction_Bin'].apply(lambda x: directions[x])

    return df, directions

# ==============================
# MAIN LOGIC
# ==============================
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success(f"File loaded: {uploaded_file.name}")

        if df.empty:
            st.warning("File kosong.")
            st.stop()

        # ==============================
        # PARSE TIMESTAMP
        # ==============================
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
            df = df.dropna(subset=['Timestamp'])

            if not df.empty:
                min_date = df['Timestamp'].min()
                max_date = df['Timestamp'].max()

                start_date, end_date = st.date_input(
                    "📅 Filter tanggal:",
                    [min_date, max_date]
                )

                df = df[
                    (df['Timestamp'] >= pd.to_datetime(start_date)) &
                    (df['Timestamp'] <= pd.to_datetime(end_date))
                ]

        # ==============================
        # DETEKSI KOLOM
        # ==============================
        cols = df.columns.tolist()

        col_dir_default = detect_column(cols, ['arah', 'deg', 'direction'])
        col_spd_default = detect_column(cols, ['kecepatan', 'speed', 'ms'])

        col_dir = st.selectbox(
            "Pilih kolom arah (derajat):",
            cols,
            index=cols.index(col_dir_default) if col_dir_default in cols else 0
        )

        col_spd = st.selectbox(
            "Pilih kolom kecepatan (m/s):",
            cols,
            index=cols.index(col_spd_default) if col_spd_default in cols else 0
        )

        # ==============================
        # CLEANING
        # ==============================
        df = clean_data(df, col_dir, col_spd)

        if df.empty:
            st.error("Data kosong setelah cleaning.")
            st.stop()

        # ==============================
        # BINNING
        # ==============================
        df, speed_labels = create_wind_bins(df, col_spd)
        df, directions = create_direction_bins(df, col_dir)

        # ==============================
        # AGREGASI
        # ==============================
        df_plot = df.groupby(['Arah', 'Speed Range']).size().reset_index(name='Freq')
        total = df_plot['Freq'].sum()

        df_plot['Persentase (%)'] = (df_plot['Freq'] / total) * 100

        # ==============================
        # VISUALISASI
        # ==============================
        fig = px.bar_polar(
            df_plot,
            r="Persentase (%)",
            theta="Arah",
            color="Speed Range",
            color_discrete_sequence=px.colors.sequential.Plasma_r,
            category_orders={
                "Arah": directions,
                "Speed Range": speed_labels
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

        # ==============================
        # METRICS
        # ==============================
        col1, col2, col3 = st.columns(3)

        col1.metric("Total Data", len(df))
        col2.metric("Rata-rata Kecepatan", f"{df[col_spd].mean():.2f} m/s")
        col3.metric("Kecepatan Maks", f"{df[col_spd].max():.2f} m/s")

        # ==============================
        # PREVIEW DATA
        # ==============================
        with st.expander("🔍 Lihat Data"):
            st.dataframe(df.head())

    except Exception as e:
        st.error(f"Terjadi error: {e}")

else:
    st.info("Silakan upload file CSV untuk memulai.")
