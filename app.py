import streamlit as st
import json
import os
import random
from num2words import num2words
import tempfile
from utils_wa import send_whatsapp_message

# ReportLab imports for pure-python robust PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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

        # Generate PDF using ReportLab
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            output_pdf_path = tmp_pdf.name

        doc = SimpleDocTemplate(output_pdf_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        
        style_normal = ParagraphStyle('NormalText', parent=styles['Normal'], fontName='Times-Roman', fontSize=11, leading=14, alignment=4)
        style_bold = ParagraphStyle('BoldText', parent=style_normal, fontName='Times-Bold')
        style_center = ParagraphStyle('CenterText', parent=style_normal, alignment=1)
        style_center_bold = ParagraphStyle('CenterBoldText', parent=style_bold, alignment=1)
        style_title = ParagraphStyle('TitleText', parent=style_center_bold, fontSize=12, leading=16)

        story = []

        # Header Title
        story.append(Paragraph("BERITA ACARA RAPAT", style_title))
        story.append(Paragraph("TENTANG", style_title))
        story.append(Paragraph(nama_pekerjaan.upper(), style_title))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Nomor : {nomor_ba}", style_center))
        story.append(Spacer(1, 15))

        # Pelaksanaan Rapat
        story.append(Paragraph("<b>Pelaksanaan Rapat</b>", style_normal))
        info_data = [
            [Paragraph("Hari / tanggal", style_normal), Paragraph(":", style_center), Paragraph(hari_tanggal, style_normal)],
            [Paragraph("Pukul", style_normal), Paragraph(":", style_center), Paragraph(pukul, style_normal)],
            [Paragraph("Tempat", style_normal), Paragraph(":", style_center), Paragraph(tempat, style_normal)],
            [Paragraph("Agenda", style_normal), Paragraph(":", style_center), Paragraph(f"Negosiasi {nama_pekerjaan}", style_normal)],
            [Paragraph("Pimpinan Rapat", style_normal), Paragraph(":", style_center), Paragraph(pimpinan_rapat, style_normal)],
            [Paragraph("Peserta Rapat", style_normal), Paragraph(":", style_center), Paragraph("Sesuai daftar hadir terlampir.", style_normal)],
        ]
        t_info = Table(info_data, colWidths=[120, 15, 385])
        t_info.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        story.append(t_info)
        story.append(Spacer(1, 10))

        # Dasar Pelaksanaan
        story.append(Paragraph("<b>Dasar Pelaksanaan</b>", style_normal))
        for idx, d in enumerate(dasar_inputs, 1):
            if d.strip():
                story.append(Paragraph(f"{idx}. {d}", style_normal))
        story.append(Spacer(1, 10))

        # Jalannya Pembahasan
        story.append(Paragraph("<b>Jalannya Pembahasan</b>", style_normal))
        story.append(Paragraph(f"Negosiasi {nama_pekerjaan}.", style_normal))
        story.append(Spacer(1, 10))

        # Hasil Pembahasan
        story.append(Paragraph("<b>Hasil Pembahasan</b>", style_normal))
        story.append(Paragraph(f"1. Telah diadakan negosiasi terhadap harga penawaran dengan {selected_vendor} terkait {nama_pekerjaan}.", style_normal))
        story.append(Paragraph("2. Dari pembahasan tersebut butir 1 (satu) diatas, maka diperoleh hasil negosiasi sebagai berikut:", style_normal))
        story.append(Paragraph(f"    a. Harga penawaran {selected_vendor} sebesar <b>{format_sebelum}</b> <b>{terbilang_sebelum}</b> belum termasuk PPN (rincian terlampir).", style_normal))
        story.append(Paragraph(f"    b. Harga setelah negosiasi sebesar <b>{format_sesudah}</b> <b>{terbilang_sesudah}</b> belum termasuk PPN dan harga tersebut {status_harga} (rincian terlampir).", style_normal))
        story.append(Paragraph("3. Progres pekerjaan dilaporkan kepada tim IT Sub Regional Jawa.", style_normal))
        story.append(Paragraph("4. Sambil menunggu proses purchase order (PO), diperintahkan kepada kontraktor agar segera melaksanakan pekerjaan tersebut.", style_normal))
        story.append(Spacer(1, 10))

        # Penutup
        story.append(Paragraph("<b>Penutup</b>", style_normal))
        story.append(Paragraph("Demikian Berita Acara Rapat ini dibuat agar dapat digunakan sebagaimana mestinya.", style_normal))
        story.append(Spacer(1, 15))

        # Signatures
        story.append(Paragraph("Surabaya, ................................", ParagraphStyle('RightDate', parent=style_normal, alignment=2)))
        story.append(Paragraph("<b>PT. Pelindo (Persero) Sub Regional Jawa</b>", ParagraphStyle('RightDateBold', parent=style_bold, alignment=2)))
        story.append(Spacer(1, 40))

        p_name_1 = pelindo_lines[0].split('|')[0].strip() if pelindo_lines else 'Mulyo Wardoyo'
        p_title_1 = pelindo_lines[0].split('|')[1].strip() if pelindo_lines and '|' in pelindo_lines[0] else 'Manager TI Sub Regional Jawa'
        v_name_1 = vendor_lines[0].split('|')[0].strip() if vendor_lines else 'Perwakilan Vendor'

        sig_data = [
            [Paragraph(f"<b>{p_name_1}</b><br/>{p_title_1}", style_normal), Paragraph(f"<b>{v_name_1}</b><br/>{selected_vendor}", style_normal)]
        ]
        
        max_len = max(len(pelindo_lines), len(vendor_lines))
        for i in range(1, max_len):
            p_n = pelindo_lines[i].split('|')[0].strip() if i < len(pelindo_lines) else ""
            p_t = pelindo_lines[i].split('|')[1].strip() if i < len(pelindo_lines) and '|' in pelindo_lines[i] else ""
            v_n = vendor_lines[i].split('|')[0].strip() if i < len(vendor_lines) else ""
            v_t = vendor_lines[i].split('|')[1].strip() if i < len(vendor_lines) and '|' in vendor_lines[i] else ""
            sig_data.append([Paragraph(f"<b>{p_n}</b><br/>{p_t}", style_normal), Paragraph(f"<b>{v_n}</b><br/>{v_t}", style_normal)])

        t_sig = Table(sig_data, colWidths=[260, 260])
        t_sig.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 30)]))
        story.append(t_sig)

        # Page Break for Attendance
        story.append(PageBreak())

        # Daftar Hadir
        story.append(Paragraph("<b>DAFTAR HADIR</b>", style_title))
        story.append(Spacer(1, 10))
        story.append(t_info)
        story.append(Spacer(1, 15))

        # Attendance Table
        att_table_data = [["NO.", "N A M A", "JABATAN / INSTANSI", "TANDA TANGAN"]]
        all_attendees = []
        for line in pelindo_lines:
            parts = line.split('|')
            all_attendees.append((parts[0].strip(), parts[1].strip() if len(parts) > 1 else "Pelindo Sub Regional Jawa"))
        for line in vendor_lines:
            parts = line.split('|')
            all_attendees.append((parts[0].strip(), parts[1].strip() if len(parts) > 1 else selected_vendor))
            
        for idx, (att_name, att_title) in enumerate(all_attendees, 1):
            att_table_data.append([str(idx), att_name, att_title, f"{idx}. ........"])
            
        for idx in range(len(all_attendees) + 1, 6):
            att_table_data.append([str(idx), "", "", f"{idx}. ........"])

        t_att = Table(att_table_data, colWidths=[35, 170, 225, 90])
        t_att.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_att)

        doc.build(story)

        st.success("✅ Dokumen PDF Berita Acara berhasil dibuat dengan ReportLab!")

        with open(output_pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()

        st.download_button(
            label="📥 Download Berita Acara PDF",
            data=pdf_bytes,
            file_name=f"BA_Negosiasi_{nomor_ba.replace('/', '_')}.pdf",
            mime="application/octet-stream"
        )

        if target_wa_phone:
            caption_text = f"Berikut adalah Berita Acara Negosiasi (BANEGO) untuk pekerjaan *{nama_pekerjaan}* dengan Nomor: *{nomor_ba}*."
            wa_response = send_whatsapp_message(target_wa_phone, caption_text)
            
            if wa_response.get("status") in [True, "true", 200, "200"]:
                st.success(f"🚀 Berhasil mengirimkan notifikasi ke WhatsApp nomor {target_wa_phone} via Watzap API!")
            else:
                st.warning(f"⚠️ Terkirim dengan status API: {wa_response}")
