import mysql.connector
from pyrogram import Client, enums
from pyrogram.raw import functions
import asyncio
import sys

# Konfigurasi MySQL sesuai koneksi.php Anda
DB_CONFIG = {
    'host': "localhost",
    'user': "novus_adminpiket",
    'password': "Syakirah@2026!",
    'database': "novus_piketdb"
}

def init_db():
    """Inisialisasi tabel di MySQL."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tg_accounts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                username VARCHAR(255),
                phone VARCHAR(50),
                name VARCHAR(255),
                session_string TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Gagal koneksi MySQL: {e}")
        sys.exit()

async def login_new():
    print("\n--- LOGIN AKUN BARU ---")
    ss = input("Masukkan String Session: ").strip()
    if not ss: return

    try:
        async with Client("temp", session_string=ss, in_memory=True) as app:
            me = await app.get_me()
            name = f"{me.first_name} {me.last_name or ''}"
            
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            query = """INSERT INTO tg_accounts (user_id, username, phone, name, session_string) 
                       VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(query, (me.id, me.username, me.phone_number, name, ss))
            conn.commit()
            conn.close()
            print(f"✅ Akun {name} berhasil disimpan!")
    except Exception as e:
        print(f"❌ Gagal: {e}")

def get_accounts():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone, username, user_id, session_string FROM tg_accounts")
    rows = cursor.fetchall()
    conn.close()
    return rows

async def manage_sessions(app):
    """Fungsi untuk melihat dan menghapus perangkat login."""
    print("\n🔍 Mengambil daftar perangkat...")
    try:
        sessions = await app.invoke(functions.account.GetAuthorizations())
        auths = sessions.authorizations
        
        print("\n--- DAFTAR PERANGKAT ---")
        for i, s in enumerate(auths):
            current = "[INI]" if s.current else ""
            print(f"{i+1}. {s.device_model} | {s.platform} | {s.ip} {current}")
            print(f"   Lokasi: {s.country} | Aplikasi: {s.app_name}")

        opt = input("\nMasukkan nomor untuk LOGOUT (atau 'b' kembali): ")
        if opt.isdigit():
            idx = int(opt) - 1
            if 0 <= idx < len(auths):
                target = auths[idx]
                if target.current:
                    print("⚠️ Tidak bisa logout perangkat ini (sedang digunakan script).")
                else:
                    confirm = input(f"Konfirmasi logout {target.device_model}? (y/n): ")
                    if confirm.lower() == 'y':
                        await app.invoke(functions.account.ResetAuthorization(hash=target.hash))
                        print("✅ Berhasil mengeluarkan perangkat tersebut.")
    except Exception as e:
        print(f"❌ Gagal akses sesi: {e}")

async def account_menu(acc_data):
    # acc_data: (id, name, phone, username, user_id, session_string)
    db_id, name, phone, username, user_id, ss = acc_data
    
    while True:
        print("\n" + "="*40)
        print(f"👤 INFORMASI AKUN")
        print(f"Nama     : {name}")
        print(f"User ID  : {user_id}")
        print(f"Username : @{username or '-'}")
        print(f"Phone    : +{phone}")
        print("="*40)
        print("1. Lihat Kode Masuk (OTP)")
        print("2. Lihat Perangkat Login")
        print("3. Kembali ke Menu Utama")
        
        pilih = input("\nPilih menu: ")
        
        if pilih in ['1', '2']:
            try:
                async with Client("viewer", session_string=ss, in_memory=True) as app:
                    if pilih == '1':
                        print("\n📬 3 Pesan Terakhir dari Telegram Official:")
                        async for msg in app.get_chat_history(777000, limit=3):
                            print(f"[{msg.date}] -> {msg.text or 'Bukan teks'}")
                    elif pilih == '2':
                        await manage_sessions(app)
            except Exception as e:
                print(f"❌ Koneksi Telegram Gagal: {e}")
        elif pilih == '3':
            break

async def main():
    init_db()
    while True:
        print("\n🚀 TG-ACCOUNT MANAGER (Pyrogram + MySQL)")
        print("1. Lanjut dengan akun tersimpan")
        print("2. Login akun Telegram (String Session)")
        print("3. Keluar")
        
        m_pilih = input("\nPilih: ")
        
        if m_pilih == '1':
            accs = get_accounts()
            if not accs:
                print("⚠️ Belum ada akun di database.")
                continue
            
            print("\n--- PILIH AKUN ---")
            for a in accs:
                print(f"[{a[0]}] {a[1]} (+{a[2]})")
            
            try:
                p_id = int(input("\nMasukkan ID Akun: "))
                target = next(a for a in accs if a[0] == p_id)
                await account_menu(target)
            except:
                print("❌ Pilihan tidak valid.")
                
        elif m_pilih == '2':
            await login_new()
        elif m_pilih == '3':
            print("Sampai jumpa!")
            break

if __name__ == "__main__":
    asyncio.run(main())
