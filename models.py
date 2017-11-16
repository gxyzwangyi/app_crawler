from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer,BINARY,SmallInteger,Date,BigInteger
import pymysql
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session


engine = create_engine('mysql+pymysql://root:appanalysis@localhost:3306/apps?charset=utf8',pool_size=100)
Model = declarative_base()
db_session = sessionmaker(bind=engine,expire_on_commit=False)

# scoped_session(db_session)

Session= scoped_session(db_session)


# db = SQLAlchemy( app )


class Apk(Model):
    __tablename__ = "apks"

    # apk path equals apk name
    sha1 = Column(BINARY(20),   primary_key = True)
    name= Column(String(500) )
    time =  Column(Integer )
    introduction = Column( String( 8000 ) )
    version = Column( String( 40 ) )
    download_number = Column( BigInteger  )
    apk_url = Column( String( 200 ) )
    serial_number = Column( Integer )
    category = Column( String( 100 ) )
    category_num = Column( String( 100 ) )
    package_name = Column( String( 200 ) )
    keywords = Column( String( 1000 ) )
    size = Column( Integer   )
    download_icon = Column( String( 1000 ) )
    download_url = Column( String( 1000 ) )

    market_id = Column(Integer,ForeignKey('markets.id'),default = 0)
    is_analyzed = Column(SmallInteger,default = 0)
    is_fancy = Column(SmallInteger,default = 0)




class Market(Model):
    __tablename__ = "markets"
    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    url = Column( String(128))
    other = Column(String(128))






class urls(Model):
    __tablename__ = "urls"

    name= Column(String(500) )
    time =  Column(Integer )
    introduction = Column( String( 8000 ) )
    version = Column( String( 40 ) , primary_key = True)
    download_number = Column( BigInteger  )
    apk_url = Column( String( 200 ) )
    serial_number = Column( Integer , primary_key = True)
    category = Column( String( 100 ) )
    category_num = Column( String( 100 ) )
    package_name = Column( String( 200 ) )
    keywords = Column( String( 1000 ) )
    size = Column( Integer   )
    download_icon = Column( String( 1000 ) )
    download_url = Column( String( 1000 ) )


    tries =Column(SmallInteger,default = 0)
    flag =Column(SmallInteger,default = 0)






class errors(Model):
    __tablename__ = "errors"



    name= Column(String(500) )
    time =  Column(Integer )
    introduction = Column( String( 8000 ) )
    version = Column( String( 40 ) , primary_key = True)
    download_number = Column( BigInteger  )
    apk_url = Column( String( 200 ) )
    serial_number = Column( Integer , primary_key = True)
    category = Column( String( 100 ) )
    category_num = Column( String( 100 ) )
    package_name = Column( String( 200 ) )
    keywords = Column( String( 1000 ) )
    size = Column( Integer   )
    download_icon = Column( String( 1000 ) )
    download_url = Column( String( 1000 ) )



    tries = Column(SmallInteger)
    error = Column(String(200))

class unused( Model ):
    __tablename__ = "unuses"
    apk_url = Column( String( 200 ), primary_key = True  )



class fancy_url( Model ):
    __tablename__ = "fancy_url"
    apk_url = Column( String( 200 ))
    update_date = Column( Date, primary_key = True )
    serial_number = Column( Integer, primary_key = True )

