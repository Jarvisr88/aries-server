import asyncio
import asyncpg
from dotenv import load_dotenv
import os

async def test_connection():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get connection string from environment
        db_url = os.getenv('DATABASE_URL')
        print(f"Attempting to connect to database...")
        
        # Create a connection
        conn = await asyncpg.connect(db_url)
        
        # Test the connection with a simple query
        version = await conn.fetchval('SELECT version()')
        print(f"Successfully connected to PostgreSQL!")
        print(f"PostgreSQL version: {version}")
        
        # Close the connection
        await conn.close()
        print("Connection closed successfully.")
        
    except Exception as e:
        print(f"Error connecting to the database: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())
