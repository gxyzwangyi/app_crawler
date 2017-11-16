#coding:utf-8

import hashlib
import binascii
# import urllib.error
import os
# import sqlalchemy.exc
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# import sqlalchemy.orm.exc
# from db import APKdata, Downloaded, Base, engine, session, Session, Errors
import os.path
import lxml.html
import urllib.request
import sys
import socket
import logging
import argparse
import time
# import MySQLdb
import sqlite3
# import http.client
import requests
from bs4 import BeautifulSoup
from optparse import OptionParser
# from wget import wget
import threading
import signal
import queue
import multiprocessing
import base64
import traceback
import pymysql
import logging
from time import sleep

from models import *
from sqlalchemy import desc
import re
import datetime

"""
DELETE FROM downloads a
WHERE a.serial_number IN (SELECT serial_number
        FROM downloads
        GROUP BY serial_number
        HAVING COUNT(*) > 1)
    AND aid NOT IN (SELECT MIN(aid)
        FROM downloads
        GROUP BY serial_number
        HAVING COUNT(*) > 1)
        """


# reload(sys)
# sys.setdefaultencoding( "utf-8" )

#(name,description,introduce,version,download_number,apk_url,serial_number,category,category_num,package_name,keywords,size,download_icon,download_url)
# [insertname,inserttime,insertintroduce,insertversion,insertdownload_number,insertapk_url,insertserial_number,insertcategory,insertcategory_num,insertpackage_name,insertkeywords,insertsize,insertdownload_icon,insertdownload_url,inserttrys]=insertlist


NUM_THREAD = 32

update_try_lock = threading.Lock()



update_flag_lock = threading.Lock()
work_queue_lock = threading.Lock()
down_queue_lock=threading.Lock()


logger = logging.getLogger('crawler')
logger.setLevel(logging.DEBUG)


print(logger.getEffectiveLevel())

fh = logging.FileHandler('crawler.log')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
from sqlalchemy.orm import scoped_session, sessionmaker

formatter=logging.Formatter("%(asctime)s %(filename)s [line:%(lineno)d] %(thread)d	%(threadName)s	%(process)d	 %(levelname)s - %(message)s","%Y-%m-%d %H:%M:%S")

fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


debug=logger.debug
info=logger.info
warn=logger.warn
error=logger.error
critical=logger.critical

class DB:

    def inserttable_url(self,insert_url):


        new = change( insert_url )
        # info(new[ "name" ])


        u = Session.query( urls ).filter(
            (urls.serial_number == new[ "serial_number" ]) & (urls.version == new[ "version" ]) ).first()

        if u != None:
            return 0
        
        

        url = urls( name = new[ "name" ], time = new[ "time" ], introduction = new[ "introduction" ],
                   version = new[ "version" ], download_number = new[ "download_number" ], apk_url = new[ "apk_url" ],
                   serial_number = new[ "serial_number" ],
                   category = new[ "category" ], category_num = new[ "category_num" ],
                   package_name = new[ "package_name" ], keywords = new[ "keywords" ], size = new[ "size" ],
                   download_icon = new[ "download_icon" ], download_url = new[ "download_url" ] )

 
    
        try:
            Session.add( url )
            Session.commit( )
        except Exception as e:
            Session.rollback( )
            Session.flush()
            error( e )
        finally:
            # info("123")
            Session.close( )


    #数据插入down表中  16
    def inserttable_down(self,insert_down,sha1):

        new = change(row2dict(insert_down))

        apk = Apk( name = new[ "name" ], time = new[ "time" ], introduction = new[ "introduction" ],
                   version = new[ "version" ], download_number = new[ "download_number" ], apk_url = new[ "apk_url" ],
                   serial_number = new[ "serial_number" ],
                   category = new[ "category" ], category_num = new[ "category_num" ],
                   package_name = new[ "package_name" ], keywords = new[ "keywords" ], size = new[ "size" ],
                   download_icon = new[ "download_icon" ], download_url = new[ "download_url" ],sha1= binascii.unhexlify(sha1))
        try:
            Session.add( apk )
            Session.commit( )
        except Exception as e:
            Session.rollback( )
            Session.flush()
            # error( e )
            self.inserttable_error( insert_down, str("Duplicate entry sha1") )
        finally:
            Session.close( )


    #数据插入error表中 17
    def inserttable_error(self,insert_error,one_error):

        new = change(row2dict(insert_error))


        err = errors( name = new[ "name" ], time = new[ "time" ], introduction = new[ "introduction" ],
                   version = new[ "version" ], download_number = new[ "download_number" ], apk_url = new[ "apk_url" ],
                   serial_number = new[ "serial_number" ],
                   category = new[ "category" ], category_num = new[ "category_num" ],
                   package_name = new[ "package_name" ], keywords = new[ "keywords" ], size = new[ "size" ],
                   download_icon = new[ "download_icon" ], download_url = new[ "download_url" ],tries=new["tries"],error=one_error )
        try:
            Session.add( err )
            Session.commit( )
        except Exception as e:
            Session.rollback( )
            Session.flush()
            error( e )
        finally:
            Session.close( )

    def inserttable_unuse(self,url):
        info(url)
        un = unused(apk_url=  url )
        try:
            Session.add( un )
            Session.commit( )
        except Exception as e:
            Session.rollback( )
            Session.flush()
            error( e )
        finally:
            Session.close( )





    def get_last_fancy_day( self):
        try:
            last = Session.query( fancy_url ).order_by( desc( fancy_url.update_date ) ).first( )
            info (last.apk_url)
            return last.update_date
        except Exception as e:
            print ("get_last_fancy_day Exception:" + str( e ))
            return ""

    def inserttable_fancy(self, url,serial_number ):
        # print ( url )
        fancy = fancy_url( apk_url = url, update_date = datetime.date.today( ),serial_number =serial_number  )
        try:
            Session.add( fancy )
            Session.commit( )
        except Exception as e:
            Session.rollback( )
            Session.flush( )
            print (e)
        finally:
            Session.close( )






    def update_try(self, snumber):
        try:
            Session.query( urls ).filter( urls.serial_number == snumber ).update( { urls.tries: urls.tries + 1 } )
            Session.commit( )
        except Exception as e:
            Session.rollback( )
            Session.flush()
            error("update try Exception:"+str(e))

        finally:
            Session.close( )


    def fetch_max(self):
        try:
            max_url = Session.query( urls ).order_by( desc( urls.serial_number ) ).first( )
            max_apk = Session.query( Apk ).order_by( desc( Apk.serial_number ) ).first()
            max_error = Session.query( errors ).order_by( desc( errors.serial_number ) ).first()

            url= int( 0 if max_url is None else max_url.serial_number )
            apk = int( 0 if max_apk is None else max_apk.serial_number )
            err = int( 0 if max_error is None else max_error.serial_number )
            info(url)
            m = max( url,apk,err )


            return m+1

        except Exception as e:
            Session.rollback( )
            Session.flush()
            error("fetch_max Exception:"+str(e))
            error( str( traceback.print_exc( ) ) )
            return 0


    def fetch_ten( self ):
        try:
            ten = Session.query( urls ).filter_by( flag = 0 ).limit(32).all()
            info(len(ten))
            return ten
        except Exception as e:
            Session.rollback( )
            Session.flush()
            error("fetch_ten Exception:"+str(e))
            return ""


    def update_ten_one( self,snumberlist ):
        try:
            l = snumberlist
            info( l )
            Session.query( urls ).filter( urls.serial_number.in_(l) ).update( { urls.flag: 1 },synchronize_session=False )
            Session.commit( )
        except Exception as e:
            Session.rollback( )
            Session.flush()
            error( "update_ten_one Exception:" + str( e ) )
            return ""
        finally:
            Session.close( )


    def update_ten_zero( self,snumber ):

        try:
            Session.query( urls ).filter( urls.serial_number == snumber ).update( { urls.flag: 0 } )
            Session.commit( )
        except Exception as e:
            Session.rollback( )
            Session.flush()
            error( "update_ten_zero Exception:" + str( e ) )
            return ""
        finally:
            Session.close( )


    def delete_downloaded(self,snumber):
        try:
            Session.query( urls ).filter( urls.serial_number == snumber ).delete(  )
            Session.commit( )

        except Exception as e:
            Session.rollback( )
            Session.flush()
            error("delete Exception:"+str(e))
            return ""
        finally:
            Session.close( )




class Url(threading.Thread):
    def __init__(self, db,work_queue):
        threading.Thread.__init__(self)
        self.db = db
        self.work_queue = work_queue
        self.exit_event = threading.Event()
        self.current_file_size = 0
        self.file_size = 0
    def exit(self):
        error("%s: asked to exit." % self.getName())
        self.exit_event.set()
        self.join()
        return self.report()
    def report(self):
        if self.file_size == 0:
            return 0
        return float(self.current_file_size) / self.file_size

    def get_apk_content(self,url):
        info("%s: crawler_apk %s " % (self.getName(), url))
        try:
            r=requests.get(url,allow_redirects=False)
            soup= BeautifulSoup(r.content,"html.parser",from_encoding='GB18030')
        # print(soup.select(".area-download")[0].a["href"]==None)

            is_real=soup.title.string==None or soup.select(".area-download")[0].a["href"]==None or soup.select(".area-download")[0].a["href"]==''
        except:
            self.db.inserttable_unuse(url)
            return 0

        if is_real:
            return 0
        else:
            try:
                result = { }
                name = soup.select(".content-right")[0].h1.text.replace("'","")
                download_time = int(time.time())
                introduction=soup.select(".introduction")[0].select('.brief-long')[0].text.replace("'","")
                version= soup.select(".content-right")[0].select(".detail")[0].select(".version")[0].text[4::]
                download_number=soup.select(".content-right")[0].select(".detail")[0].select(".download-num")[0].text[6::]
                apk_url=soup.find_all(rel="canonical")[0].get("href")
                serial_number=apk_url[(lambda x:x.index('e/'))(apk_url)+2:-5]
                category=soup.select(".app-nav")[0].select(".nav")[0].find_all('a')[-1].text
                category_num=soup.select(".app-nav")[0].select(".nav")[0].find_all('a')[-1].get("href")
                package_name=soup.select(".one-setup-btn")[0].get("data_package")
                keywords=soup.select("meta")[1].get("content").replace("'","")
                size=soup.select(".one-setup-btn")[0].get("data_size")
                download_icon=soup.select(".one-setup-btn")[0].get("data_icon")
                download_url=soup.select(".area-download")[0].a["href"]
                tries=0




                result[ "name" ] = name
                result[ "time" ] = download_time
                result[ "introduction" ] = introduction
                result[ "version" ] = version
                result[ "download_number" ] = download_number
                result[ "apk_url" ] = apk_url
                result[ "serial_number" ] = serial_number
                result[ "category" ] = category
                result[ "category_num" ] = category_num
                result[ "package_name" ] = package_name
                result[ "keywords" ] = keywords
                result[ "size" ] = size
                result[ "download_icon" ] = download_icon
                result[ "download_url" ] = download_url
                result[ "tries" ] = tries


            except Exception as ex:
                # error("get_apk_content Exception:"+str(ex)+url)
                error(str(traceback.print_exc()))
                return 0

            # info(str(result))
            return result

    def run(self):
        while not self.exit_event.isSet():
            # info(  self.work_queue.qsize() )
            work_queue_lock.acquire()
            if not self.work_queue.empty():
                url = self.work_queue.get()
                work_queue_lock.release()
                try:
                    self.insert_db(url)
                except Exception as e:
                    error(e)
                    pass
            else:
                # info("empty")
                work_queue_lock.release()
        error("%s: received exit event." % self.getName())

    def insert_db(self,url):
        apk_content_list=self.get_apk_content(url)
        # info(apk_content_list)
        if apk_content_list!=0 and apk_content_list!={}:
            self.db.inserttable_url(apk_content_list)



class NotAndroiderror(RuntimeError):
    def __init__(self, arg):
        self.args = arg


class Downloader(threading.Thread):
    def __init__(self,db, down_queue ,output_dir):
        threading.Thread.__init__(self)
        self.exit_event = threading.Event()
        self.db = db
        self.down_queue = down_queue
        self.proxies = None
        #self.proxies = {"http": ""}
        self.output_dir = output_dir
        self.current_file_size = 0
        self.file_size = 0
        self.new_output_path=""

    def exit(self):
        print("%s: asked to exit." % self.getName())
        self.exit_event.set()
        self.join()
        return self.report()

    def report(self):
        if self.file_size == 0:
            return 0
        return float(self.current_file_size) / self.file_size

    def run(self):
        while not self.exit_event.isSet():
            down_queue_lock.acquire()
            if not self.down_queue.empty():
                now_queue=self.down_queue.get()

                # print(now_queue)

                self.url =  now_queue.download_url
                self.code = now_queue.serial_number
                self.trys = now_queue.tries

                down_queue_lock.release()
                try:

                    temp=self.download()


                    # temp=self.temp_output_path

                    sha1 = self.SHA1FileWithName( temp )
                    self.save(sha1)


                    #去掉id和trys flag,加上sha1
                    self.db.inserttable_down(now_queue,sha1)
                    self.db.delete_downloaded(self.code)


                except Exception as e:
                    #trys大于2  去掉 flag放到error里
                    if self.trys > 1:
                        one_error=str( e ).replace( "'", "" )
                        self.db.inserttable_error( now_queue,one_error )
                        self.db.delete_downloaded( self.code )
                    else:
                        self.db.update_try(self.code )
                        self.db.update_ten_zero(self.code)

                    # info("run Exception:"+str(e))
                    # error(str(traceback.print_exc()))

            else:
                down_queue_lock.release()
        print("%s: received exit event." % self.getName())


    def download(self):
        info("%s: downloading %s is %s" % (self.getName(), self.url,self.code))

        self.current_file_size = 0
        self.file_size = 0
        proxy_handler = urllib.request.ProxyHandler()
        if (self.proxies):
            proxy_handler = urllib.request.proxyHandler(self.proxies)
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [
            ('User-Agent', r"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 "
                "(KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11"),
            ('Referer', self.url)
        ]
        urllib.request.install_opener(opener)
        opening = urllib.request.urlopen(self.url,timeout=5)
        meta = opening.info()
        if "android" in meta.get_all("Content-Type")[0]:
            self.file_size = int(meta.get_all("Content-Length")[0])
            temp_file_name = "temp%s.apk" % (self.code)
            temp_dir = self.output_dir + os.sep + "temp"
            self.temp_output_path = temp_dir + os.sep + temp_file_name
            temp=temp_dir + os.sep + temp_file_name
            info("temp:"+self.temp_output_path)
            os.makedirs( os.path.dirname( self.temp_output_path ), exist_ok = True )
            with open(self.temp_output_path, 'wb+') as fil:
                block_size = 64 *1024
                while True:
                    buf = opening.read(block_size)
                    self.current_file_size += len(buf)
                    fil.write(buf)
                    if not buf:
                        return temp


        else:
            raise NotAndroiderror( "n" )





    def save(self,sha1):
        try:
            new_output_path = self.output_dir + os.sep + sha1[0:2] + os.sep+  sha1 + ".apk"
            if os.path.isfile(new_output_path):
                os.remove(new_output_path)
            # print(os.path.isfile(self.temp_output_path))
            os.makedirs( os.path.dirname( new_output_path ), exist_ok = True )
            os.rename(self.temp_output_path, new_output_path)
            self.new_output_path = new_output_path
            info("%s: %s.apk is completed." % (self.getName(), self.code))
        except Exception as e:
            error("save Exception:"+str(e))
            error( str(traceback.print_exc()  ))



    def SHA1FileWithName(self,fineName, block_size=64 * 1024):
        try:
            with open(fineName, 'rb') as f:
                sha1 = hashlib.sha1()
                while True:
                    data = f.read(block_size)
                    if not data:
                        break
                    sha1.update(data)
                # retsha1 = base64.b64encode(sha1.digest())
                retsha1 = sha1.hexdigest()
                return retsha1
        except Exception as e:
            error("sha1 Exception:"+str(e))
            error( str( traceback.print_exc()))




class Monitor(threading.Thread):
    def __init__(self, threads):
        threading.Thread.__init__(self)
        self.threads = threads
        self.exit_event = threading.Event()
    def exit(self):
        self.exit_event.set()
        self.join()
    def run(self):
        while not self.exit_event.isSet():
            for t in self.threads:
                if t.report() == 0:
                    pass
                else:
                    debug("哪个"+str(t))
                    print("%3.0f%%" % (t.report()*100)),
            time.sleep(1)

class Watcher:
    def __init__(self):
        self.child = os.fork()
        if self.child == 0:
            return
        else:
            self.watch()
    def watch(self):
        try:
            os.wait()
        except KeyboardInterrupt:
            print("KeyBoardInterrupt")
            self.kill()
        sys.exit()
    def kill(self):
        try:
            os.kill(self.child, signal.SIGKILL)
        except OSError:
            pass



def generate_url(start,work_queue):
    gap=500
    end=start+gap
    for number in range(start,end):
        url="http://shouji.baidu.com/software/"+str(number)+".html"
        info(url)
        work_queue.put(url)
    return end


def generate_fancy_url(work_queue,the_db):
    url=[]
    url1=["http://shouji.baidu.com/rank/features/","http://shouji.baidu.com/rank/features/artistic/"]
    url2=["http://shouji.baidu.com/discovery/top/","http://shouji.baidu.com/discovery/pop/","http://shouji.baidu.com/discovery/hot/","http://shouji.baidu.com/discovery/new/","http://shouji.baidu.com/rank/features/developer/"]
    url4=["http://shouji.baidu.com/rank/up/"]
    url5=["http://shouji.baidu.com/rank/top/"]
    url11=["http://shouji.baidu.com/rank/top/software/","http://shouji.baidu.com/rank/features/classic/"]


    for u in url1:
        url.append(u+"list_"+str(1)+".html")

    for u in url2:
        for i in range(2):
            url.append(u+"list_"+str(i+1)+".html")

    for u in url4:
        for i in range(4):
            url.append(u+"list_"+str(i+1)+".html")

    for u in url5:
        for i in range(5):
            url.append(u+"list_"+str(i+1)+".html")

    for u in url11:
        for i in range(11):
            url.append(u+"list_"+str(i+1)+".html")



    result_url=[]

    for u in url:
        r = requests.get( u, allow_redirects = False )
        # 获取<a href></a>中的URL
        res_url = r"(?<=href=\").+?(?=\")"
        link = re.findall( res_url, r.content.decode('utf-8'), re.I | re.S | re.M )
        for url in link:
            if "/software/" in url and "html" in url and "http" not in url:
                result="https://shouji.baidu.com"+url
                result_url.append(result)
                index1=url.index(".")
                serial_number=int(url[10:index1])
                the_db.inserttable_fancy(result,serial_number)
                work_queue.put( result )












def put_url(ten,down_queue):
    for apk in ten:
        # print(apk)
        down_queue.put(apk)
    return 1





def url_thread(the_db):

    info("url_thread")
    end = 30000000
    start=7060070

    info("This max is"+str(the_db.fetch_max( )))
    #暂时不用
    # every_start = int( the_db.fetch_max( )) if the_db.fetch_max( ) != 0 else start
    every_start=start

    info("This begin in"+str(every_start))

    threads = [ ]
    work_queue = queue.Queue( )




    initThreadsName=[]#保存初始化线程组名字


    Watcher( )
    for i in range( NUM_THREAD ):
        t = Url( the_db, work_queue )
        t.daemon = True
        t.start( )
        threads.append( t )

    # monitor_thread = Monitor( threads )
    # monitor_thread.daemon = True
    # monitor_thread.start( )

    init=threading.enumerate()#获取初始化的线程对象
    info(len(init))
    for i in init:
        initThreadsName.append(i.getName())#保存初始化线程组名字

    info(initThreadsName)
    check=threading.Thread(target=checkThread,args=(60,init))#用来检测是否有线程down并重启down线程
    check.setName('Thread:check')
    check.start()





    temp = generate_url( every_start, work_queue )
    exit_flag = 0
    pause_flag = 0
    last_flag = 0
    while exit_flag < 2:
        if work_queue.qsize( ) <50:
            if the_db.get_last_fancy_day( ) < datetime.date.today( ):
                generate_fancy_url(work_queue,the_db)
            info( temp )
            temp = generate_url( temp, work_queue )
            if temp > end:
                info(temp)
                exit_flag += 1
        else:
            exit_flag = 0
            info( work_queue.qsize( ) )
            time.sleep( 1 )
            # 以下方法无用
            # if last_flag==int(work_queue.qsize()):
            #     pause_flag=pause_flag+1
            # info( pause_flag )
            # if pause_flag>50:
            #     info( pause_flag )
            #     work_queue.queue.clear()
            #     pause_flag=0
            # info( work_queue.qsize() )
            # time.sleep( 1 )
            # last_flag=work_queue.qsize()




        # while not work_queue.empty( ):
        #     info(work_queue.qsize() )
        #     time.sleep( 1 )
    info("end")
    for t in threads:
        info( "exit" )
        t.exit( )
    # monitor_thread.exit( )




# def mysqlunpack_url(cur):
#     result=[]
#     for c in cur:
#         temp=[c['aid'],c['name'],c['time'],c['introduce'],c['version'],c['download_number'],c['apk_url'],c['serial_number'],c['category'],c['category_num'],c['package_name'],c['keywords'],c['size'],c['download_icon'],c['download_url'],c['trys'],c['flag']]
#         result.append(temp)
#     return result


def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))

    return d



def change(x):
    result={}
    try:
        name=x["name"]
        time=x["time"]
        # timeArray = time.strptime( rtime[0:-3], "%Y-%m-%d-%H-%M-%S")
        # timeStamp = int( time.mktime( timeArray ) )

        introduction=x["introduction"]
        version=x["version"]
        apk_url=x["apk_url"]
        download_number=x["download_number"]

        download_number=download_number.replace("+", "")

        if isinstance( download_number, int ):
            download_number = int( download_number )
        else:
            multiple = download_number[ -1 ]
            if multiple == "千":
                download_number = int( float( download_number[ 0:-1 ] ) * 1000 )
            elif multiple == "万":
                download_number = int( float( download_number[ 0:-1 ] ) * 10000 )
            elif multiple == "亿":
                download_number = int( float( download_number[ 0:-1 ] ) * 100000000 )
            else:
                download_number = int( download_number)

        serial_number=int(x["serial_number"])
        category=x["category"]
        category_num=x["category_num"]
        package_name=x["package_name"]
        keywords=x["keywords"]
        size=int(x["size"])
        download_icon=x["download_icon"]
        download_url=x["download_url"]


        result[ "name" ] = name
        result[ "time" ] = time
        result[ "introduction" ] = introduction
        result[ "version" ] = version
        result[ "download_number" ] = download_number
        result[ "apk_url" ] = apk_url
        result[ "serial_number" ] = serial_number
        result[ "category" ] = category
        result[ "category_num" ] = category_num
        result[ "package_name" ] = package_name
        result[ "keywords" ] = keywords
        result[ "size" ] = size
        result[ "download_icon" ] = download_icon
        result[ "download_url" ] = download_url

        if x.get("sha1")!=None:
            sha1=x.get("sha1")
            sha1=binascii.unhexlify(sha1)
            result[ "sha1" ] = sha1

        if x.get("tries")!=None:
            tries=x.get("tries")
            result[ "tries" ] = tries

        if x.get("error")!=None:
            error=x.get("error")
            result[ "error" ] = error
    except Exception as e:
        print(e)
        info( str( traceback.print_exc( ) ) )

    return result







def download_thread(the_db):


    info("download_thread")

    # ten = the_db.fetch_ten( )
    # c = [ b[ 0 ] for b in ten ]
    # info(c)
    # the_db.update_ten_one(c)


    threads = [ ]

    down_queue = queue.Queue( )

    Watcher( )
    for i in range( NUM_THREAD ):
        t = Downloader( the_db, down_queue, os.getcwd()+"/a" )
        t.daemon = True
        t.start( )
        threads.append( t )


    # monitor_thread = Monitor( threads )
    # monitor_thread.daemon = True
    # monitor_thread.start( )


    exit_flag = 0
    while exit_flag < 2:
        if down_queue.empty( ):
            ten = the_db.fetch_ten( )
            c = [ b.serial_number for b in ten ]
            info( str(c) )
            if c==[]:
                 time.sleep( 2 )
            else:
                the_db.update_ten_one( c )
                put_url(ten,down_queue)
        else:
            exit_flag = 0
            time.sleep( 1 )
        # while not down_queue.empty( ):
        #     time.sleep( 1 )
    for t in threads:
        t.exit( )
    # monitor_thread.exit( )




# def checkThread(sleeptimes,initThreadsName,the_db,work_queue):
#     for i in range(0,100800):#循环运行
#         nowThreadsName=[]#用来保存当前线程名称
#         now=threading.enumerate()#获取当前线程名
#         info( len( now ) )
#         for i in now:
#             nowThreadsName.append(i.getName())#保存当前线程名称
#         info(nowThreadsName)
#         info(initThreadsName)
#         for ip in initThreadsName:
#             if  ip in nowThreadsName:
#                 pass #当前某线程名包含在初始化线程组中，可以认为线程仍在运行
#             else:
#                 print ('-----'+ip,'stopped restart')
#                 # t=threading.Thread(target=printIP,args=(ip,))#重启线程
#                 # work_queue=[]
#                 t= Url( the_db, work_queue );
#                 t.setName(ip)#重设name
#                 t.start()
#         time.sleep(sleeptimes)#隔一段时间重新运行，检测有没有线程down
#


def checkThread(sleeptimes,initThreadsName):
    for i in range(0,100800):#循环运行
        nowThreadsName=[]#用来保存当前线程名称
        now=threading.enumerate()#获取当前线程名
        info( len( now ) )
        for i in now:
            nowThreadsName.append(i.getName())#保存当前线程名称
        info(nowThreadsName)
        # info(initThreadsName)

        for ip in initThreadsName:
            if  ip.isAlive():
                info( ip.getName()+"alive" )
                pass #当前某线程活着，可以认为线程仍在运行
            else:
                info ('-----'+ip,'stopped restart')
                # t=threading.Thread(target=printIP,args=(ip,))#重启线程
                # work_queue=[]
                # t= Url( the_db, work_queue );
                # t.setName(ip)#重设name
                ip.start()
        # info( "alive" )
        time.sleep(sleeptimes)#隔一段时间重新运行，检测有没有线程down











def main():


    info("main")


    the_db=DB()

    p1 = multiprocessing.Process(target = url_thread, args = (the_db,))
    p2 = multiprocessing.Process(target = download_thread, args = (the_db,))
    p1.start()
    p2.start()


    # p=[p1,p2]
    # while 1:
    #     for pi in p:
    #         info (pi.pid)
    #         info (pi.is_alive())
    #         if pi.is_alive()==False:
    #             pi.start()
    #     sleep(3)




if __name__ == '__main__':
    main()













