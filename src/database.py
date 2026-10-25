import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 1. تحميل المتغيرات السرية من ملف .env
load_dotenv()

# 2. الحصول على المتغيرات السرية من البيئة
def get_db_engine():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")

    # 3. إنشاء سلسلة الاتصال
    connection_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"

    # 4. إنشاء محرك SQLAlchemy
    engine = create_engine(connection_url)
    return engine

# هذا الجزء يشتغل فقط كي نشغلوا هذا الملف مباشرة لاختبار الاتصال
if __name__ == "__main__":
    engine = get_db_engine()
    with engine.connect() as connection:
        result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
        tables = [row[0] for row in result]
        print(f"Connected successfully! Tables in DB: {tables}")