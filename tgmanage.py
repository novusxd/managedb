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
    """Memastikan tabel lengkap dengan kolom user_id dan username."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # Membuat tabel dasar jika belum ada
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
        # Cek apakah kolom user_id sudah ada (untuk migrasi tabel lama)
        cursor.execute("SHOW COLUMNS FROM tg_accounts LIKE 'user_id'")
        if not cursor.fetchone():
            print("🔄 Memperbarui struktur tabel MySQL...")
            cursor.execute("ALTER TABLE tg_accounts ADD COLUMN user_id BIGINT AFTER id")
            cursor.execute("ALTER TABLE tg_accounts ADD COLUMN username VARCHAR(255) AFTER user_id")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Gagal inisialisasi database: {e}")
        sys.exit()

async def login_new():
    print("\n--- LOGIN AKUN BARU ---")
    ss = input("Masukkan String Session: ").strip()
    if not ss: return

    try:
        # Gunakan in_memory agar tidak membuat file .session
        async with Client("temp_login", session_string=ss, in_memory=True) as app:
            me = await app.get_me()
            name = f"{me.first_name} {me.last_name or ''}".strip()
            
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Cek apakah akun sudah ada (update jika ada, insert jika baru)
            cursor.execute("SELECT id FROM tg_accounts WHERE user_id = %s", (me.id,))
            exists = cursor.fetchone()
            
            if exists:
                query = "UPDATE tg_accounts SET username=%s, phone=%s, name=%s, session_string=%s WHERE user_id=%s"
                cursor.execute(query, (me.username, me.phone_number, name, ss, me.id))
                print(f"✅ Akun {name} sudah ada, data diperbarui!")
            else:
                query = "INSERT INTO tg_accounts (user_id, username, phone, name, session_string) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(query, (me.id, me.username, me.phone_number, name, ss))
                print(f"✅ Berhasil menyimpan akun baru: {name}")
                
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"❌ Gagal login: {e}")

def get_accounts():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone, username, user_id, session_string FROM tg_accounts")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except: return []

async def manage_sessions(app):
    print("\n🔍 Mengambil daftar perangkat aktif...")
    try:
        sessions = await app.invoke(functions.account.GetAuthorizations())
        auths = sessions.authorizations
        
        print("\n--- DAFTAR PERANGKAT ---")
        for i, s in enumerate(auths):
            status = "[SEDANG DIGUNAKAN]" if s.current else f"ID: {s.hash}"
            print(f"{i+1}. {s.device_model} ({s.platform})")
            print(f"   IP: {s.ip} | Negara: {s.country} | {status}")
            print("-" * 20)

        opt = input("\nMasukkan No Perangkat untuk LOGOUT (atau 'b' kembali): ")
        if opt.isdigit():
            idx = int(opt) - 1
            if 0 <= idx < len(auths):
                target = auths[idx]
                if target.current:
                    print("⚠️ Tidak bisa logout sesi aktif ini.")
                else:
                    conf = input(f"Yakin keluarkan {target.device_model}? (y/n): ")
                    if conf.lower() == 'y':
                        await app.invoke(functions.account.ResetAuthorization(hash=target.hash))
                        print("✅ Perangkat berhasil dikeluarkan.")
    except Exception as e:
        print(f"❌ Error: {e}")

async def account_menu(acc_data):
    # Data: (id, name, phone, username, user_id, session_string)
    db_id, name, phone, username, user_id, ss = acc_data
    
    while True:
        print("\n" + "="*45)
        print(f"👤 INFO AKUN: {name}")
        print(f"📱 Nomor   : +{phone}")
        print(f"🆔 User ID : {user_id}")
        print(f"🏷️ User    : @{username or '-'}")
        print("="*45)
        print("1. Lihat Kode Masuk (+42777)")
        print("2. Lihat Perangkat Login")
        print("3. Hapus Akun dari Database")
        print("4. Kembali ke Menu Utama")
        
        choice = input("\nPilih: ")
        
        if choice in ['1', '2']:
            try:
                async with Client("viewer", session_string=ss, in_memory=True) as app:
                    if choice == '1':
                        print("\n📬 3 Pesan Terakhir dari Telegram Official:")
                        async for msg in app.get_chat_history(777000, limit=3):
                            print(f"[{msg.date}] {msg.text[:50] if msg.text else '[Media]'}")
                    elif choice == '2':
                        await manage_sessions(app)
            except Exception as e:
                print(f"❌ Gagal menyambung ke Telegram: {e}")
        elif choice == '3':
            confirm = input("Hapus akun ini dari database? (y/n): ")
            if confirm.lower() == 'y':
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tg_accounts WHERE id = %s", (db_id,))
                conn.commit()
                conn.close()
                print("🗑️ Akun dihapus dari database.")
                break
        elif choice == '4':
            break

async def main():
    init_db()
    while True:
        print("\n🚀 TG-ACCOUNT MANAGER V2")
        print("-" * 30)
        print("1. Lihat Akun Tersimpan")
        print("2. Login Akun Baru (String Session)")
        print("3. Keluar")
        
        m_choice = input("\nPilih: ")
        
        if m_choice == '1':
            accs = get_accounts()
            if not accs:
                print("⚠️ Database kosong.")
                continue
            
            print("\n--- DAFTAR AKUN ---")
            for a in accs:
                print(f"[{a[0]}] {a[1]} (+{a[2]})")
            
            try:
                p_id = int(input("\nPilih ID Akun: "))
                target = next(a for a in accs if a[0] == p_id)
                await account_menu(target)
            except:
                print("❌ ID tidak ditemukan.")
                
        elif m_choice == '2':
            await login_new()
        elif m_choice == '3':
            break

if __name__ == "__main__":
    asyncio.run(main())
