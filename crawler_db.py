import mysql.connector 
import logging
import sys, traceback
from mysql.connector import errorcode
from crawler_config import *

CRAWLER_DB_NAME = 'crawlerdb' 
CRAWLER_DB_USER_NAME = 'crawler' 
CRAWLER_DB_USER_PWD = '1qa2ws'

log = logging.getLogger('rss_crawler')

#####################################
# template method to run a function in a transaction on provided cnx
#####################################
def run_in_transaction(func, cnx, *args):
  try:
    # print '>> run_in_transaction: ', func, '; cnx=', cnx
    if args:
      value = func(args, cnx)
    else:
      value =func(cnx)

  except KeyboardInterrupt:
    log.warning('WARN: CTRL-C detected. Program will exit!')
    cnx.rollback() # rollback transaction if interrupted by user
    cnx.close()
    exit(1)

  except: 
    # traceback.print_exc(file=sys.stdout) # print exception to console    
    log.error('really bad. program will exit now!', exc_info=True)
    cnx.rollback()
    exit(2)
    # restart process again ??? Recursive call is ok ??? 
    # if args:
    #   run_in_transaction(func, cnx, args)
    # else:  
    #   run_in_transaction(func, cnx)

  else:
    cnx.commit() # commit transaction if all good
    # return same values as the function  
    # print '>> run_in_transaction: ', func, '; cnx=', cnx, ' COMMIT ------> RETURNS: ', value
    return value 

##########################
# get maildb connection
##########################
def get_crawlerdb_connection():
    db_config = { 
    'user': CRAWLER_DB_USER_NAME, 
    'password': CRAWLER_DB_USER_PWD, 
    'host': '127.0.0.1', 
    'database': CRAWLER_DB_NAME, 
    'raise_on_warnings': True, 
    }
    cnx = mysql.connector.connect(**db_config) 
    return cnx


######################
# check if 
######################
def urlExists(url, table, cursor):
  # log.debug('urlExists: ' + url)  
  sql = "SELECT url FROM {} WHERE hash = MD5(%s)".format(table)
  cursor.execute(sql, (url,))
  result = cursor.fetchone()
  return result

##########################
# get one url from todo
##########################
def getTodo(cursor):
  cursor.execute("SELECT url FROM todo LIMIT 1")
  result = cursor.fetchone()
  if result:
    return result[0] 
  

################
# count records
###############
def count(table, cursor):
  cursor.execute("SELECT count(1) FROM {}".format(table))
  return cursor.fetchone()[0]

##################3
# remove a url from todo list
###################
def removeTodo(url, cursor, reason):
  cursor.execute("DELETE FROM todo WHERE hash=MD5(%s)",(url,))
  addURL(url, 'crawled', cursor, reason)

####################################################
# add url to a table if does not exists already (feeds, bad_feeds, crawled, todo)
#####################################################
def addURL(url, table, cursor, reason=''):
  # print 'addURL: ', url, ' table=', table, ' reason=', reason

  if not urlExists(url, table, cursor):
    if table =='bad_feeds':
      sql = "INSERT INTO {}(url, hash, reason) VALUES(%s, MD5(%s), %s)".format(table)
      cursor.execute(sql, (url, url, reason))
    elif table == 'crawled':
      sql = "INSERT INTO {}(url, hash, status) VALUES(%s, MD5(%s), %s)".format(table)
      cursor.execute(sql, (url, url, reason))
    else:
      sql = "INSERT INTO {}(url, hash) VALUES(%s, MD5(%s))".format(table)
      cursor.execute(sql, (url, url))

############################
# 
############################
def acceptPageFromDomain(name, cursor):
  cursor.execute("SELECT page_count FROM domains where hash = MD5(%s)", (name,))
  page_count = cursor.fetchone()
  if page_count:    
    if page_count[0] < MAX_PAGES_PER_DOMAIN:
      # update database
      cursor.execute("UPDATE domains set page_count=page_count+1 where hash = MD5(%s)",(name,))
      return True
  else:
    cursor.execute("INSERT INTO domains(name, hash) VALUES(%s, MD5(%s))", (name, name))
    return True
  # by default return false  
  return False  



#################################
# creates the database 
#################################
def create_database(cnx):  

  cursor = cnx.cursor(buffered=True) 
  
  ##################################################
  def _create_db(): 
    try: 
      cursor.execute( 
        "CREATE DATABASE IF NOT EXISTS {}  DEFAULT CHARACTER SET 'utf8'".format(CRAWLER_DB_NAME))      
      log.info("OK: create database '{}'".format(CRAWLER_DB_NAME))
    except mysql.connector.Error as err: 
          if (err.errno != 1007): # 1007: Can't create database ; database exists 
            log.error("ERROR: Failed creating database: {}".format(err), exc_info=True) 
            # traceback.print_exc(file=sys.stdout)
            exit(1) 
  
  ##################################################
  def _create_db_user(): 
    try: 
      cursor.execute( 
        "GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,DROP ON {}.* TO '{}'@'localhost' IDENTIFIED by '{}'".format(CRAWLER_DB_NAME, CRAWLER_DB_USER_NAME, CRAWLER_DB_USER_PWD)) 
      cursor.execute( 
        "GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,DROP ON {}.* TO '{}'@'%' IDENTIFIED by '{}'".format(CRAWLER_DB_NAME, CRAWLER_DB_USER_NAME, CRAWLER_DB_USER_PWD)) 
      log.info("OK: create database user '{}'".format(CRAWLER_DB_USER_NAME) )
    except mysql.connector.Error as err: 
      log.error("ERROR: Failed creating user: {}".format(err), exc_info=True) 
      #traceback.print_exc(file=sys.stdout)
      exit(1) 
  
  ##################################################
  def _setup_all():
    # create database        
    _create_db()
    # create db user and privileges
    _create_db_user() 
    # create database tables if yes
    crawlerdb_cnx = get_crawlerdb_connection()
    run_in_transaction(create_database_tables, crawlerdb_cnx) 
    crawlerdb_cnx.close() 

  ##################################################  
  # check if database exists 
  cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{}'".format(CRAWLER_DB_NAME)) 
  if cursor.fetchone(): 
    if GLOBAL_CONFIG['drop_existing_database']:
      cursor.execute("DROP DATABASE {}".format(CRAWLER_DB_NAME)) 
      log.info("OK: drop database '{}'".format(CRAWLER_DB_NAME))
      _setup_all()
    else:
      log.warning("MySQL database '{}' aready exists! Existing database tables will be used for crawling!".format(CRAWLER_DB_NAME))            

  else: #database does not exist
    _setup_all()

  # make sure to close the cursor
  cursor.close()


###########################
# create db tables
###########################
def create_database_tables(cnx):  
  cursor = cnx.cursor(buffered=True) 
  # print("OK: create_database_tables: {}".format(cnx.database)) 
  TABLES = {} 

  TABLES['crawled'] = ( 
    "CREATE TABLE `crawled` (" 
      "  `pkid` bigint unsigned NOT NULL AUTO_INCREMENT," 
      "  `url` varchar(3000) NOT NULL,"
      "  `status` varchar(1000) NOT NULL,"      
      "  `hash` varchar(32) NOT NULL,"     
      "  PRIMARY KEY (`pkid`),"
      "  UNIQUE KEY `hash` (`hash`)"
      ") ENGINE=InnoDB") 

  TABLES['todo'] = ( 
    "CREATE TABLE `todo` (" 
      "  `pkid` bigint unsigned NOT NULL AUTO_INCREMENT," 
      "  `url` varchar(3000) NOT NULL," 
      "  `hash` varchar(32) NOT NULL,"     
      "  PRIMARY KEY (`pkid`),"
      "  UNIQUE KEY `hash` (`hash`)"
      ") ENGINE=InnoDB") 

  TABLES['feeds'] = ( 
    "CREATE TABLE `feeds` (" 
      "  `pkid` bigint unsigned NOT NULL AUTO_INCREMENT," 
      "  `url` varchar(3000) NOT NULL,"   
      "  `hash` varchar(32) NOT NULL,"   
      "  PRIMARY KEY (`pkid`)," 
      "  UNIQUE KEY `hash` (`hash`)" 
      ") ENGINE=InnoDB") 

  TABLES['bad_feeds'] = (
    "CREATE TABLE `bad_feeds` (" 
      "  `pkid` bigint unsigned NOT NULL AUTO_INCREMENT," 
      "  `url` varchar(3000) NOT NULL,"
      "  `reason` varchar(1000) NOT NULL DEFAULT ''," 
      "  `hash` varchar(32) NOT NULL,"      
      "  PRIMARY KEY (`pkid`)," 
      "  UNIQUE KEY `hash` (`hash`)" 
      ") ENGINE=InnoDB")  

  TABLES['domains'] = (
    "CREATE TABLE `domains` (" 
      "  `pkid` bigint unsigned NOT NULL AUTO_INCREMENT," 
      "  `name` varchar(1000) NOT NULL,"
      "  `page_count` smallint(3) NOT NULL DEFAULT 1," 
      "  `hash` varchar(32) NOT NULL,"      
      "  PRIMARY KEY (`pkid`)," 
      "  UNIQUE KEY `hash` (`hash`)" 
      ") ENGINE=InnoDB")

  ### creating tables ========= 
  for name, ddl in TABLES.iteritems(): 
    try:
      cursor.execute(ddl)           
    except mysql.connector.Error as err: 
      if err.errno == errorcode.ER_TABLE_EXISTS_ERROR: 
        log.warning("WARN: database table '{}' already exists.".format(name))
      else: 
        log.error('ERROR create_database_tables -> for table:' + name, exc_info=True)
        exit(1)
    else:
      log.info("OK: create table '{}'".format(name))
  #close cursor in the end
  cursor.close()

######################
######################
def prepare_database():
  log.debug('prepare_database')

  cnx = mysql.connector.connect(**DB_CONFIG) 
  run_in_transaction(create_database, cnx)    
  cnx.close()  
    
###########################
# if executed as a script
###########################
if __name__ == "__main__":  
  prepare_database();
  

