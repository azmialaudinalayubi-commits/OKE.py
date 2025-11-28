import psycopg2
import psycopg2.extras
import getpass
from datetime import date
import os


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

def input_required(msg):
    while True:
        v = input(msg).strip()
        if v != "":
            return v
        print("Input tidak boleh kosong!")

def input_int(msg):
    while True:
        try:
            return int(input_required(msg))
        except:
            print("Harus bilangan bulat!")

def input_luas_lahan(msg="luas lahan (ha, maksimal 2): ", max_value=2.0):
    while True:
        try:
            val = float(input_required(msg))
            if 0 < val <= max_value:
                return val
            else:
                print(f"Luas lahan tidak boleh lebih dari {max_value} ha.")
        except:
            print("Harus berupa angka desimal atau bilangan bulat!")

def get_or_create_role(conn, role_name_input):
    """
    role_name_input: 'admin' / 'ketua' / 'petani'
    Tabel roles berisi nama_roles: 'Admin', 'Ketua kelompok tani', 'Petani'
    """
    mapping = {
        "admin": "Admin",
        "ketua": "Ketua kelompok tani",
        "petani": "Petani"
    }
    nama_roles = mapping.get(role_name_input.lower(), role_name_input)

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
    username = input_required("Username : ")
    
   
    while True:
        pw = getpass.getpass("Password: ")
        pw2 = getpass.getpass("Ulangi password: ")
        if pw != pw2:
            print("Password tidak cocok!")
        else:
            break

    nomor_hp = input_required("Nomor HP : ")


    print("\nPilih role:")
    print("1. Admin")
    print("2. Ketua kelompok tani")
    print("3. Petani")

    role_map = {
        "1": "Admin",
        "2": "Ketua kelompok tani",
        "3": "Petani"
    }

    role_input = ""
    while role_input not in role_map:
        role_input = input_required("Pilih (1/2/3): ")

    nama_role = role_map[role_input]

  
    sk_path = None
    if nama_role == "Ketua kelompok tani":
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

   
    nama_kecamatan = None
    nama_alamat = None
    ketua_dipilih = None 

    if nama_role == "Petani":
        rows_kec = query_fetch(conn, """
    SELECT DISTINCT ON (LOWER(nama_kecamatan))
        nama_kecamatan
    FROM kecamatan
    WHERE nama_kecamatan IS NOT NULL
    ORDER BY LOWER(nama_kecamatan);
""")

        if rows_kec:
            print("\nPilih kecamatan:")
            for i, r in enumerate(rows_kec, start=1):
                print(f"{i}. {r['nama_kecamatan']}")
            idx = -1
            while idx < 0 or idx >= len(rows_kec):
                idx = input_int("Pilih nomor kecamatan: ") - 1
            nama_kecamatan = rows_kec[idx]['nama_kecamatan']
        else:
            print("\nBelum ada data kecamatan di tabel, isi manual.")
            nama_kecamatan = input_required("Nama kecamatan : ")

        rows_ketua = query_fetch(conn, """
            SELECT DISTINCT u.id_users, u.nama
            FROM users u
            JOIN user_role ur ON ur.id_users = u.id_users
            JOIN roles r ON r.id_roles = ur.id_roles
            WHERE r.nama_roles = 'Ketua kelompok tani'
            ORDER BY u.nama
        """)

        if rows_ketua:
            print("\nPilih Ketua Kelompok Tani:")
            for i, r in enumerate(rows_ketua, start=1):
                print(f"{i}. {r['nama']}")
            idx = -1
            while idx < 0 or idx >= len(rows_ketua):
                idx = input_int("Pilih nomor ketua: ") - 1
            ketua_dipilih = rows_ketua[idx]
            print(f"Ketua yang dipilih: {ketua_dipilih['nama']}")
            os.system('cls')
        else:
            print("\nBelum ada ketua kelompok tani terdaftar di sistem.")
            os.system('cls')
        nama_alamat = input_required("Alamat lengkap : ")

    else:
        nama_kecamatan = input_required("Nama kecamatan : ")
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

    query_execute(conn, """
        INSERT INTO kecamatan (id_users, nama_kecamatan, nama_alamat)
        VALUES (%s, %s, %s)
    """, (id_users, nama_kecamatan, nama_alamat))

    print(f"\nUser '{nama}' berhasil diregistrasi sebagai {nama_role}")
    input("Tekan Enter untuk melanjutkan...")
    os.system('cls')
    if nama_role == "Ketua kelompok tani":
        print(f"  (SK ketua disimpan di: {sk_path})")
    if nama_role == "Petani" and ketua_dipilih:
        print(f"  Terdaftar di kecamatan {nama_kecamatan}, ketua: {ketua_dipilih['nama']}")

def login(conn):
    os.system('cls')
    print("=== LOGIN ===")
    username = input_required("Username: ")
    pw = getpass.getpass("Password: ")
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
        
       
        role_map = {
            'Admin': 'admin',
            'Ketua kelompok tani': 'ketua',
            'Petani': 'petani'
        }
        user['roles'] = role_map.get(role_name, 'unknown')
        return user

    print("Login gagal!")
    input("Tekan Enter untuk melanjutkan...")
    os.system('cls')
    return None

def menu_admin(conn, user):
    while True:
        print("""
====== MENU ADMIN ======
1. Lihat semua akun
2. Lihat riwayat hasil panen
3. Logout
""")
        c = input_required("Pilih menu: ")

        if c == "1":
            rows = query_fetch(conn, """
                SELECT u.id_users, u.nama, u.username, r.nama_roles
                FROM users u
                LEFT JOIN user_role ur ON ur.id_users = u.id_users
                LEFT JOIN roles r ON r.id_roles = ur.id_roles
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
            print("Logout admin...")
            break

        else:
            print("Menu tidak dikenal!")


def menu_ketua(conn, user):
    os.system('cls')
    while True:
        print("""
====== MENU KETUA ======
1. Lihat semua hasil panen petani
2. Rekap per kecamatan
3. Rekap per bulan
4. Rekap per tanaman
5. Verifikasi pupuk subsidi
6. Logout
""")
        c = input_required("Pilih menu: ")

        if c == "1":
            os.system('cls')
            rows = query_fetch(conn, """
                SELECT h.id_hasil_panen, u.nama, h.tanggal_panen, h.jumlah_hasil,
                       h.kualitas, h.status_verifikasi, h.luas_lahan, t.nama_tanaman
                FROM hasil_panen h
                JOIN users u ON u.id_users = h.id_users
                LEFT JOIN tanaman t ON t.id_hasil_panen = h.id_hasil_panen
                LEFT JOIN user_role ur ON ur.id_users = u.id_users
                LEFT JOIN roles r ON r.id_roles = ur.id_roles
                WHERE r.nama_roles = 'Petani'
                ORDER BY h.tanggal_panen DESC, h.id_hasil_panen
            """)
            print("\n--- Hasil Panen Petani ---")
            for r in rows:
                print(
                    f"{r['id_hasil_panen']:>3} | {r['nama']} | {r['tanggal_panen']} | "
                    f"{r['nama_tanaman'] or '-'} | {r['jumlah_hasil']} kg | "
                    f"Kualitas:{r['kualitas']} | Lahan:{r['luas_lahan']} | "
                    f"Status:{r['status_verifikasi']}"
                )
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')

        elif c == "5":
            os.system('cls')
            rows = query_fetch(conn, """
                SELECT h.id_hasil_panen, u.nama, h.tanggal_panen, h.jumlah_hasil,
                       h.luas_lahan, h.kualitas
                FROM hasil_panen h
                JOIN users u ON u.id_users = h.id_users
                LEFT JOIN user_role ur ON ur.id_users = u.id_users
                LEFT JOIN roles r ON r.id_roles = ur.id_roles
                WHERE h.status_verifikasi = 'pending' AND r.nama_roles = 'Petani'
                ORDER BY h.tanggal_panen, h.id_hasil_panen
            """)

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

            hid = input_int("Masukkan id_hasil_panen yang ingin di-ACC: ")

            valid = [x for x in rows if x['id_hasil_panen'] == hid]
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
            """, (today, hid))

            hp = query_fetch(conn, """
                SELECT luas_lahan, id_users
                FROM hasil_panen
                WHERE id_hasil_panen = %s
            """, (hid,))[0]

            try:
                luas_val = float(hp.get('luas_lahan') or 0)
            except Exception:
                luas_val = 0.0

            kuota = int(luas_val * 100)
            jenis_pupuk = input_required("Jenis pupuk (misal: Urea/Phonska): ")
            
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
            """, (id_pupuk_subsidi, hid, kuota, tgl_pakai))

            print(f"Hasil panen {hid} di-ACC. Kuota pupuk {kuota} kg (jenis {jenis_pupuk}) sudah dibuat.")
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')
            conn.commit()

        elif c == "6":
            print("Logout ketua...")
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')
            break

        else:
            print("Menu belum diimplementasi / tidak dikenal.")
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')
            menu_ketua(conn, user)

def menu_petani(conn, user):
    os.system('cls')
    id_users = user['id_users']

    while True:
        print("""
====== MENU PETANI ======
1. Input hasil panen
2. Riwayat hasil panen
3. Cek status pupuk subsidi
4. Logout
""")
        c = input_required("Pilih menu: ")

        if c == "1":
            nama_tanaman = input_required("Nama tanaman : ")
            tanggal_panen = input_required("Tanggal panen (YYYY-MM-DD): ")
            jumlah_hasil = input_int("Jumlah hasil panen (kg): ")
            kualitas = input_required("Kualitas (Baik/Buruk): ")

        
            luas_lahan = input_luas_lahan("Luas lahan (ha, 0.5 sampai 2): ")

            hp = query_execute(conn, """
                INSERT INTO hasil_panen
                (id_users, tanggal_panen, jumlah_hasil, kualitas, status_verifikasi, tanggal_verifikasi, luas_lahan)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_hasil_panen
            """, (
                id_users,
                tanggal_panen,
                jumlah_hasil,
                kualitas,
                "pending",
                None,
                luas_lahan
            ), return_lastrow=True)

            id_hasil_panen = hp['id_hasil_panen']

            query_execute(conn, """
                INSERT INTO tanaman (id_hasil_panen, nama_tanaman, is_deleted)
                VALUES (%s, %s, %s)
            """, (id_hasil_panen, nama_tanaman, False))

            print(" Data hasil panen dan tanaman berhasil disimpan (status: pending).")
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')
            conn.commit()

        elif c == "2":
            os.system('cls')
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
                    input("Tekan Enter untuk melanjutkan...")
                    os.system('cls')

        elif c == "3":
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
                os.system('cls')
            else:
                for r in rows:
                    print(f"{r['id_pupuk_subsidi']:<4} {r['jenis_pupuk']:<10} "
                          f"{r['kuota']:<12} {r['jumlah_pupuk']:<12} "
                          f"{r['tanggal_penggunaan']:<12} {r['status']:<12}")
                input("\nTekan Enter untuk melanjutkan...")
                os.system('cls')

        elif c == "4":
            print("Logout petani...")
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')
            break

        else:
            print("Menu tidak dikenal!")
            input("Tekan Enter untuk melanjutkan...")
            os.system('cls')


def main():
    os.system('cls')
    conn = connect()
    try:
        while True:
            print("""
===== SISTEM PENGELOLAAN TANI =====
1. Register
2. Login
3. Exit
""")
            c = input_required("Pilih menu: ")

            if c == "1":
                os.system('cls')
                register(conn)
                

            elif c == "2":
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

            elif c == "3":
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
