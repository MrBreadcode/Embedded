from abc import ABC, abstractmethod
from typing import List
from hub.app.entities.processed_agent_data import ProcessedAgentData
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base  # Correct import


Base = declarative_base()


class ProcessedAgentDataEntity(Base):
    __tablename__ = 'processed_agent_data'

    id = Column(Integer, primary_key=True, index=True)
    road_state = Column(String)
    user_id = Column(Integer)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(DateTime)


class StoreGateway(ABC):
    """
    Abstract class representing the Store Gateway interface.
    All store gateway adapters must implement these methods.
    """

    @abstractmethod
    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]) -> bool:
        """
        Method to save the processed agent data in the database.
        Parameters:
            processed_agent_data_batch (List[ProcessedAgentData]): The processed agent data to be saved.
        Returns:
            bool: True if the data is successfully saved, False otherwise.
        """
        pass


class SQLAlchemyStoreGateway(StoreGateway):
    """
    SQLAlchemy implementation of the StoreGateway interface.
    """

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]) -> bool:
        """
        Method to save the processed agent data in the database using SQLAlchemy.
        Parameters:
            processed_agent_data_batch (List[ProcessedAgentData]): The processed agent data to be saved.
        Returns:
            bool: True if the data is successfully saved, False otherwise.
        """
        try:
            session = self.SessionLocal()
            entities = [ProcessedAgentDataEntity(
                road_state=data.road_state,
                user_id=data.agent_data.user_id,
                x=data.agent_data.accelerometer.x,
                y=data.agent_data.accelerometer.y,
                z=data.agent_data.accelerometer.z,
                latitude=data.agent_data.gps.latitude,
                longitude=data.agent_data.gps.longitude,
                timestamp=data.agent_data.timestamp
            ) for data in processed_agent_data_batch]
            session.add_all(entities)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            # Log the exception or handle it appropriately
            return False
        finally:
            session.close()
