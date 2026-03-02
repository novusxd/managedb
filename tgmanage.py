import mysql.connector
from pyrogram import Client
import sys
import asyncio

# Konfigurasi MySQL sesuai koneksi.php Anda
DB_CONFIG = {
    'host': "localhost",
    'user': "novus_adminpiket",
    'password': "Syakirah@2026!",
    'database': "novus_piketdb"
}

def init_db():
    """Membuat tabel untuk menyimpan session telegram."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tg_accounts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                phone VARCHAR(50),
                session_string TEXT NOT NULL,
                name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Gagal koneksi database: {e}")
        sys.exit()

async def login_new_account():
    print("\n--- LOGIN AKUN TELEGRAM BARU ---")
    ss = input("Masukkan String Session Pyrogram: ").strip()
    
    try:
        # Mengetes validitas session
        async with Client("temp_session", session_string=ss, in_memory=True) as app:
            me = await app.get_me()
            name = f"{me.first_name} {me.last_name or ''}"
            phone = me.phone_number
            
            # Simpan ke MySQL
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tg_accounts (phone, session_string, name) VALUES (%s, %s, %s)",
                (phone, ss, name)
            )
            conn.commit()
            conn.close()
            print(f"✅ Berhasil login & simpan: {name} ({phone})")
    except Exception as e:
        print(f"❌ String Session Tidak Valid: {e}")

def get_saved_accounts():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone, session_string FROM tg_accounts")
    rows = cursor.fetchall()
    conn.close()
    return rows

async def view_official_messages(session_string):
    try:
        async with Client("temp_session", session_string=session_string, in_memory=True) as app:
            print("\n📬 Mengambil 3 pesan terakhir dari Telegram Official (+42777)...")
            # ID Telegram Official biasanya 777000
            async for message in app.get_chat_history(777000, limit=3):
                print("-" * 30)
                print(f"Tanggal: {message.date}")
                print(f"Pesan  : {message.text or '[Bukan Pesan Teks]'}")
            print("-" * 30)
    except Exception as e:
        print(f"❌ Gagal mengambil pesan: {e}")

async def main():
    init_db()
    while True:
        print("\n=== TELEGRAM SESSION MANAGER ===")
        print("1. Lanjut dengan akun tersimpan")
        print("2. Login ke akun Telegram (Tambah Baru)")
        print("3. Keluar")
        
        choice = input("Pilih menu: ")
        
        if choice == '1':
            accounts = get_saved_accounts()
            if not accounts:
                print("⚠️ Belum ada akun tersimpan.")
                continue
            
            print("\n--- DAFTAR AKUN ---")
            for acc in accounts:
                print(f"[{acc[0]}] {acc[1]} ({acc[2]})")
            
            try:
                acc_id = int(input("\nPilih ID Akun: "))
                selected = next(a for a in accounts if a[0] == acc_id)
                
                print(f"\nAkun terpilih: {selected[1]}")
                print("1. Lihat kode masuk (+42777)")
                print("2. Kembali")
                
                sub_choice = input("Pilih: ")
                if sub_choice == '1':
                    await view_official_messages(selected[3])
            except Exception:
                print("❌ Input tidak valid.")

        elif choice == '2':
            await login_new_account()
        elif choice == '3':
            break

if __name__ == "__main__":
    asyncio.run(main())
