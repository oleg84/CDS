from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, backref, subqueryload
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.exc import IntegrityError
import logging

engine = create_engine('sqlite:///data.sqlite')
Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'

    cardId = Column(String, primary_key = True)
    balance = Column(Integer, nullable = False)
    clientInfo = Column(String)
    coupons = relationship('Coupon', backref = 'client')

    def __repr__(self):
        return "<Client('%s', %d)>" % (self.cardId, self.balance)

class Coupon(Base):
    __tablename__ = 'coupons'
    id = Column(Integer, primary_key = True)
    clientId = Column(String, ForeignKey('clients.cardId'))
    name = Column(String, unique = True)
    isUsed = Column(Integer, nullable = False)

    def __init__(self, name, isUsed):
        self.name = name
        self.isUsed = isUsed

    def __repr__(self):
        return "<Coupon('%s', %d)>" % (self.name, self.isUsed)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

####################################
#Working with clients and coupons
####################################
def getClient(cardId):
    '''
    Tries to get a Client in the following format:
    {
      'balance':integer
      'coupons': ['name' : 'string', 'isUsed': integer(0/1)]
    }
    If there is no such client, returns None
    '''
    session = Session()
    try:
        c = session.query(Client).filter(Client.cardId == cardId).one()
    except MultipleResultsFound: #this should never happen
        logging.critical("Found multiple clients with cardId=%s", unicode(cardId))
        return None
    except NoResultFound:
        return None

    ret = {'balance' : c.balance, 'coupons' : []}

    for cp in c.coupons:
        ret['coupons'].append({'name' : cp.name, 'isUsed' : cp.isUsed})

    session.close()
    return ret


def createClient(cardId, balance, clientInfo):
    '''
    Creates a client

    Returns the same as GetClient
    '''

    session = Session()
    c = Client()
    c.cardId = cardId
    c.balance = balance
    c.clientInfo = clientInfo
    try:
        session.add(c)
        session.commit()
    except IntegrityError as e:
        logging.error("Error creating a client: %s", str(e))
        return None
    session.close()

    return {'balance' : balance, 'coupons' : []}


def updateClient(cardId, balance, coupons):
    '''
    Update the client info with the new balance and coupons information
    Coupon info is overwritten

    coupons are in the same format as described in GetClient()

    Returns False if failed, True otherwise
    '''
    session = Session()
    try:
        c = session.query(Client).options(subqueryload(Client.coupons)).filter(Client.cardId == cardId).one()
    except MultipleResultsFound: #this should never happen
        logging.critical("Found multiple clients with cardId=%s", unicode(cardId))
        return False
    except NoResultFound:
        logging.error("Did not find a client with cardId=%s", unicode(cardId))
        return False

    c.balance = balance
   
    for toDelete in c.coupons:
        session.delete(toDelete)
    session.flush()

    #add new coupons
    try:
        for coupon in coupons:
            if 'name' in coupon and 'isUsed' in coupon:
                c.coupons.append(Coupon(coupon['name'], coupon['isUsed']))
            else:
                logging.error("Wrong coupon format: %s", unicode(coupon))
    except TypeError as e:
        logging.error("Wrong coupons format: %s", unicode(coupons))
        return False

    try:
        session.commit()
    except IntegrityError as e:
        logging.error("Error updating a client: %s", str(e))
        return False

    session.close()
    return True
    
        
