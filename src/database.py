import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def get_db_engine():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")

    connection_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"

    engine = create_engine(connection_url)
    return engine

if __name__ == "__main__":
    engine = get_db_engine()
    with engine.connect() as connection:
        result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
        tables = [row[0] for row in result]
        print(f"Connected successfully! Tables in DB: {tables}")