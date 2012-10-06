from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///data.sqlite')
Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key = True)
    cardId = Column(String, unique = True)
    ballance = Column(Integer)

    def __repr__(self):
        return "<Client('%s', '%d')>" % (self.cardId, self.ballance)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def _add_clients():
    session = Session()
    c = Client()
    c.cardId = "id1"
    c.ballance = 1000
    session.add(c)
    c = Client()
    c.cardId = "id2"
    c.ballance = 10000
    session.add(c)
    session.commit()
    session.close()
