import mysql.connector
from pyrogram import Client, enums
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
    """Inisialisasi tabel jika belum ada."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tg_accounts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                phone VARCHAR(50),
                username VARCHAR(255),
                name VARCHAR(255),
                session_string TEXT NOT NULL,
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
    if not ss: return

    try:
        async with Client("temp_login", session_string=ss, in_memory=True) as app:
            me = await app.get_me()
            full_name = f"{me.first_name} {me.last_name or ''}".strip()
            
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            query = """INSERT INTO tg_accounts (user_id, phone, username, name, session_string) 
                       VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(query, (me.id, me.phone_number, me.username, full_name, ss))
            conn.commit()
            conn.close()
            print(f"✅ Berhasil menyimpan akun: {full_name}")
    except Exception as e:
        print(f"❌ Gagal Login: {e}")

def get_accounts():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tg_accounts")
    rows = cursor.fetchall()
    conn.close()
    return rows

async def manage_sessions(app):
    """Melihat dan mengeluarkan perangkat lain."""
    try:
        sessions = await app.get_authorizations()
        print("\n--- DAFTAR PERANGKAT AKTIF ---")
        for i, s in enumerate(sessions):
            current = "[INI]" if s.address == "0.0.0.0" else "" # Placeholder sederhana
            print(f"[{i}] {s.device_model} | {s.platform} | {s.ip} {current}")
        
        print("\n[d] Hapus/Logout Perangkat Lain (Terminate all others)")
        print("[b] Kembali")
        opt = input("Pilih: ").lower()
        
        if opt == 'd':
            # Pyrogram terminate_all_others
            await app.terminate_all_others()
            print("✅ Berhasil mengeluarkan semua perangkat lain!")
    except Exception as e:
        print(f"❌ Gagal mengelola sesi: {e}")

async def account_menu(acc_data):
    ss = acc_data['session_string']
    try:
        async with Client("temp_manage", session_string=ss, in_memory=True) as app:
            me = await app.get_me()
            
            while True:
                print("\n" + "="*40)
                print(f"👤 INFORMASI AKUN")
                print(f"Nama Lengkap : {me.first_name} {me.last_name or ''}")
                print(f"User ID      : {me.id}")
                print(f"Nomor Ponsel : +{me.phone_number}")
                print(f"Username     : @{me.username or 'Tidak ada'}")
                print("="*40)
                print("1. Lihat Kode Masuk (+42777)")
                print("2. Keluar Dari Device (Manage Sessions)")
                print("3. Kembali ke Menu Utama")
                
                choice = input("\nPilih menu: ")
                
                if choice == '1':
                    print("\n📩 3 Pesan Terakhir dari Telegram Official:")
                    # ID 777000 adalah Service Notifications
                    async for msg in app.get_chat_history(777000, limit=3):
                        print(f"[{msg.date}] -> {msg.text or '[Media/Bukan Teks]'}")
                
                elif choice == '2':
                    await manage_sessions(app)
                
                elif choice == '3':
                    break
    except Exception as e:
        print(f"❌ Koneksi ke Telegram gagal: {e}")

async def main():
    init_db()
    while True:
        print("\n🚀 TELEGRAM ACCOUNT MANAGER (SQL BASED)")
        print("1. Lanjut dengan akun tersimpan")
        print("2. Login ke akun Telegram (Input String)")
        print("3. Keluar")
        
        main_opt = input("\nPilih (1/2/3): ")
        
        if main_opt == '1':
            accounts = get_accounts()
            if not accounts:
                print("⚠️ Tidak ada akun di database.")
                continue
            
            print("\n📋 DAFTAR AKUN TERSIMPAN:")
            for a in accounts:
                print(f"  [{a['id']}] {a['name']} (+{a['phone']})")
            
            try:
                target_id = int(input("\nPilih ID Akun: "))
                selected = next(acc for acc in accounts if acc['id'] == target_id)
                await account_menu(selected)
            except (ValueError, StopIteration):
                print("❌ ID tidak valid.")
                
        elif main_opt == '2':
            await login_new_account()
        elif main_opt == '3':
            print("Sampai jumpa!")
            break

if __name__ == "__main__":
    asyncio.run(main())
