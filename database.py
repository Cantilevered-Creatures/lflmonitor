from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class dbconfig():

  engine = None
  db_session = None

  def __init__(self, db_path):
    self.db_path = db_path

    engine = create_engine('sqlite:///' + db_path, \
                        convert_unicode=True)

    self.engine = engine
    
    db_session = scoped_session(sessionmaker(autocommit=False,
                                          autoflush=False,
                                          bind=engine))

    self.db_session = db_session
    
    Base.query = db_session.query_property()
    import models
    Base.metadata.create_all(bind=engine)