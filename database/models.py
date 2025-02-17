from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DECIMAL, Enum, Text, TIMESTAMP, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from database.database import Base
from datetime import datetime


# Define the User model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)



class Cars(Base):
    __tablename__ = 'cars'

    id = Column(Integer, primary_key=True, autoincrement=True)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    min_price = Column(Float(10,2), nullable=False)
    market_price = Column(Float(10,2), nullable=False)


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    car_id = Column(Integer, ForeignKey('cars.id'), nullable=False)
    price = Column(Float(10,2), nullable=False)  # Price at which the car was ordered
    order_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="orders")
    car = relationship("Cars", backref="orders")

