from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings
from sqlalchemy.exc import SQLAlchemyError
from utils.logger import logger
from dotenv import load_dotenv

load_dotenv() 

class Settings(BaseSettings):
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str = "5433"  # Default port if not provided in the environment
    DB_NAME: str

    @property
    def DATABASE_URL(self):
        """Construct the full database URL from the components."""
        return f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env" 
        extra = "allow" 

settings = Settings()

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Setup SQLAlchemy Engine and SessionLocal
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)  # Using pool_pre_ping for connection checking
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Initialize the database: connect, check connection, create tables
def init_db():
    try:
        # Attempting to connect to the database
        with engine.connect() as connection:
            # If we reach this point, the connection is established and usable
            logger.info("Database connection successful.")

        # Create all tables defined in Base
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully.")

    except SQLAlchemyError as e:
        # Log any errors that occur while connecting to the database
        logger.error(f"Error connecting to the database: {str(e)}")

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
