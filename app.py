import streamlit as st
import json
import os
import random
from num2words import num2words
from weasyprint import HTML
import tempfile
from utils_wa import send_whatsapp_message

st.set_page_config(page_title="BANEGO Generator - Pelindo Sub Regional Jawa", layout="wide")

# Load configuration data
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

users_db = load_json("config_users.json")
vendors_db = load_json("config_vendors.json")

# Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = ""
if "username" not in st.session_state:
    st.session_state.username = ""

def terbilang(nominal):
    try:
        val = int(nominal)
        words = num2words(val, lang='id')
        words_cap = ' '.join([w.capitalize() for w in words.split()])
        return f"({words_cap} Rupiah)"
    except Exception:
        return "(...................................................)"

def format_rupiah(nominal):
    try:
        val = int(nominal)
        return f"Rp. {val:,.0f},-".replace(",", ".")
    except Exception:
        return "Rp. 0,-"

# ================= AUTHENTICATION & OTP PAGE =================
if not st.session_state.authenticated:
    st.title("🔐 Login Sistem Berita Acara Negosiasi (BANEGO)")
    st.markdown("Masukkan username Anda untuk verifikasi OTP via WhatsApp.")

    with st.form("login_form"):
        username_input = st.selectbox("Pilih Username / Akun", options=list(users_db.keys()))
        btn_request_otp = st.form_submit_button("📤 Kirim Kode OTP via WhatsApp")

        if btn_request_otp:
            user_info = users_db.get(username_input)
            if user_info:
                otp = str(random.randint(100000, 999999))
                st.session_state.generated_otp = otp
                st.session_state.username = username_input
                
                phone = user_info["whatsapp"]
                msg = f"Halo {user_info['nama']}, Kode OTP login BANEGO Anda adalah: *{otp}*. Jangan berikan kode ini kepada siapapun."
                
                res = send_whatsapp_message(phone, msg)
                st.session_state.otp_sent = True
                st.success(f"Kode OTP telah dikirimkan ke WhatsApp terdaftar ({phone}). Cek pesan Anda.")
            else:
                st.error("Username tidak ditemukan di database.")

    if st.session_state.otp_sent:
        with st.form("otp_verify_form"):
            st.markdown("### Verifikasi OTP")
            entered_otp = st.text_input("Masukkan 6 Digit Kode OTP", type="password")
            btn_verify = st.form_submit_button("✅ Verifikasi & Masuk")

            if btn_verify:
                if entered_otp == st.session_state.generated_otp:
                    st.session_state.authenticated = True
                    st.success("Login Berhasil! Mengalihkan ke aplikasi...")
                    st.rerun()
                else:
                    st.error("Kode OTP salah! Silakan coba lagi.")

else:
    # ================= MAIN APPLICATION =================
    current_user = users_db.get(st.session_state.username, {})
    
    st.sidebar.title(f"👤 Selamat Datang, {current_user.get('nama', 'User')}")
    st.sidebar.markdown(f"Jabatan: {current_user.get('jabatan', '-')}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.otp_sent = False
        st.session_state.generated_otp = ""
        st.session_state.username = ""
        st.rerun()

    st.title("📝 Generator Berita Acara Negosiasi (BANEGO)")
    st.markdown("Aplikasi pembuatan Berita Acara Negosiasi resmi Sub Regional Jawa terintegrasi dengan database vendor terpisah dan API WhatsApp Watzap.")

    with st.form("banego_main_form"):
        st.subheader("1. Informasi Umum Rapat")
        col1, col2 = st.columns(2)
        with col1:
            nama_pekerjaan = st.text_input("Nama Pekerjaan / Judul Pengadaan", value="Pengadaan Perangkat Penunjang Operasional Sub Bagian Teknologi Informasi Sub Regional Jawa Periode Juni 2026 via Padi UMKM")
            nomor_ba = st.text_input("Nomor Berita Acara (Bisa diedit manual)", value="XXXXX")
            hari_tanggal = st.text_input("Hari / Tanggal Rapat", value="Selasa / 23 Juni 2026")
        with col2:
            pukul = st.text_input("Pukul / Jam Rapat", value="10.00 - Selesai")
            tempat = st.text_input("Tempat Rapat", value="Ruang Rapat Manager Teknologi Informasi Sub Regional Jawa")
            pimpinan_rapat = st.text_input("Pimpinan Rapat", value="Manager Teknologi Informasi Sub Regional Jawa")

        st.subheader("2. Dasar Pelaksanaan Pekerjaan")
        if "dasar_list" not in st.session_state:
            st.session_state.dasar_list = [
                "Nota Dinas Nomor: SI.02/18/6/1/D9/D9.R3-26 tanggal 18 Juni 2026 perihal Izin Prinsip Permohonan Pengadaan Perangkat Penunjang Operasional Sub Bagian Teknologi Informasi Sub Regional Jawa Periode Juni 2026;",
                "Surat Penawaran Harga vendor terkait."
            ]

        dasar_inputs = []
        for i, item in enumerate(st.session_state.dasar_list):
            dasar_inputs.append(st.text_area(f"Dasar Pelaksanaan ke-{i+1}", value=item, key=f"dasar_{i}"))
        
        if st.form_submit_button("➕ Tambah Baris Dasar Pelaksanaan"):
            st.session_state.dasar_list.append("")
            st.rerun()

        st.subheader("3. Informasi Vendor & Harga Negosiasi")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            selected_vendor = st.selectbox("Pilih PT / Vendor dari Database", options=list(vendors_db.keys()))
            harga_sebelum = st.number_input("Harga Sebelum Negosiasi (Rp)", min_value=0, value=122040000, step=100000)
        with col_v2:
            harga_sesudah = st.number_input("Harga Setelah Negosiasi (Rp)", min_value=0, value=107170000, step=100000)
            status_harga = st.text_input("Pernyataan Kesanggupan Vendor", value="dapat diterima oleh vendor dan sekaligus menyatakan kesanggupannya untuk melaksanakan pekerjaan")

        st.subheader("4. Penandatangan & Daftar Hadir")
        st.markdown("Pihak Pelindo:")
        penandatangan_pelindo = st.text_area("Format: Nama | Jabatan (1 baris per orang)", value="Mulyo Wardoyo | Manager Teknologi Informasi Sub Regional Jawa\nYanuar Kresnanto | Officer Teknologi Informasi Sub Regional Jawa")
        
        st.markdown(f"Pihak Vendor ({selected_vendor}) - Diambil dari Database Terpisah:")
        default_vendor_staff = "\n".join(vendors_db.get(selected_vendor, []))
        penandatangan_vendor = st.text_area("Pegawai Vendor (Bisa diedit/ditambah)", value=default_vendor_staff)

        st.subheader("5. Kirim Dokumen ke WhatsApp")
        target_wa_phone = st.text_input("Nomor WhatsApp Tujuan Pengiriman (Contoh: 6281234567890)", value=current_user.get("whatsapp", ""))

        submitted_form = st.form_submit_button("🚀 Generate PDF & Kirim via Watzap API")

    if submitted_form:
        terbilang_sebelum = terbilang(harga_sebelum)
        terbilang_sesudah = terbilang(harga_sesudah)
        format_sebelum = format_rupiah(harga_sebelum)
        format_sesudah = format_rupiah(harga_sesudah)

        pelindo_lines = [l.strip() for l in penandatangan_pelindo.split("\n") if l.strip()]
        vendor_lines = [l.strip() for l in penandatangan_vendor.split("\n") if l.strip()]

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            @page {{ size: A4; margin: 20mm 15mm; background: #fff; }}
            body {{ font-family: 'Times New Roman', Times, serif; font-size: 11pt; line-height: 1.3; color: #000; }}
            .center {{ text-align: center; }}
            .bold {{ font-weight: bold; }}
            table.info-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            table.info-table td {{ vertical-align: top; padding: 3px 0; }}
            table.info-table td.label {{ width: 140px; }}
            table.info-table td.sep {{ width: 15px; text-align: center; }}
            table.sig-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; page-break-inside: avoid; }}
            table.sig-table td {{ vertical-align: top; width: 50%; padding: 5px; }}
            table.attendance {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            table.attendance th, table.attendance td {{ border: 1px solid #000; padding: 5px 8px; font-size: 10pt; }}
            table.attendance th {{ background-color: #f2f2f2; text-align: center; }}
            .page-break {{ page-break-before: always; }}
        </style>
        </head>
        <body>
            <div class="center bold" style="font-size: 12pt;">BERITA ACARA RAPAT</div>
            <div class="center bold" style="font-size: 12pt; margin-bottom: 15px;">TENTANG</div>
            <div class="center bold" style="font-size: 12pt; text-transform: uppercase; margin-bottom: 20px;">{nama_pekerjaan}</div>
            <div class="center" style="margin-bottom: 20px;">Nomor : {nomor_ba}</div>

            <div class="bold">Pelaksanaan Rapat</div>
            <table class="info-table">
                <tr><td class="label">Hari / tanggal</td><td class="sep">:</td><td>{hari_tanggal}</td></tr>
                <tr><td class="label">Pukul</td><td class="sep">:</td><td>{pukul}</td></tr>
                <tr><td class="label">Tempat</td><td class="sep">:</td><td>{tempat}</td></tr>
                <tr><td class="label">Agenda</td><td class="sep">:</td><td>Negosiasi {nama_pekerjaan}</td></tr>
                <tr><td class="label">Pimpinan Rapat</td><td class="sep">:</td><td>{pimpinan_rapat}</td></tr>
                <tr><td class="label">Peserta Rapat</td><td class="sep">:</td><td>Sesuai daftar hadir terlampir.</td></tr>
            </table>

            <div class="bold" style="margin-top: 15px;">Dasar Pelaksanaan</div>
            <ol style="margin-top: 5px; padding-left: 20px;">
        """
        for d in dasar_inputs:
            if d.strip():
                html_content += f"<li style='margin-bottom: 3px;'>{d}</li>"
                
        html_content += f"""
            </ol>

            <div class="bold" style="margin-top: 15px;">Jalannya Pembahasan</div>
            <p style="margin-top: 5px; text-align: justify;">Negosiasi {nama_pekerjaan}.</p>

            <div class="bold" style="margin-top: 15px;">Hasil Pembahasan</div>
            <ol style="margin-top: 5px; padding-left: 20px;">
                <li style="margin-bottom: 5px; text-align: justify;">Telah diadakan negosiasi terhadap harga penawaran dengan {selected_vendor} terkait {nama_pekerjaan}.</li>
                <li style="margin-bottom: 5px; text-align: justify;">Dari pembahasan tersebut butir 1 (satu) diatas, maka diperoleh hasil negosiasi sebagai berikut:
                    <ul style="list-style-type: lower-alpha; margin-top: 5px;">
                        <li style="margin-bottom: 4px;">Harga penawaran {selected_vendor} sebesar <b>{format_sebelum}</b> <b>{terbilang_sebelum}</b> belum termasuk PPN (rincian terlampir).</li>
                        <li style="margin-bottom: 4px;">Harga setelah negosiasi sebesar <b>{format_sesudah}</b> <b>{terbilang_sesudah}</b> belum termasuk PPN dan harga tersebut {status_harga} (rincian terlampir).</li>
                    </ul>
                </li>
                <li style="margin-bottom: 5px; text-align: justify;">Progres pekerjaan dilaporkan kepada tim IT Sub Regional Jawa.</li>
                <li style="margin-bottom: 5px; text-align: justify;">Sambil menunggu proses purchase order (PO), diperintahkan kepada kontraktor agar segera melaksanakan pekerjaan tersebut.</li>
            </ol>

            <div class="bold" style="margin-top: 15px;">Penutup</div>
            <p style="margin-top: 5px; text-align: justify;">Demikian Berita Acara Rapat ini dibuat agar dapat digunakan sebagaimana mestinya.</p>

            <div style="margin-top: 30px; float: right; width: 320px;">
                Surabaya, ................................<br>
                <b>PT. Pelindo (Persero) Sub Regional Jawa</b>
            </div>
            <div style="clear: both;"></div>

            <table class="sig-table">
                <tr>
                    <td>
                        <div style="min-height: 70px;"></div>
                        <b>{pelindo_lines[0].split('|')[0].strip() if pelindo_lines else 'Mulyo Wardoyo'}</b><br>
                        {pelindo_lines[0].split('|')[1].strip() if pelindo_lines and '|' in pelindo_lines[0] else 'Manager TI Sub Regional Jawa'}
                    </td>
                    <td>
                        <div style="min-height: 70px;"></div>
                        <b>{vendor_lines[0].split('|')[0].strip() if vendor_lines else 'Perwakilan Vendor'}</b><br>
                        {selected_vendor}
                    </td>
                </tr>
        """
        
        max_len = max(len(pelindo_lines), len(vendor_lines))
        for i in range(1, max_len):
            p_name = pelindo_lines[i].split('|')[0].strip() if i < len(pelindo_lines) else ""
            p_title = pelindo_lines[i].split('|')[1].strip() if i < len(pelindo_lines) and '|' in pelindo_lines[i] else ""
            v_name = vendor_lines[i].split('|')[0].strip() if i < len(vendor_lines) else ""
            v_title = vendor_lines[i].split('|')[1].strip() if i < len(vendor_lines) and '|' in vendor_lines[i] else ""
            
            html_content += f"""
                <tr>
                    <td><div style="min-height: 60px;"></div><b>{p_name}</b><br>{p_title}</td>
                    <td><div style="min-height: 60px;"></div><b>{v_name}</b><br>{v_title}</td>
                </tr>
            """

        html_content += f"""
            </table>

            <div class="page-break"></div>

            <div class="center bold" style="font-size: 12pt; margin-bottom: 15px;">DAFTAR HADIR</div>
            <table class="info-table" style="margin-bottom: 15px;">
                <tr><td class="label">Hari / Tanggal</td><td class="sep">:</td><td>{hari_tanggal}</td></tr>
                <tr><td class="label">Pukul</td><td class="sep">:</td><td>{pukul}</td></tr>
                <tr><td class="label">Tempat</td><td class="sep">:</td><td>{tempat}</td></tr>
                <tr><td class="label">Agenda</td><td class="sep">:</td><td>Negosiasi {nama_pekerjaan}</td></tr>
            </table>

            <table class="attendance">
                <thead>
                    <tr><th style="width: 40px;">NO.</th><th>N A M A</th><th>JABATAN / INSTANSI</th><th style="width: 100px;">TANDA TANGAN</th></tr>
                </thead>
                <tbody>
        """
        
        all_attendees = []
        for line in pelindo_lines:
            parts = line.split('|')
            all_attendees.append((parts[0].strip(), parts[1].strip() if len(parts) > 1 else "Pelindo Sub Regional Jawa"))
        for line in vendor_lines:
            parts = line.split('|')
            all_attendees.append((parts[0].strip(), parts[1].strip() if len(parts) > 1 else selected_vendor))
            
        for idx, (att_name, att_title) in enumerate(all_attendees, 1):
            html_content += f"<tr><td class='center'>{idx}.</td><td>{att_name}</td><td>{att_title}</td><td class='center'>{idx}. ........</td></tr>"
            
        for idx in range(len(all_attendees) + 1, 6):
            html_content += f"<tr><td class='center'>{idx}.</td><td></td><td></td><td class='center'>{idx}. ........</td></tr>"

        html_content += "</tbody></table></body></html>"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            output_pdf_path = tmp_pdf.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp_html:
            tmp_html.write(html_content)
            input_html_path = tmp_html.name

        HTML(filename=input_html_path).write_pdf(output_pdf_path)

        st.success("✅ Dokumen PDF Berita Acara berhasil dibuat!")

        with open(output_pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()

        st.download_button(
            label="📥 Download Berita Acara PDF",
            data=pdf_bytes,
            file_name=f"BA_Negosiasi_{nomor_ba.replace('/', '_')}.pdf",
            mime="application/octet-stream"
        )

        if target_wa_phone:
            caption_text = f"Berikut adalah Berita Acara Negosiasi (BANEGO) untuk pekerjaan *{nama_pekerjaan* with Nomor: *{nomor_ba}*."
            wa_response = send_whatsapp_message(target_wa_phone, caption_text)
            
            if wa_response.get("status") in [True, "true", 200, "200"]:
                st.success(f"🚀 Berhasil mengirimkan notifikasi ke WhatsApp nomor {target_wa_phone} via Watzap API!")
            else:
                st.warning(f"⚠️ Terkirim dengan status API: {wa_response}")
