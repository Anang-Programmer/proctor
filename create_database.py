import pymysql

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Sesuaikan dengan password MySQL Anda
    'charset': 'utf8mb4'
}

def create_database():
    """Create database for ujian proctor system"""
    try:
        # Connect to MySQL server
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:
            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS ujian_proctor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Database 'ujian_proctor' berhasil dibuat!")
            
            # Show databases
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print("\n📋 Daftar database:")
            for db in databases:
                print(f"   - {db[0]}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Membuat database untuk Sistem Ujian Online...")
    print("=" * 50)
    
    if create_database():
        print("\n✅ Setup database selesai!")
        print("\n📝 Langkah selanjutnya:")
        print("1. Pastikan MySQL server berjalan")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Jalankan aplikasi: python app.py")
    else:
        print("\n❌ Setup database gagal!")
        print("\n🔧 Troubleshooting:")
        print("1. Pastikan MySQL server berjalan")
        print("2. Periksa username/password MySQL")
        print("3. Pastikan port 3306 tidak diblokir")