from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship, backref, subqueryload
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.exc import IntegrityError
import logging
from datetime import datetime, timedelta

DB_LAST_SHOWN_ID = 1
DB_LAST_ALLOWED_ID = 2

engine = create_engine('sqlite:///data.sqlite')
Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'

    cardId = Column(String, primary_key = True)
    balance = Column(Integer, nullable = False)
    isVip = Column(Integer, nullable = False)
    isOkForBar = Column(Integer, nullable = False)
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

class BigShow(Base):
    __tablename__ = 'big_show'
    id = Column(Integer, primary_key = True)
    time = Column(DateTime)

    def __repr__(self):
        return "<lastTime %s>" % str(self.lastShown)

class Feedback(Base):
    __tablename__ = 'feedback'
    id = Column(String, primary_key = True)
    count = Column(Integer)

    def __repr__(self):
        return "<Feedback: %s, count: %d>" % (self.id, self.count)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

####################################
#Working with clients and coupons
####################################
def getClient(cardId, isBar):
    '''
    Tries to get a Client in the following format:
    {
      'balance':integer
      'isVip':integer (0/1)
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

    if isBar and not c.isOkForBar:
        return None

    ret = {'balance' : c.balance, 'isVip' : c.isVip, 'coupons' : []}

    for cp in c.coupons:
        ret['coupons'].append({'name' : cp.name, 'isUsed' : cp.isUsed})

    session.close()
    return ret


def createClient(cardId, balance, isVip, clientInfo):
    '''
    Creates a client

    Returns the same as GetClient
    '''

    session = Session()
    c = Client()
    c.cardId = cardId
    c.balance = balance
    c.isVip = isVip
    c.isOkForBar = 0
    c.clientInfo = clientInfo
    try:
        session.add(c)
        session.commit()
    except IntegrityError as e:
        logging.error("Error creating a client: %s", str(e))
        return None
    session.close()

    return {'balance' : balance, 'isVip': isVip, 'coupons' : []}


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

def allowClientToBar(cardId):
    '''
    Update the client info to allow it to visit a bar

    Returns False if failed, True otherwise
    '''

    logging.debug("DB: allow client to bar: %s", unicode(cardId))
    session = Session()
    try:
        c = session.query(Client).options(subqueryload(Client.coupons)).filter(Client.cardId == cardId).one()
    except MultipleResultsFound: #this should never happen
        logging.critical("Found multiple clients with cardId=%s", unicode(cardId))
        return False
    except NoResultFound:
        logging.error("Did not find a client with cardId=%s", unicode(cardId))
        return False

    c.isOkForBar = 1
   
    try:
        session.commit()
    except IntegrityError as e:
        logging.error("Error updating a client: %s", str(e))
        return False

    session.close()
    return True
        

####################################
#Working with BigShow
####################################

def ShouldStartBigShow(bigShowIntervalSeconds, bigShowSimplateTimeout):
    '''
    Determines if the Big show should be started.
    There are two conditions:
    1. The diff between now and last time shown is more than a bigShowIntervalSeconds
    1. The diff between now and last allowed is more than a bigShowSimplateTimeout 
    '''
    session = Session()
    lastShownTime = session.query(BigShow).filter(BigShow.id == DB_LAST_SHOWN_ID).first()
    lastAllowedTime = session.query(BigShow).filter(BigShow.id == DB_LAST_ALLOWED_ID).first()
    now = datetime.utcnow()

    lastShownDelta = timedelta.max
    lastAllowedDelta = timedelta.max
    
    if lastShownTime:
        lastShownDelta = now - lastShownTime.time
        logging.debug("Last shown time = %s", lastShownTime.time )

    if lastAllowedTime:
        lastAllowedDelta = now - lastAllowedTime.time
        logging.debug("Last allowed time = %s", lastAllowedTime.time )

    if _timedelta_total_seconds(lastShownDelta) < bigShowIntervalSeconds:
        logging.debug("lastShownDelta(%d) < bigShowIntervalSeconds(%d)", _timedelta_total_seconds(lastShownDelta), bigShowIntervalSeconds)
        return False

    if _timedelta_total_seconds(lastAllowedDelta) < bigShowSimplateTimeout:
        logging.debug("lastAllowedDelta(%d) < bigShowSimplateTimeout(%d)", _timedelta_total_seconds(lastAllowedDelta), bigShowSimplateTimeout)
        return False

    if not lastAllowedTime:
        lastAllowedTime = BigShow()
        lastAllowedTime.id = DB_LAST_ALLOWED_ID
        session.add(lastAllowedTime)
    lastAllowedTime.time = now
    session.commit()
    session.close()

    return True

def SetBigShowShown():
    '''
    Sets the last shown time to now
    '''
    session = Session()
    lastShownTime = session.query(BigShow).filter(BigShow.id == DB_LAST_SHOWN_ID).first()

    if not lastShownTime:
        lastShownTime = BigShow()
        lastShownTime.id = DB_LAST_SHOWN_ID
        session.add(lastShownTime)

    lastShownTime.time = datetime.utcnow()

    session.commit()
    session.close()

def CancelLastAllowedTime():
    '''
    Cancels the last allowed time
    '''
    session = Session()
    lastAllowedTime = session.query(BigShow).filter(BigShow.id == DB_LAST_ALLOWED_ID).first()

    if lastAllowedTime:
        session.delete(lastAllowedTime)

    session.commit()
    session.close()

def _timedelta_total_seconds(td): #this is not defined in python earlier v 2.7
    return td.days * 24 * 3600 + td.seconds #ignore microseconds

####################################
#Working with Feedback
####################################

def IncrementFeedback(answer):
    '''
    Increment a value of the feedback for a specific answer

    answer should be a string
    '''
    session = Session()
    f = session.query(Feedback).filter(Feedback.id == answer).first()

    if not f:
        f = Feedback() 
        f.id = answer
        f.count = 0
        session.add(f)

    f.count += 1

    session.commit()
    session.close()

def GetFeedbackStatistics():
    '''
    Returns a dictionary of feedback statistics in the following format:
    {
        'answer1' : count1,
        'answer2' : count2,
        ...
    }
    '''
    session = Session()
    fs = session.query(Feedback).all()
    
    ret = {}

    for f in fs:
        ret[f.id] = f.count

    session.close()

    return ret


    
