from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import psycopg2
import psycopg2.extras
from datetime import date
import os
import math


def connect():
    conn = psycopg2.connect(
        host="localhost",
        database="SIMPANANN",   
        user="postgres",
        password="Azma140700",
         
    )
    return conn


def query_execute(conn, sql, params=None, return_lastrow=False):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(sql, params or ())
    lastrow = None
    if return_lastrow:
        try:
            lastrow = cur.fetchone()
        except:
            lastrow = None
    conn.commit()
    cur.close()
    return lastrow

def query_fetch(conn, sql, params=None):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    return rows


print (r"""

███████╗██╗███╗   ███╗██████╗  █████╗ ███╗   ██╗ █████╗ ███╗   ██╗
██╔════╝██║████╗ ████║██╔══██╗██╔══██╗████╗  ██║██╔══██╗████╗  ██║
███████╗██║██╔████╔██║██████╔╝███████║██╔██╗ ██║███████║██╔██╗ ██║
╚════██║██║██║╚██╔╝██║██╔═══╝ ██╔══██║██║╚██╗██║██╔══██║██║╚██╗██║
███████║██║██║ ╚═╝ ██║██║     ██║  ██║██║ ╚████║██║  ██║██║ ╚████║
╚══════╝╚═╝╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝

""")

def input_required(pesan):
    while True:
        value = input(pesan).strip() 
        if value != "":
            return value
        print("Input tidak boleh kosong!")

def input_int(pesan):
    while True:
        try:
            return int(input_required(pesan))
        except:
            print("Harus bilangan bulat!")

def input_luas_lahan(pesan="luas lahan (ha, maksimal 2): ", min_value=0.5, max_value=2.0):
    while True:
        try:
            luas_lahan= float(input_required(pesan))
        except:
            print("Harus berupa angka desimal atau bilangan bulat!")
            continue

        if luas_lahan < min_value :
            print(f"Luas lahan minimal {min_value} ha.")
            continue
        if luas_lahan > max_value :
            print(f"Luas lahan tidak boleh lebih dari {max_value} ha.")
            continue

        return luas_lahan
        
def get_or_create_role(conn, role_name_input):
   
    daftar_role = {
        "admin": "Admin",
        "ketua": "Ketua kelompok tani",
        "petani": "Petani"
    }
    nama_roles = daftar_role.get(role_name_input.lower(), role_name_input)

    rows = query_fetch(conn,
        "SELECT id_roles FROM roles WHERE LOWER(nama_roles) = LOWER(%s)",
        (nama_roles,)
    )
    if rows:
        return rows[0]['id_roles']  


    row = query_execute(conn,
        "INSERT INTO roles (nama_roles) VALUES (%s) RETURNING id_roles",
        (nama_roles,),
        return_lastrow=True
    )
    return row['id_roles']

def register(conn):
    os.system('cls')
    print("\n=== REGISTER USER ===")
    nama = input_required("Nama lengkap : ")

    
    cek_ketua = None
    nama_kecamatan = None
    nama_alamat = None
    ketua_dipilih = None

    
    while True:
        username = input_required("Username : ")

        ada = query_fetch(conn,
            "SELECT 1 FROM users WHERE username = %s",
            (username,)
        )
        if ada:
            print("Username sudah dipakai, silakan gunakan username lain.")
        else:
            break

    
    while True:
        pw = input("Password: ")
        pw2 = input("Ulangi password: ")
        if pw != pw2:
            print("Password tidak cocok!")
        else:
            break

    nomor_hp = input_required("Nomor HP : ")

    
    print("\nPilih role:")
    print("1. Admin")
    print("2. Ketua kelompok tani")
    print("3. Petani")

    daftar_role= {
        "1": "Admin",
        "2": "Ketua kelompok tani",
        "3": "Petani"
    }

    role_input = ""
    while role_input not in daftar_role:
        role_input = input_required("Pilih (1/2/3): ")

    nama_role = daftar_role[role_input]

    sk_path = None

   
    if nama_role == "Ketua kelompok tani":
        print("\n=== Data Wilayah Ketua ===")
        nama_kecamatan = input_required("Masukkan Kecamatan Ketua: ")
        nama_alamat    = input_required("Masukkan Alamat Ketua: ")

        
        cek_ketua = query_fetch(conn, """
            SELECT u.nama
            FROM users u
            JOIN user_role ur ON ur.id_users = u.id_users
            JOIN roles r ON r.id_roles = ur.id_roles
            JOIN kecamatan k ON k.id_users = u.id_users
            WHERE r.nama_roles = 'Ketua kelompok tani'
              AND LOWER(TRIM(k.nama_kecamatan)) = LOWER(TRIM(%s))
        """, (nama_kecamatan,))

        if cek_ketua:
            print(f"\nKecamatan '{nama_kecamatan}' sudah memiliki ketua: {cek_ketua[0]['nama']}")
            print("Pendaftaran ketua baru untuk kecamatan ini tidak diperbolehkan.\n")
            input("Tekan Enter untuk kembali...")
            os.system('cls')
            return

        
        while True:
            sk_path = input_required("Masukkan path file SK (.pdf): ")
            if not sk_path.lower().endswith(".pdf"):
                print("File SK harus berformat .pdf!")
                continue
            if not os.path.exists(sk_path):
                print("File tidak ditemukan di path tersebut!")
                continue

            print(" SK ketua ditemukan dan valid.")
            break

   
    elif nama_role == "Petani":
        rows_kec = query_fetch(conn, """
            SELECT DISTINCT ON (LOWER(TRIM(nama_kecamatan)))
                   TRIM(nama_kecamatan) AS nama_kecamatan
            FROM kecamatan
            WHERE nama_kecamatan IS NOT NULL
            ORDER BY LOWER(TRIM(nama_kecamatan)), TRIM(nama_kecamatan);
        """)

        if rows_kec:
            print("\nPilih kecamatan:")
            for i, r in enumerate(rows_kec, start=1):
                print(f"{i}. {r['nama_kecamatan']}")

            index_kecamatan_yang_dipilih = -1

            while index_kecamatan_yang_dipilih < 0 or index_kecamatan_yang_dipilih >= len(rows_kec):
                index_kecamatan_yang_dipilih = input_int("Pilih nomor kecamatan: ") - 1
            nama_kecamatan = rows_kec[index_kecamatan_yang_dipilih]['nama_kecamatan']
        else:
            print("\nBelum ada data kecamatan di tabel, isi manual.")
            nama_kecamatan = input_required("Nama kecamatan : ")

        rows_ketua = query_fetch(conn, """
            SELECT DISTINCT u.id_users, u.nama, k.nama_kecamatan
            FROM users u
            JOIN user_role ur ON ur.id_users = u.id_users
            JOIN roles r ON r.id_roles = ur.id_roles
            JOIN kecamatan k ON k.id_users = u.id_users
            WHERE r.nama_roles = 'Ketua kelompok tani'
            ORDER BY u.nama
        """)

        if rows_ketua:
            while True:
                print("\nPilih Ketua Kelompok Tani:")
                for i, r in enumerate(rows_ketua, start=1):
                    print(f"{i}. {r['nama']} (kec: {r['nama_kecamatan']})")

                index_ketua_yang_dipilih = -1
                while index_ketua_yang_dipilih < 0 or index_ketua_yang_dipilih >= len(rows_ketua):
                    index_ketua_yang_dipilih = input_int("Pilih nomor ketua: ") - 1

                ketua_dipilih = rows_ketua[index_ketua_yang_dipilih]
                ketua_kec = ketua_dipilih['nama_kecamatan']

                if ketua_kec.strip().lower() != nama_kecamatan.strip().lower():
                    print(
                        f" Kecamatan ketua tani tidak sesuai!\n"
                        f" Kecamatan ketua : {ketua_kec}\n"
                        f" Kecamatan petani: {nama_kecamatan}\n"
                        "Silahkan pilih ketua yang sesuai dengan kecamatan Anda."
                    )
                    continue
                else:
                    print(f"Ketua yang dipilih: {ketua_dipilih['nama']} (Kec: {ketua_kec})")
                    os.system('cls')
                    break
        else:
            print(f"\nBelum ada ketua kelompok tani terdaftar di sistem.")
            os.system('cls')

        nama_alamat = input_required("Alamat lengkap : ")

    

    cek_role = query_fetch(conn,
        "SELECT id_roles FROM roles WHERE nama_roles = %s",
        (nama_role,)
    )

    if cek_role:
        id_roles = cek_role[0]['id_roles']
    else:
        row_role = query_execute(conn,
            "INSERT INTO roles (nama_roles) VALUES (%s) RETURNING id_roles",
            (nama_role,),
            return_lastrow=True
        )
        id_roles = row_role['id_roles']

    new_user = query_execute(conn, """
        INSERT INTO users (nama, username, password, nomor_hp)
        VALUES (%s, %s, %s, %s)
        RETURNING id_users
    """, (nama, username, pw, nomor_hp), return_lastrow=True)

    id_users = new_user['id_users']

    query_execute(conn, """
        INSERT INTO user_role (id_users, id_roles)
        VALUES (%s, %s)
    """, (id_users, id_roles))


    if nama_role in ("Ketua kelompok tani", "Petani"):
        query_execute(conn, """
            INSERT INTO kecamatan (id_users, nama_kecamatan, nama_alamat)
            VALUES (%s, %s, %s)
        """, (id_users, nama_kecamatan, nama_alamat))

    print(f"\n User '{nama}' berhasil diregistrasi sebagai {nama_role}")
    if nama_role == "Ketua kelompok tani":
        print(f"  (SK ketua disimpan di: {sk_path})")
    if nama_role == "Petani" and ketua_dipilih:
        print(f"  Terdaftar di kecamatan {nama_kecamatan}, ketua: {ketua_dipilih['nama']}")

    input("Tekan Enter untuk melanjutkan...")
    os.system('cls')


def login(conn):
    os.system('cls')
    print("=== LOGIN ===")
    username = input_required("Username: ")
    pw = input("Password: ")
    os.system('cls')

    rows = query_fetch(conn,
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, pw)
    )
    if rows:
        user = dict(rows[0])  
        id_users = user['id_users']
        
       
        role_rows = query_fetch(conn,
            """SELECT r.nama_roles FROM user_role ur
               JOIN roles r ON r.id_roles = ur.id_roles
               WHERE ur.id_users = %s""",
            (id_users,)
        )
        
        role_name = role_rows[0]['nama_roles'] if role_rows else "Unknown"
        print(f"Selamat datang {user['nama']} (role: {role_name})")
        input("Tekan Enter untuk melanjutkan...")
        os.system('cls')
        
       
        daftar_role = {
            'Admin': 'admin',
            'Ketua kelompok tani': 'ketua',
            'Petani': 'petani'
        }
        user['roles'] = daftar_role.get(role_name, 'unknown')
        return user

    print("Login gagal!")
    input("Tekan Enter untuk melanjutkan...")
    os.system('cls')
    return None

def get_laporan_akhir_rows(conn):
    return query_fetch(conn, """
        SELECT 
            h.id_hasil_panen,
            u.nama AS nama_petani,
            COALESCE(k.nama_kecamatan, '-') AS nama_kecamatan,
            h.tanggal_panen,
            COALESCE(t.nama_tanaman, '-') AS nama_tanaman,
            h.jumlah_hasil,
            h.kualitas,
            h.luas_lahan,
            ps.jenis_pupuk,
            ps.kuota
        FROM hasil_panen h
        JOIN users u ON u.id_users = h.id_users
        LEFT JOIN kecamatan k ON k.id_users = u.id_users
        LEFT JOIN tanaman t ON t.id_hasil_panen = h.id_hasil_panen
        LEFT JOIN detail_pupuk dp ON dp.id_hasil_panen = h.id_hasil_panen
        LEFT JOIN pupuk_subsidi ps ON ps.id_pupuk_subsidi = dp.id_pupuk_subsidi
        WHERE h.status_verifikasi = 'diacc'
        ORDER BY k.nama_kecamatan, u.nama, h.tanggal_panen, h.id_hasil_panen
    """)

    

def admin_tampil_laporan_akhir(conn):
    os.system('cls')
    rows = get_laporan_akhir_rows(conn)

    print("\n=== LAPORAN AKHIR HASIL PANEN (SUDAH DI-ACC) ===\n")
    if not rows:
        print("Belum ada data hasil panen yang di-ACC ketua.")
        input("\nTekan Enter untuk kembali...")
        os.system('cls')
        return

    for r in rows:
        print(
            f"{r['id_hasil_panen']:>3} | {r['nama_petani']} | {r['tanggal_panen']} | "
            f"{r['nama_tanaman']} | {r['jumlah_hasil']} kg | "
            f"Kualitas:{r['kualitas']} | Lahan:{r['luas_lahan']}"
        )

    input("\nTekan Enter untuk melanjutkan...")

    for r in rows:
        print(f"{r['id_hasil_panen']:<4} ", f"{r['nama_petani']:<15} ", f"{r['nama_kecamatan']:<12} ", f"{str(r['tanggal_panen']):<12} "
              f"{r['nama_tanaman']:<10} ", f"{r['jumlah_hasil']:<10} ",  f"{r['luas_lahan']:<10} ", f"{r['kualitas']:<8}")

    input("\nTekan Enter untuk kembali...")
    os.system('cls')

def admin_pilih_laporan_akhir(conn):
   
    rows_kec = query_fetch(conn, """
        SELECT DISTINCT TRIM(k.nama_kecamatan) AS nama_kecamatan
        FROM kecamatan k
        JOIN users u ON u.id_users = k.id_users
        JOIN user_role ur ON ur.id_users = u.id_users
        JOIN roles r ON r.id_roles = ur.id_roles
        WHERE r.nama_roles = 'Petani'
        ORDER BY nama_kecamatan
    """)
    if not rows_kec:
        print("Belum ada kecamatan untuk petani.")
        input("Tekan Enter untuk melanjutkan...")
        return [], None, None, None

    print("\nPilih kecamatan:")
    for i, r in enumerate(rows_kec, start=1):
        print(f"{i}. {r['nama_kecamatan']}")

    index_kecamatan_yang_dipilih = -1
    while index_kecamatan_yang_dipilih < 0 or index_kecamatan_yang_dipilih >= len(rows_kec):
        index_kecamatan_yang_dipilih = input_int("Pilih nomor kecamatan: ") - 1

    nama_kec = rows_kec[index_kecamatan_yang_dipilih]['nama_kecamatan']

    row_ketua = query_fetch(conn, """
        SELECT u.nama
        FROM users u
        JOIN user_role ur ON ur.id_users = u.id_users
        JOIN roles r ON r.id_roles = ur.id_roles
        JOIN kecamatan k ON k.id_users = u.id_users
        WHERE r.nama_roles = 'Ketua kelompok tani'
          AND TRIM(k.nama_kecamatan) ILIKE TRIM(%s)
        LIMIT 1
    """, (nama_kec,))
    nama_ketua = row_ketua[0]['nama'] if row_ketua else "-"

    rows_petani = query_fetch(conn, """
        SELECT u.id_users, u.nama AS nama_petani
        FROM users u
        JOIN user_role ur ON ur.id_users = u.id_users
        JOIN roles r ON r.id_roles = ur.id_roles
        JOIN kecamatan k ON k.id_users = u.id_users
        WHERE r.nama_roles = 'Petani'
          AND TRIM(k.nama_kecamatan) ILIKE TRIM(%s)
        ORDER BY u.nama
    """, (nama_kec,))

    id_petani = None
    nama_petani = None

    if rows_petani:
        print(f"\nPilih petani di kecamatan {nama_kec}:")
        for i, data_petani  in enumerate(rows_petani, start=1):
            print(f"{i}. {data_petani['nama_petani']}")

        while True:
            pilihan = input_required("Pilih nomor petani (atau ketik 'semua'): ").strip().lower()

            if pilihan == "semua":
                id_petani = None
                nama_petani = "Semua_petani"
                break
            try:
                nomor = int(pilihan)
            except:
                print("Masukkan nomor yang Valid atau ketik 'semua'.")
                continue

            if 1 <= nomor <= len(rows_petani):
                id_petani = rows_petani[nomor - 1]['id_users']
                nama_petani = rows_petani[nomor - 1]['nama_petani']
                break
            else :
                print("Nomor petani tidak ada di daftar.")

    else:
        print(f"Tidak ada petani di kecamatan {nama_kec}.")
        input("Tekan Enter untuk melanjutkan")
        return [], nama_kec, nama_ketua, None
        
    query_laporan = """
            SELECT
                h.id_hasil_panen,
                u.nama AS nama_petani,
                h.tanggal_panen,
                h.jumlah_hasil,
                h.kualitas,
                h.luas_lahan,
                t.nama_tanaman,
                p.jenis_pupuk,
                p.kuota
            FROM hasil_panen h
            JOIN users u ON u.id_users = h.id_users
            JOIN kecamatan k ON k.id_users = u.id_users
            LEFT JOIN tanaman t ON t.id_hasil_panen = h.id_hasil_panen
            LEFT JOIN detail_pupuk d ON d.id_hasil_panen = h.id_hasil_panen
            LEFT JOIN pupuk_subsidi p ON p.id_pupuk_subsidi = d.id_pupuk_subsidi
            WHERE h.status_verifikasi = 'diacc'
              AND TRIM(k.nama_kecamatan) ILIKE TRIM(%s)
        """
    daftar_parameter = [nama_kec]

    if id_petani is not None:
        syarat_petani = "AND h.id_users = %s"
        query_laporan = "".join([query_laporan, syarat_petani])
        daftar_parameter.append(id_petani)

    penutup_query = """
        ORDER BY h.tanggal_panen DESC, h.id_hasil_panen
    """
    query_laporan = "".join([query_laporan, penutup_query])
    rows = query_fetch(conn, query_laporan, tuple(daftar_parameter))

    return rows, nama_kec, nama_ketua, nama_petani


def admin_simpan_laporan_pdf(conn, filename="laporan_hasil_panen.pdf"):
    rows = get_laporan_akhir_rows(conn)
    if not rows:
        print("Tidak ada data laporan untuk disimpan ke PDF.")
        input("Tekan Enter...")
        return

    pdf_canvas= canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    y = height - 50
    pdf_canvas.setFont("Helvetica-Bold", 14)
    pdf_canvas.drawString(50, y, "LAPORAN AKHIR HASIL PANEN (DIACC)")
    y -= 30

    pdf_canvas.setFont("Helvetica", 10)
    for r in rows:
        text = (
            f"ID:{r['id_hasil_panen']} | Nama:{r['nama_petani']} | Tgl:{r['tanggal_panen']} | "
            f"Tanaman:{r['nama_tanaman']} | Hasil:{r['jumlah_hasil']}kg | "
            f"Kualitas:{r['kualitas']} | Lahan:{r['luas_lahan']}ha"
        )
        pdf_canvas.drawString(50, y, text)
        y -= 18

        if y < 50:  
            pdf_canvas.showPage()
            y = height - 50
            pdf_canvas.setFont("Helvetica", 10)

    pdf_canvas.save()
    print(f"\n Laporan berhasil disimpan ke file: {filename}")
    input("Tekan Enter untuk melanjutkan...")

    os.system('cls')


def menu_admin(conn, user):
    while True:
        print("""
====== MENU ADMIN ======
1. Lihat semua akun
2. Lihat riwayat hasil panen (semua)
3. Lihat laporan akhir hasil panen (sudah di-ACC)
4. Simpan laporan akhir ke PDF
5. Logout
""")
        c = input_required("Pilih menu: ")

        if c == "1":
            rows = query_fetch(conn, """
                SELECT u.id_users, u.nama, u.username, r.nama_roles
                FROM users u
                JOIN user_role ur ON ur.id_users = u.id_users
                JOIN roles r ON r.id_roles = ur.id_roles
                ORDER BY r.nama_roles, u.id_users
            """)
            print("\n--- Semua Akun ---")
            for r in rows:
                print(f"{r['id_users']:>2} | {r['nama']} | {r['username']} | {r['nama_roles']}")

        elif c == "2":
            rows = query_fetch(conn, """
                SELECT h.id_hasil_panen, u.nama, h.tanggal_panen, h.jumlah_hasil,
                       h.kualitas, h.status_verifikasi, h.luas_lahan,
                       t.nama_tanaman
                FROM hasil_panen h
                JOIN users u ON u.id_users = h.id_users
                LEFT JOIN tanaman t ON t.id_hasil_panen = h.id_hasil_panen
                ORDER BY h.tanggal_panen DESC, h.id_hasil_panen
            """)
            print("\n--- Riwayat Semua Hasil Panen ---")
            for r in rows:
                print(
                    f"{r['id_hasil_panen']:>3} | {r['nama']} | {r['tanggal_panen']} | "
                    f"{r['nama_tanaman'] or '-'} | {r['jumlah_hasil']} kg | "
                    f"Kualitas:{r['kualitas']} | Lahan:{r['luas_lahan']} | "
                    f"Status:{r['status_verifikasi']}"
                )

        elif c == "3":
            os.system('cls')
            rows, nama_kec, nama_ketua, nama_petani = admin_pilih_laporan_akhir(conn)

            if not rows:
                print("\nTidak ada data laporan akhir sesuai filter.")
                input("Tekan Enter untuk melanjutkan...")
                os.system('cls')
                continue

            print("\n=== LAPORAN AKHIR HASIL PANEN (SUDAH DI-ACC) ===")
            print(f"Kecamatan : {nama_kec}")
            print(f"Ketua     : {nama_ketua}")
            if nama_petani:
                print(f"Petani    : {nama_petani}")
            else:
                print("Petani    : Semua")

            print("\nID  | Tanggal     | Petani    | Tanaman    |Hasil(kg)    | Lahan(ha)  | Kualitas   |Pupuk   | Kuota")
            print("-" * 100)
            for r in rows:
                jenis = r.get('jenis_pupuk') or "-"
                kuota_val = r.get('kuota') 
                kuota = "-" if kuota_val is None else str(kuota_val)

                print(
                    f"{r['id_hasil_panen']:>3} | {r['tanggal_panen']} | "
                    f"{r['nama_petani']:<11} | {r['nama_tanaman'] or '-':<10} | "
                    f"{r['jumlah_hasil']:>8} | {r['luas_lahan']!s:>8} | "
                    f"{r['kualitas']:<8} | {jenis:<7} | {kuota!s:>5}"
                )

            input("\nTekan Enter untuk melanjutkan...")
            os.system('cls')

        elif c == "4":
            os.system('cls')
            admin_simpan_laporan_pdf(conn)
            os.system('cls')

        elif c == "5":
            print("Logout admin...")
            break

        else:
            print("Menu tidak dikenal!")

def ketua_rekap_hasil_panen(conn, user, kecamatan_ketua):
    os.system('cls')

    if not kecamatan_ketua:
        print("Anda belum memiliki kecamatan yang terdaftar di tabel kecamatan.")
        input("Tekan Enter untuk kembali...")
        os.system('cls')
        return

    while True:
        os.system('cls')
        print("====== REKAP HASIL PANEN KETUA ======")
        print(f"Nama Ketua   : {user['nama']}")
        print(f"Kecamatan    : {kecamatan_ketua}")
        print("-------------------------------------")
        print("1. Tampilkan semua hasil panen (di-ACC)")
        print("2. Rekap per bulan")
        print("3. Rekap per tanaman")
        print("4. Kembali ke menu utama")
        pilih = input("Pilih menu rekap: ")

        if pilih == "1":
            rows = query_fetch(conn, """
                SELECT
                    h.id_hasil_panen,
                    u.nama AS nama_petani,
                    h.tanggal_panen,
                    h.jumlah_hasil,
                    h.kualitas,
                    h.luas_lahan,
                    t.nama_tanaman,
                    ps.jenis_pupuk,
                    ps.kuota
                FROM hasil_panen h
                JOIN users u ON u.id_users = h.id_users
                JOIN kecamatan k ON k.id_users = u.id_users
                LEFT JOIN tanaman t ON t.id_hasil_panen = h.id_hasil_panen
                LEFT JOIN detail_pupuk dp ON dp.id_hasil_panen = h.id_hasil_panen
                LEFT JOIN pupuk_subsidi ps ON ps.id_pupuk_subsidi = dp.id_pupuk_subsidi
                WHERE h.status_verifikasi = 'diacc'
                  AND TRIM(k.nama_kecamatan) ILIKE TRIM(%s)
                ORDER BY h.tanggal_panen DESC, h.id_hasil_panen
            """, (kecamatan_ketua,))

     
        elif pilih == "2":
            tahun = input_int("Masukkan tahun (YYYY): ")
            bulan = input_int("Masukkan bulan (1-12): ")

            rows = query_fetch(conn, """
                SELECT
                    h.id_hasil_panen,
                    u.nama AS nama_petani,
                    h.tanggal_panen,
                    h.jumlah_hasil,
                    h.kualitas,
                    h.luas_lahan,
                    t.nama_tanaman,
                    ps.jenis_pupuk,
                    ps.kuota
                FROM hasil_panen h
                JOIN users u ON u.id_users = h.id_users
                JOIN kecamatan k ON k.id_users = u.id_users
                LEFT JOIN tanaman t ON t.id_hasil_panen = h.id_hasil_panen
                LEFT JOIN detail_pupuk dp ON dp.id_hasil_panen = h.id_hasil_panen
                LEFT JOIN pupuk_subsidi ps ON ps.id_pupuk_subsidi = dp.id_pupuk_subsidi
                WHERE h.status_verifikasi = 'diacc'
                  AND TRIM(k.nama_kecamatan) ILIKE TRIM(%s)
                  AND EXTRACT(YEAR FROM h.tanggal_panen) = %s
                  AND EXTRACT(MONTH FROM h.tanggal_panen) = %s
                ORDER BY h.tanggal_panen DESC, h.id_hasil_panen
            """, (kecamatan_ketua, tahun, bulan))

    
        elif pilih == "3":
            nama_tanaman = input("Nama tanaman (padi / jagung / cabai): ")

            rows = query_fetch(conn, """
                SELECT
                    h.id_hasil_panen,
                    u.nama AS nama_petani,
                    h.tanggal_panen,
                    h.jumlah_hasil,
                    h.kualitas,
                    h.luas_lahan,
                    t.nama_tanaman,
                    ps.jenis_pupuk,
                    ps.kuota
                FROM hasil_panen h
                JOIN users u ON u.id_users = h.id_users
                JOIN kecamatan k ON k.id_users = u.id_users
                LEFT JOIN tanaman t ON t.id_hasil_panen = h.id_hasil_panen
                LEFT JOIN detail_pupuk dp ON dp.id_hasil_panen = h.id_hasil_panen
                LEFT JOIN pupuk_subsidi ps ON ps.id_pupuk_subsidi = dp.id_pupuk_subsidi
                WHERE h.status_verifikasi = 'diacc'
                  AND TRIM(k.nama_kecamatan) ILIKE TRIM(%s)
                  AND t.nama_tanaman ILIKE %s
                ORDER BY h.tanggal_panen DESC, h.id_hasil_panen
            """, (kecamatan_ketua, f"%{nama_tanaman}%"))

        elif pilih == "4":
            os.system('cls')
            return

        else:
            print("Menu tidak dikenal!")
            input("Tekan Enter untuk melanjutkan...")
            continue
        os.system('cls')


        print("====== LAPORAN AKHIR HASIL PANEN (DI-ACC) ======")
        print(f"Kecamatan : {kecamatan_ketua}")
        print("-----------------------------------------------")

        if not rows:
            print("Tidak ada data sesuai filter.")
            input("Tekan Enter untuk kembali...")
            continue

        print("ID | Tanggal     | Petani       | Tanaman    | Hasil(kg) | Lahan(ha) | Kualitas | Pupuk | Kuota")
        print("-" * 95)
        for r in rows:
            jenis = r['jenis_pupuk'] if r['jenis_pupuk'] is not None else "-"
            kuota = str(r['kuota']) if r['kuota'] is not None else "-"
            print(
                f"{r['id_hasil_panen']:>2} | "
                f"{r['tanggal_panen']} | "
                f"{r['nama_petani']:<11} | "
                f"{(r['nama_tanaman'] or '-'): <10} | "
                f"{r['jumlah_hasil']:>8} | "
                f"{str(r['luas_lahan']):>8} | "
                f"{r['kualitas']:<8} | "
                f"{jenis:<5} | "
                f"{kuota}"
            )

        input("\nTekan Enter untuk kembali ke menu rekap...")


def menu_ketua(conn, user):
    os.system('cls')

    row_kec = query_fetch(conn, """
        SELECT nama_kecamatan
        FROM kecamatan
        WHERE id_users = %s
        LIMIT 1
    """, (user['id_users'],))

    if row_kec:
        kecamatan_ketua = row_kec[0]['nama_kecamatan']
    else:
        kecamatan_ketua = None
    
    while True:
        print("""
    ====== MENU KETUA ======
    1. Riwayat hasil panen petani
    2. Rekap data hasil panen (kecamatan/bulan/tanaman)
    3. Verifikasi pupuk subsidi
    4. Logout
    """)
        pilih = input("Pilih menu: ")

        if pilih == "1":
            os.system('cls')
            rows = query_fetch(conn, """
                SELECT h.id_hasil_panen, u.nama, h.tanggal_panen, h.jumlah_hasil,
                       h.kualitas, h.status_verifikasi, h.luas_lahan, t.nama_tanaman
                FROM hasil_panen h
                JOIN users u ON u.id_users = h.id_users
                LEFT JOIN tanaman t ON t.id_hasil_panen = h.id_hasil_panen
                LEFT JOIN user_role ur ON ur.id_users = u.id_users
                LEFT JOIN roles r ON r.id_roles = ur.id_roles
                LEFT JOIN kecamatan k ON k.id_users = u.id_users
                WHERE r.nama_roles = 'Petani'
                    AND k.nama_kecamatan IS NOT NULL
                    AND LOWER(TRIM(k.nama_kecamatan)) = LOWER(TRIM(%s))
                ORDER BY h.tanggal_panen DESC, h.id_hasil_panen
            """,(kecamatan_ketua,))

            print("\n--- Hasil Panen Petani di Kecamatan", kecamatan_ketua, "---")
            if not rows:
                print("Belum ada data panen untuk kecamatan ini.")
            else:
                for r in rows:
                    print(
                        f"{r['id_hasil_panen']:>3} | {r['nama']} | {r['tanggal_panen']} | "
                        f"{r['nama_tanaman'] or '-'} | {r['jumlah_hasil']} kg | "
                        f"Kualitas:{r['kualitas']} | Lahan:{r['luas_lahan']} | "
                        f"Status:{r['status_verifikasi']}"
                    )
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')
        elif pilih == "2":
            os.system('cls')
            ketua_rekap_hasil_panen(conn,user,kecamatan_ketua)

        elif pilih == "3":
            os.system('cls')
            rows = query_fetch(conn, """
                SELECT h.id_hasil_panen, u.nama, h.tanggal_panen, h.jumlah_hasil,
                       h.luas_lahan, h.kualitas
                FROM hasil_panen h
                JOIN users u ON u.id_users = h.id_users
                LEFT JOIN user_role ur ON ur.id_users = u.id_users
                LEFT JOIN roles r ON r.id_roles = ur.id_roles
                LEFT JOIN kecamatan k ON k.id_users = u.id_users
                WHERE h.status_verifikasi = 'pending' 
                    AND r.nama_roles = 'Petani'
                    AND k.nama_kecamatan IS NOT NULL
                    AND LOWER(TRIM(k.nama_kecamatan)) = LOWER(TRIM(%s))
                               
                ORDER BY h.tanggal_panen, h.id_hasil_panen
                """, (kecamatan_ketua,))

            if not rows:
                print("Tidak ada hasil panen 'pending' untuk diverifikasi.")
                input("Tekan Enter untuk melanjutkan...")
                os.system('cls')
                continue

            print("\n--- Daftar hasil panen pending ---")
            for r in rows:
                print(
                    f"{r['id_hasil_panen']:>3} | {r['nama']} | {r['tanggal_panen']} | "
                    f"Panen: {r['jumlah_hasil']} kg | Lahan: {r['luas_lahan']} | "
                    f"Kualitas: {r['kualitas']}"
                )

            id_hasil = input_int("Masukkan id_hasil_panen yang ingin di-ACC: ")

            valid = [x for x in rows if x['id_hasil_panen'] == id_hasil]
            if not valid:
                print("ID hasil panen tidak valid!")
                input("Tekan Enter untuk melanjutkan...")
                os.system('cls')
                continue

            today = date.today()
            query_execute(conn, """
                UPDATE hasil_panen
                SET status_verifikasi = 'diacc',
                    tanggal_verifikasi = %s
                WHERE id_hasil_panen = %s
                """, (today, id_hasil))

            select = query_fetch(conn, """
                SELECT luas_lahan, id_users
                FROM hasil_panen
                WHERE id_hasil_panen = %s
                """, (id_hasil,))[0]

            try:
                luas_val = float(select.get('luas_lahan') or 0)
            except Exception:
                luas_val = 0.0

            kuota = int(math.ceil(luas_val/0.5) * 50)
            allowed_pupuk ={
                "urea": "Urea",
                "phonska": "Phonska"
                }

            while True:
                jenis_input = input("Jenis pupuk(Urea/Phonska):").strip().lower()
                if jenis_input in allowed_pupuk:
                    jenis_pupuk = allowed_pupuk[jenis_input]
                    break
                else:
                    print("Jenis pupuk tidak valid! Hanya boleh 'Urea' atau 'Phonska'. Silahkan ulangi. " )
            
            new_ps = query_execute(conn, """
                INSERT INTO pupuk_subsidi (jenis_pupuk, kuota, status)
                VALUES (%s, %s, %s)
                RETURNING id_pupuk_subsidi
                """, (jenis_pupuk, kuota, "Diverifikasi"), return_lastrow=True)

            id_pupuk_subsidi = new_ps['id_pupuk_subsidi']

            tgl_pakai = today

            query_execute(conn, """
                INSERT INTO detail_pupuk (id_pupuk_subsidi, id_hasil_panen, jumlah_pupuk, tanggal_penggunaan)
                VALUES (%s, %s, %s, %s)
                """, (id_pupuk_subsidi, id_hasil, kuota, tgl_pakai))
            conn.commit()

            print(f"Hasil panen {id_hasil} di-ACC. Kuota pupuk {kuota} kg (jenis {jenis_pupuk}) sudah dibuat.")
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')

        elif pilih == "4":
            print("Logout ketua...")
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')
            break

        else:
            print("Menu belum diimplementasi / tidak dikenal.")
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')
            menu_ketua(conn, user)
            

def petani_tampil_laporan_akhir(conn, user):
    os.system('cls')

    row_kec = query_fetch(conn, """
        SELECT nama_kecamatan
        FROM kecamatan
        WHERE id_users = %s
        LIMIT 1
        """, (user['id_users'],))
    if row_kec:
        nama_kec = row_kec[0]['nama_kecamatan']
    else:
        nama_kec = "-"

    row_ketua = query_fetch(conn, """
        SELECT u.nama
        FROM users u
        JOIN user_role ur ON ur.id_users = u.id_users
        JOIN roles r ON r.id_roles = ur.id_roles
        JOIN kecamatan k ON k.id_users = u.id_users
        WHERE r.nama_roles = 'Ketua kelompok tani'
          AND TRIM(LOWER(k.nama_kecamatan)) = TRIM(LOWER(%s))
        LIMIT 1
        """, (nama_kec,))
    nama_ketua = row_ketua[0]['nama'] if row_ketua else "-"

    rows = query_fetch(conn, """
        SELECT
            h.id_hasil_panen,
            h.tanggal_panen,
            t.nama_tanaman,
            h.jumlah_hasil,
            h.luas_lahan,
            h.kualitas,
            ps.jenis_pupuk,
            ps.kuota
        FROM hasil_panen h
        JOIN tanaman t ON t.id_hasil_panen = h.id_hasil_panen
        LEFT JOIN detail_pupuk dp ON dp.id_hasil_panen = h.id_hasil_panen
        LEFT JOIN pupuk_subsidi ps ON ps.id_pupuk_subsidi = dp.id_pupuk_subsidi
        WHERE h.status_verifikasi = 'diacc'
            AND h.id_users = %s
        ORDER BY h.tanggal_panen DESC
        """, (user['id_users'],))


    print("\n=== LAPORAN AKHIR HASIL PANEN (DIACC) ===\n")
    print(f"Nama Petani : {user['nama']}")
    print(f"Kecamatan   : {nama_kec}")
    print(f"Ketua KT    : {nama_ketua}")
    print("-" * 70)
    print("ID  Tanggal    Tanaman   Hasil(kg)  Lahan(ha)  Kualitas  Pupuk  Kuota  ")
    print("-" * 70)

    if not rows:
        print("Belum ada hasil panen yang di-ACC.")
        input("\nTekan Enter untuk kembali...")
        os.system('cls')
        return

    for r in rows:
        print(f"{r['id_hasil_panen']:>2}  {r['tanggal_panen']}  {r['nama_tanaman']:<8}  "
              f"{r['jumlah_hasil']:>5}      {r['luas_lahan']!s:>6}    {r['kualitas']:<6}  "
              f"{(r['jenis_pupuk'] or '-'):<6}  {str(r['kuota'] or '-'):>4}")

    input("\nTekan Enter untuk kembali...")
    os.system('cls')


def menu_petani(conn, user):
    os.system('cls')
    id_users = user['id_users']

    while True:
        print("""
    ====== MENU PETANI ====== 
               
    1. Input hasil panen
    2. Riwayat hasil panen
    3. Cek status pupuk subsidi
    4. Laporan akhir hasil panen (di-ACC)
    5. Logout
    """)
        pilih = input_required("Pilih menu: ")
        

        if pilih == "1":
            nama_tanaman = input("Nama tanaman : ")
            tanggal_panen = input_required("Tanggal panen (YYYY-MM-DD): ")
            jumlah_hasil = input_required("Jumlah hasil panen (kg): ")
            kualitas = input("Kualitas (Baik/Buruk): ")

        
            luas_lahan = input("Luas lahan (ha, 0.5 sampai 2): ")

            hasil_panen = query_execute(conn, """
                INSERT INTO hasil_panen
                (id_users, tanggal_panen, jumlah_hasil, kualitas, status_verifikasi, tanggal_verifikasi, luas_lahan)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_hasil_panen
                """, (id_users, tanggal_panen, jumlah_hasil, kualitas, "pending", None, luas_lahan), return_lastrow=True)
            conn.commit()

            id_hasil_panen = hasil_panen['id_hasil_panen']

            query_execute(conn, """
                INSERT INTO tanaman (id_hasil_panen, nama_tanaman, is_deleted)
                VALUES (%s, %s, %s)
                """, (id_hasil_panen, nama_tanaman, False))
            conn.commit()

            print(" Data hasil panen dan tanaman berhasil disimpan (status: pending).")
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')

        elif pilih == "2":
            rows = query_fetch(conn, """
                SELECT h.id_hasil_panen, h.tanggal_panen, h.jumlah_hasil,
                       h.kualitas, h.status_verifikasi, h.luas_lahan,
                       t.nama_tanaman
                FROM hasil_panen h
                LEFT JOIN tanaman t ON t.id_hasil_panen = h.id_hasil_panen
                WHERE h.id_users = %s
                ORDER BY h.tanggal_panen DESC, h.id_hasil_panen
                """, (id_users,))

            print("\n--- Riwayat Hasil Panen Anda ---")
            if not rows:
                print("Belum ada data panen.")
            else:
                for r in rows:
                    print(
                        f"{r['id_hasil_panen']:>3} | {r['tanggal_panen']} | "
                        f"{r['nama_tanaman'] or '-'} | {r['jumlah_hasil']} kg | "
                        f"Kualitas:{r['kualitas']} | Lahan:{r['luas_lahan']} | "
                        f"Status:{r['status_verifikasi']}"
                    )

            input("\nTekan Enter untuk melanjutkan...")
            os.system('cls')

        elif pilih == "3":
            os.system('cls')
            rows = query_fetch(conn, """
                SELECT ps.id_pupuk_subsidi, ps.jenis_pupuk, ps.kuota, ps.status,
                       dp.tanggal_penggunaan, dp.jumlah_pupuk,
                       h.id_hasil_panen
                FROM pupuk_subsidi ps
                JOIN detail_pupuk dp ON ps.id_pupuk_subsidi = dp.id_pupuk_subsidi
                JOIN hasil_panen h ON dp.id_hasil_panen = h.id_hasil_panen
                WHERE h.id_users = %s
                ORDER BY ps.id_pupuk_subsidi
                """, (user['id_users'],))

            print("\n====== STATUS PUPUK SUBSIDI ======\n")
            print(f"{'ID':<4} {'Jenis':<10} {'Kuota(kg)':<12} {'Dipakai(kg)':<12} {'Tgl Pakai':<12} {'Status':<12}")
            print("-" * 70)
            if not rows:
                print("Belum ada data pupuk subsidi.")
                input("Tekan Enter untuk melanjutkan..")
                os.system('cls')
            else:
                for r in rows:
                    print(f"{r['id_pupuk_subsidi']:<4} {r['jenis_pupuk']:<10} "
                          f"{r['kuota']:<12} {r['jumlah_pupuk']:<12} "
                          f"{r['tanggal_penggunaan']:<12} {r['status']:<12}")
                input("\nTekan Enter untuk melanjutkan...")
                os.system('cls')

        elif pilih == "4":
           petani_tampil_laporan_akhir(conn,user)

        elif pilih == "5":
            print("Logout petani..")
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')
            break
        else:
            print("Menu tidak dikenal!")
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')

print (""""

███╗   ███╗███████╗███╗   ██╗██╗   ██╗     █████╗ ██╗    ██╗ █████╗ ██╗     
████╗ ████║██╔════╝████╗  ██║██║   ██║    ██╔══██╗██║    ██║██╔══██╗██║     
██╔████╔██║█████╗  ██╔██╗ ██║██║   ██║    ███████║██║ █╗ ██║███████║██║     
██║╚██╔╝██║██╔══╝  ██║╚██╗██║██║   ██║    ██╔══██║██║███╗██║██╔══██║██║     
██║ ╚═╝ ██║███████╗██║ ╚████║╚██████╔╝    ██║  ██║╚███╔███╔╝██║  ██║███████╗
╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝ ╚═════╝     ╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝

""")


def main():
    conn = connect()
    try:
        while True:
            print("""
    ===== SISTEM PENGELOLAAN TANI =====
    1. Register
    2. Login
    3. Exit
    """)
            pilih = input("Pilih menu: ")

            if pilih == "1":
                os.system('cls')
                register(conn) 
            elif pilih == "2":
                os.system('cls')
                user = login(conn)
                if not user:
                    os.system('cls')
                    continue

                role = (user['roles'] or "").lower()
                if role == "admin":
                    os.system('cls')
                    menu_admin(conn, user)
                elif role == "ketua":
                    os.system('cls')
                    menu_ketua(conn, user)
                elif role == "petani":
                    os.system('cls')
                    menu_petani(conn, user)
                else:
                    print("Role di tabel users tidak dikenal:", role)
                    input("Tekan Enter untuk melanjutkan...")
                    os.system('cls')
            elif pilih == "3":
                print("Keluar dari sistem...")
                input("Tekan Enter untuk melanjutkan...")
                os.system('cls')
                break
            else:
                print("Menu tidak dikenal!")
                input("Tekan Enter untuk melanjutkan...")
                os.system('cls')
    finally:
        conn.close()

if __name__ == "__main__":
    main()