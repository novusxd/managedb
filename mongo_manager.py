import mysql.connector
from pymongo import MongoClient
import sys

# Konfigurasi MySQL
DB_CONFIG = {
    'host': "localhost",
    'user': "novus_adminpiket",
    'password': "Syakirah@2026!",
    'database': "novus_piketdb"
}

def init_db():
    """Membuat tabel jika belum ada di database MySQL."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mongo_storage (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uri TEXT NOT NULL,
                label VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Gagal koneksi ke MySQL: {e}")
        sys.exit()

def save_uri(uri):
    """Menyimpan URI baru ke MySQL."""
    label = input("🏷️ Beri Label (Contoh: Bot Utama / DB Backup): ")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mongo_storage (uri, label) VALUES (%s, %s)", (uri, label))
        conn.commit()
        conn.close()
        print("✅ MongoDB URI berhasil disimpan ke MySQL.")
    except Exception as e:
        print(f"❌ Gagal menyimpan ke MySQL: {e}")

def get_saved_uris():
    """Mengambil daftar URI dari MySQL."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, label, uri FROM mongo_storage")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"❌ Gagal mengambil data: {e}")
        return []

def view_mongo_data(uri):
    """Membaca dan menampilkan isi MongoDB dengan fitur pagination."""
    try:
        # Menggunakan tlsAllowInvalidCertificates untuk melewati error SSL Handshake di VPS
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
        
        # Tes koneksi
        client.admin.command('ping')
        
        dbs = client.list_database_names()
        print("\n📂 Daftar Database:")
        for i, d in enumerate(dbs):
            print(f"  {i+1}. {d}")
        
        db_idx = int(input("\nPilih nomor database: ")) - 1
        db_name = dbs[db_idx]
        db = client[db_name]
        
        cols = db.list_collection_names()
        if not cols:
            print(f"⚠️ Database '{db_name}' kosong (tidak ada koleksi).")
            return

        print("\n📑 Daftar Koleksi:")
        for i, c in enumerate(cols):
            print(f"  {i+1}. {c}")
        
        col_idx = int(input("\nPilih nomor koleksi: ")) - 1
        col_name = cols[col_idx]
        collection = db[col_name]

        limit = 5
        skip = 0
        
        while True:
            docs = list(collection.find().skip(skip).limit(limit))
            
            print(f"\n" + "="*50)
            print(f"📄 Koleksi: {col_name} | Data {skip+1} - {skip+len(docs)}")
            print("="*50)
            
            if not docs:
                print("   (Tidak ada data untuk ditampilkan)")
            else:
                for doc in docs:
                    print(f"🔹 {doc}\n")
            
            print("="*50)
            nav = input("[n] Next | [p] Prev | [q] Kembali ke Menu: ").lower()
            
            if nav == 'n':
                if len(docs) == limit:
                    skip += limit
                else:
                    print("ℹ️ Sudah mencapai akhir data.")
            elif nav == 'p':
                if skip >= limit:
                    skip -= limit
                else:
                    print("ℹ️ Sudah di halaman pertama.")
            elif nav == 'q':
                break
                
    except Exception as e:
        print(f"\n❌ Error MongoDB: {e}")
        print("💡 Pastikan IP VPS sudah di-whitelist (0.0.0.0/0) di panel MongoDB Atlas.")

def main():
    init_db()
    while True:
        saved = get_saved_uris()
        print("\n🚀 MONGO-MYSQL CONNECTOR MANAGER")
        print("-" * 35)
        
        if not saved:
            print("Belum ada URI tersimpan di database.")
            uri = input("Masukkan MongoDB URI: ")
            if uri.strip():
                save_uri(uri)
        else:
            print("1. Tambah MongoDB URI Baru")
            print("2. Pilih MongoDB Tersimpan")
            print("3. Keluar")
            pilihan = input("\nPilih menu (1/2/3): ")
            
            if pilihan == '1':
                uri = input("Masukkan MongoDB URI: ")
                if uri.strip():
                    save_uri(uri)
            elif pilihan == '2':
                print("\n📋 Daftar MongoDB di MySQL:")
                for row in saved:
                    print(f"  [{row[0]}] {row[1]}")
                
                try:
                    target_id = int(input("\nPilih ID untuk dibuka: "))
                    # Mencari URI berdasarkan ID
                    selected_uri = next((r[2] for r in saved if r[0] == target_id), None)
                    
                    if selected_uri:
                        view_mongo_data(selected_uri)
                    else:
                        print("❌ ID tidak ditemukan.")
                except ValueError:
                    print("❌ Masukkan angka ID yang valid.")
            elif pilihan == '3':
                print("Terima kasih! Sesi berakhir.")
                break

if __name__ == "__main__":
    main()
