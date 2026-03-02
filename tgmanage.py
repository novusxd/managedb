import mysql.connector
from pyrogram import Client, enums
from pyrogram.raw import functions
import asyncio
import sys
import certifi

# Konfigurasi MySQL sesuai koneksi.php Anda
DB_CONFIG = {
    'host': "localhost",
    'user': "novus_adminpiket",
    'password': "Syakirah@2026!",
    'database': "novus_piketdb"
}

def init_db():
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
        # Migrasi kolom jika belum ada
        cursor.execute("SHOW COLUMNS FROM tg_accounts LIKE 'user_id'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE tg_accounts ADD COLUMN user_id BIGINT AFTER id")
            cursor.execute("ALTER TABLE tg_accounts ADD COLUMN username VARCHAR(255) AFTER user_id")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Database Error: {e}")
        sys.exit()

async def login_new():
    print("\n--- LOGIN AKUN BARU ---")
    ss = input("Masukkan String Session: ").strip()
    if not ss: return
    try:
        async with Client("temp", session_string=ss, in_memory=True) as app:
            me = await app.get_me()
            name = f"{me.first_name} {me.last_name or ''}".strip()
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            query = "REPLACE INTO tg_accounts (user_id, username, phone, name, session_string) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (me.id, me.username, me.phone_number, name, ss))
            conn.commit()
            conn.close()
            print(f"✅ Akun {name} (ID: {me.id}) berhasil disimpan!")
    except Exception as e:
        print(f"❌ Gagal: {e}")

async def get_messages_by_user(app):
    target = input("\n🔍 Masukkan Username/ID (contoh: @username): ").strip()
    if not target: return
    try:
        print(f"⏳ Mengambil 10 pesan terakhir dari {target}...")
        count = 0
        async for msg in app.get_chat_history(target, limit=10):
            count += 1
            sender = msg.from_user.first_name if msg.from_user else "System/Bot"
            text = msg.text or msg.caption or "[Media/Non-Teks]"
            print(f"\n[{count}] {msg.date.strftime('%H:%M:%S')}")
            print(f"👤 {sender}: {text}")
        if count == 0:
            print("⚠️ Tidak ada pesan ditemukan.")
    except Exception as e:
        print(f"❌ Gagal mengambil pesan: {e}")

async def manage_sessions(app):
    try:
        sessions = await app.invoke(functions.account.GetAuthorizations())
        print("\n--- DAFTAR PERANGKAT ---")
        for i, s in enumerate(sessions.authorizations):
            curr = "[AKTIF]" if s.current else ""
            print(f"{i+1}. {s.device_model} ({s.platform}) | {s.ip} {curr}")
        
        opt = input("\nLogout nomor (b untuk kembali): ")
        if opt.isdigit():
            idx = int(opt) - 1
            target = sessions.authorizations[idx]
            if not target.current:
                await app.invoke(functions.account.ResetAuthorization(hash=target.hash))
                print("✅ Berhasil Logout.")
            else: print("⚠️ Sesi aktif tidak bisa dimatikan dari sini.")
    except Exception as e:
        print(f"❌ Error Sesi: {e}")

async def account_menu(acc_data):
    db_id, name, phone, username, user_id, ss = acc_data
    while True:
        print("\n" + "="*45)
        print(f"👤 INFORMASI AKUN: {name}")
        print(f"📱 Phone: +{phone} | ID: {user_id}")
        print("="*45)
        print("1. Lihat Kode Masuk (+42777)")
        print("2. Lihat Pesan dengan Username")
        print("3. Lihat Perangkat Login")
        print("4. Hapus Akun dari Database")
        print("5. Kembali")
        
        choice = input("\nPilih: ")
        if choice in ['1', '2', '3']:
            try:
                async with Client("viewer", session_string=ss, in_memory=True) as app:
                    if choice == '1':
                        async for m in app.get_chat_history(777000, limit=3):
                            print(f"\n[{m.date}] {m.text}")
                    elif choice == '2':
                        await get_messages_by_user(app)
                    elif choice == '3':
                        await manage_sessions(app)
            except Exception as e: print(f"❌ Koneksi Gagal: {e}")
        elif choice == '4':
            confirm = input("Hapus dari DB? (y/n): ")
            if confirm.lower() == 'y':
                conn = mysql.connector.connect(**DB_CONFIG)
                cursor = conn.cursor(); cursor.execute("DELETE FROM tg_accounts WHERE id=%s",(db_id,))
                conn.commit(); conn.close()
                break
        elif choice == '5': break

async def main():
    init_db()
    while True:
        print("\n🚀 TG-ACCOUNT MANAGER V3")
        print("1. Akun Tersimpan | 2. Login Baru | 3. Keluar")
        m = input("\nPilih: ")
        if m == '1':
            conn = mysql.connector.connect(**DB_CONFIG); cursor = conn.cursor()
            cursor.execute("SELECT id, name, phone, username, user_id, session_string FROM tg_accounts")
            accs = cursor.fetchall(); conn.close()
            if not accs: print("⚠️ Kosong."); continue
            for a in accs: print(f"[{a[0]}] {a[1]} (+{a[2]})")
            try:
                p_id = int(input("\nID Akun: "))
                target = next(a for a in accs if a[0] == p_id)
                await account_menu(target)
            except: print("❌ Invalid.")
        elif m == '2': await login_new()
        elif m == '3': break

if __name__ == "__main__":
    asyncio.run(main())
