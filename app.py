from flask import Flask, render_template, request
import pandas as pd
import matplotlib
# Gunakan 'Agg' backend agar Matplotlib tidak membuka GUI window (penting untuk web server)
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from windrose import WindroseAxes
import io
import base64

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_url = None
    error_msg = None

    if request.method == 'POST':
        # Cek apakah ada file yang diunggah
        file = request.files.get('file_csv')
        
        if file and file.filename != '':
            try:
                # 1. Baca CSV
                df = pd.read_csv(file)
                
                # Pastikan kolom ada
                if 'Arah_Angin_deg' not in df.columns or 'Kecepatan_Angin_ms' not in df.columns:
                    raise ValueError("Kolom 'Arah_Angin_deg' atau 'Kecepatan_Angin_ms' tidak ditemukan.")

                wd = df['Arah_Angin_deg']
                ws = df['Kecepatan_Angin_ms']

                # 2. Buat Plot Wind Rose
                fig = plt.figure(figsize=(8, 8), dpi=100)
                ax = WindroseAxes.from_ax(fig=fig)
                
                # =========================================================
                # PENGATURAN POSISI MATA ANGIN (KOMPAS)
                # =========================================================
                ax.set_theta_zero_location("N") # Mengatur 0 derajat (Utara) berada di paling atas
                ax.set_theta_direction(-1)      # Mengatur putaran searah jarum jam (clockwise)
                # =========================================================

                ax.bar(wd, ws, normed=True, opening=0.85, edgecolor='white', nsector=16, cmap=plt.cm.viridis)
                ax.set_legend(title="Kecepatan (m/s)", loc='lower right', decimal_places=1, fontsize=10)
                
                # Karena arah sudah searah jarum jam dimulai dari Utara (atas), 
                # urutan array label ini sudah sangat tepat.
                ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'], fontsize=12)
                
                plt.title("Grafik Wind Rose", fontsize=14, pad=20)

                # 3. Simpan plot ke dalam buffer memori (tidak disave ke hardisk)
                img = io.BytesIO()
                plt.savefig(img, format='png', bbox_inches='tight')
                img.seek(0)
                plt.close(fig) # Bersihkan memori

                # 4. Konversi gambar ke base64 agar bisa dibaca HTML
                plot_url = base64.b64encode(img.getvalue()).decode('utf8')

            except Exception as e:
                error_msg = str(e)

    # Render template index.html dengan mengirimkan data plot atau pesan error
    return render_template('index.html', plot_url=plot_url, error_msg=error_msg)

if __name__ == '__main__':
    # Menambahkan use_reloader=False akan mematikan fitur auto-restart
    app.run(debug=True, use_reloader=False)