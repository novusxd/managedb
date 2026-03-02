import mysql.connector
from pymongo import MongoClient
import sys
import certifi

# Konfigurasi MySQL
DB_CONFIG = {
    'host': "localhost",
    'user': "novus_adminpiket",
    'password': "Syakirah@2026!",
    'database': "novus_piketdb"
}

def init_db():
    """Memastikan tabel tersedia di MySQL."""
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
    """Menyimpan URI ke database."""
    label = input("🏷️ Beri Label (Contoh: Bot Utama / DB Backup): ")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mongo_storage (uri, label) VALUES (%s, %s)", (uri, label))
        conn.commit()
        conn.close()
        print("✅ MongoDB URI berhasil disimpan ke MySQL.")
    except Exception as e:
        print(f"❌ Gagal menyimpan: {e}")

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
        return []

def view_mongo_data(uri):
    """Membaca isi MongoDB dengan proteksi SSL dan Pagination."""
    try:
        # Menggunakan certifi untuk validasi SSL yang lebih kuat
        ca = certifi.where()
        
        print("⏳ Menghubungkan ke MongoDB...")
        client = MongoClient(
            uri, 
            serverSelectionTimeoutMS=5000,
            tlsCAFile=ca,
            tlsAllowInvalidCertificates=True # Tetap diaktifkan sebagai backup jika SSL VPS usang
        )
        
        # Paksa cek koneksi
        client.admin.command('ping')
        print("✅ Koneksi Berhasil!")
        
        dbs = client.list_database_names()
        print("\n📂 Daftar Database:")
        for i, d in enumerate(dbs): print(f"  {i+1}. {d}")
        
        db_idx = int(input("\nPilih nomor database: ")) - 1
        db = client[dbs[db_idx]]
        
        cols = db.list_collection_names()
        if not cols:
            print("⚠️ Database ini tidak memiliki koleksi.")
            return

        print("\n📑 Daftar Koleksi:")
        for i, c in enumerate(cols): print(f"  {i+1}. {c}")
        
        col_idx = int(input("\nPilih nomor koleksi: ")) - 1
        col_name = cols[col_idx]
        collection = db[col_name]

        limit = 5
        skip = 0
        while True:
            docs = list(collection.find().skip(skip).limit(limit))
            
            print(f"\n" + "="*50)
            print(f"📄 Data {col_name} | Halaman: {(skip//limit)+1}")
            print("="*50)
            
            if not docs:
                print("   (Kosong / Tidak ada data lagi)")
            else:
                for doc in docs:
                    print(f"🔹 {doc}\n")
            
            print("="*50)
            nav = input("[n] Next | [p] Prev | [q] Keluar: ").lower()
            
            if nav == 'n' and len(docs) == limit:
                skip += limit
            elif nav == 'p' and skip >= limit:
                skip -= limit
            elif nav == 'q':
                break
    except Exception as e:
        print(f"\n❌ Error MongoDB: {e}")
        print("\n💡 SOLUSI:")
        print("1. Pastikan IP VPS sudah di-whitelist (0.0.0.0/0) di MongoDB Atlas.")
        print("2. Jika password Anda mengandung '@', ganti '@' menjadi '%40' di URI.")

def main():
    init_db()
    while True:
        saved = get_saved_uris()
        print("\n🚀 MONGO-MYSQL CONNECTOR MANAGER")
        print("-" * 35)
        
        if not saved:
            print("Belum ada URI tersimpan di database.")
            uri = input("Masukkan MongoDB URI: ")
            if uri: save_uri(uri)
        else:
            print("1. Tambah MongoDB URI Baru")
            print("2. Pilih MongoDB Tersimpan")
            print("3. Keluar")
            pilihan = input("\nPilih menu (1/2/3): ")
            
            if pilihan == '1':
                uri = input("Masukkan MongoDB URI: ")
                if uri: save_uri(uri)
            elif pilihan == '2':
                print("\n📋 Daftar MongoDB di MySQL:")
                for row in saved:
                    print(f"  [{row[0]}] {row[1]}")
                
                try:
                    target_id = int(input("\nPilih ID untuk dibuka: "))
                    selected_uri = next(r[2] for r in saved if r[0] == target_id)
                    view_mongo_data(selected_uri)
                except (ValueError, StopIteration):
                    print("❌ ID tidak valid.")
            elif pilihan == '3':
                print("Sampai jumpa!")
                break

if __name__ == "__main__":
    main()
