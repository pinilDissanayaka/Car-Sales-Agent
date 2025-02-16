from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create the base class for all models
Base = declarative_base()


DATABASE_URL = "mysql://root@localhost:3306/carsale"

# Create an engine and bind it to the base
engine = create_engine(DATABASE_URL, echo=True)

# Create the tables in the database

# Create a session
Session = sessionmaker(bind=engine)

session = Session()
