import sys, traceback, getopt
import logging
from bs4 import BeautifulSoup  
from urlparse import urlparse
import requests
import crawler_db
from crawler_config import *
	
########################################
# check if URL is valid and increase page_count / domain
########################################
def isToDoURLValid(url, parentURL, cursor):
	#  'isToDoURLValid: ', url, '; parentURL=', parentURL, "; cursor = ", cursor
	if not badURL(url): 
		newURL = buildURL(url, parentURL)
		if not crawler_db.urlExists(newURL, 'crawled', cursor): # and not crawler_db.urlExists(newURL, 'todo', cursor):
			o = urlparse(newURL)
			return crawler_db.acceptPageFromDomain(o.netloc, cursor)
	return False			

########################################
# check if we can add url in todo list 
########################################
def addToDoURL(url, parentURL, cursor):
	if isToDoURLValid(url, parentURL, cursor):			
		newURL = buildURL(url, parentURL)
		crawler_db.addURL(newURL, 'todo', cursor)

########################################
#  build correct URL (UTF-8 encoded) if relative path is provided
########################################
def buildURL(url, parentURL):	
	newURL = url;
	if not parentURL:
		return newURL
	parsed_url = urlparse(url)
	if (not parsed_url.scheme and not parsed_url.netloc): # relative URL or //domain.com 
		o = urlparse(parentURL)
		if url.startswith('/'):
			newURL = o.scheme + '://' + o.netloc + url
		else:
			newURL = o.scheme + '://' + o.netloc + '/' + url	
	elif (not parsed_url.scheme and parsed_url.netloc): # //domain.com
		if url.startswith('//'):
			o = urlparse(parentURL)
			newURL = o.scheme + ':' + url	
		elif url.startswith('/'):
			newURL = o.scheme + '://' + o.netloc + url
		else:
			newURL = o.scheme + '://' + o.netloc + '/' + url
			
	return newURL.encode('utf-8')


#####################
# initialize todo list
#####################
def init_todo(cnx):
	cursor = cnx.cursor(buffered=True)
	#  'init_todo: cnx=', cnx, " ; cursor=", cursor
	for url in GLOBAL_CONFIG['start_urls']:
		crawler_db.addURL(url.encode('utf-8'), 'todo', cursor)
	cursor.close()


#######################################
# find RSS feeds  
#######################################
def crawl_feeds(cnx):
	# get an url 	
	cursor = cnx.cursor(buffered=True)	
	url = crawler_db.getTodo(cursor)
	#  'crawl_feeds: cnx=', cnx, " ; cursor=", cursor, ' --> url:', url
	if url:
		url = url.encode('utf-8')
		# check if URL is good 
		if isToDoURLValid(url, '', cursor):			
			log.info('<crawled={}, feeds={}, todo={}> -- Fetch URL: {}'.format(crawler_db.count('crawled', cursor), crawler_db.count('feeds', cursor), crawler_db.count('todo', cursor), url))
			rss_links = []
			
			try:
				resp = requests.get(url)
				if (resp.status_code == 200) and ('html' in resp.headers['content-type']):					
						soup = BeautifulSoup(resp.text)
						# rss_links = soup.select('link[type="application/rss+xml"]')
						rss_links = soup.find_all('link', type='application/rss+xml') 
						if (len(rss_links) > 0):
							log.info('	>> Found {} RSS links on page: {}'.format(len(rss_links), url))
						
						# add other links from this page in todo 	
						for link in soup.find_all('a'):
							if link.has_attr('href'):
								addToDoURL(link['href'], url, cursor)	
				else:
					reason = 'HTTP GET: ' + url + ' --> status_code:' + str(resp.status_code) + " --> Content-Type:" + resp.headers['content-type']
					log.error(reason)
					crawler_db.removeTodo(url, cursor, reason)					
			except Exception, e:
				reason = 'Unexpected ERROR:' + str(e) + " from URL: "+ url						
				log.error(reason, exc_info=True)  # traceback.print_exc(file=sys.stdout)
				crawler_db.removeTodo(url, cursor, reason)				
			else:
				# check if each feed is HTTP OK
				for lnk in rss_links:
					if not link.has_attr('href'):
						continue;
					theLink = buildURL(lnk['href'], url)	
					if not crawler_db.urlExists(theLink, 'crawled', cursor) and not crawler_db.urlExists(theLink, 'bad_feeds', cursor) and not crawler_db.urlExists(theLink, 'feeds', cursor): #check if it's a brand NEW feed
						try:   
							resp = requests.get(theLink)
							if (resp.status_code == 200):
								if ('xml' in  resp.headers['content-type']):
									log.info('	RSS OK @ ' + theLink + ':' + str(resp.status_code)) #, ' --> FINAL URL: ', resp.url
									crawler_db.addURL(theLink, 'feeds', cursor)									
								else:
									reason = '	RSS ERROR @' + theLink + ' ==> BAD ContentType:' + resp.headers['content-type']
									log.info(reason)
									crawler_db.addURL(theLink, 'bad_feeds', cursor, reason)
							else:	
								reason = '	RSS ERROR @' + theLink + ':' + str(resp.status_code)
								log.info(reason)
								crawler_db.addURL(theLink, 'bad_feeds', cursor, reason)
						except Exception as ex:
							reason = '	### Unexpected ERROR ###' + str(ex) + " from LINK: " + theLink 
							log.error(reason, exc_info=True) #traceback.print_exc(file=sys.stdout)
							crawler_db.addURL(theLink, 'bad_feeds', cursor, reason)
					else:
						reason = '	WARN: RSS duplicate or bad feed:' + theLink
						log.warning(reason)

				# save crawled link	
				crawler_db.addURL(url, 'crawled', cursor)				
				# remove crawled link from todos
				crawler_db.removeTodo(url, cursor, 'OK')
		else:
			log.warning('URL: ' + url + '  is not valid!')
			crawler_db.removeTodo(url, cursor, 'URL not valid')							
	else: # no url availabel in TODO
		log.warning('WARN: No URLs available in TODO list. Program will exit!')
		return False
	#at the end of page processing close this cursor and return true tp fetch next page
	cursor.close()	
	return True	

#####################
# print short help message
#####################
def print_usage():
	print 'Usage: rss_crawler.py -s,--start \'http://www.start-here.com\' -d,--drop -c,--console -p,--pwd mysql-root-password'
	sys.exit()	


#################################
# if it's executed as a script
#################################
if __name__ == "__main__":
	argv = sys.argv[1:]
	try:	
		opts, args = getopt.getopt(argv,"hs:dcp:",["start=","drop","console","pwd="])
		if len(opts) > 5:
			print_usage()
	except getopt.GetoptError:
		traceback.print_exc(file=sys.stdout)
		print_usage()	

	for opt, arg in opts:
		if opt == '-h':
			print_usage()
		elif opt in ("-s", "--start"):
			# override START url with link provided		
			GLOBAL_CONFIG['start_urls'] = [ arg ]					
		elif opt in ("-d", "--drop"):
			GLOBAL_CONFIG['drop_existing_database'] = True
		elif opt in ("-c", "--console"):
			GLOBAL_CONFIG['log_to_file'] = False	
		elif opt in ("-p", "--pwd"):
			if arg == 'none':
				DB_CONFIG.pop('password')
			else:
				DB_CONFIG['password'] = arg
	#logging setup:  %(name)s => logger name, %(module)s => module name
	# If you want each run to start afresh, not remembering the messages from earlier runs, you can specify the 'filemode' argument
	if GLOBAL_CONFIG['log_to_file']:
		logging.basicConfig(filename='crawler.log', filemode='w', level=logging.ERROR, format='%(asctime)s : %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
	else:
		logging.basicConfig(level=logging.ERROR, format='%(asctime)s : %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

	#get root logger and set DEBUG level as opposed to global ERROR level
	log = logging.getLogger('rss_crawler')
	log.setLevel(logging.DEBUG)

	log.debug('START - Magic RSS Crawler (Alpha)')
	
	try:
		crawler_db.prepare_database();

		cnx = crawler_db.get_crawlerdb_connection()
		# set up initial TOD urls	
		crawler_db.run_in_transaction(init_todo, cnx)

		#lauch crawling process 
		while True:
			next = crawler_db.run_in_transaction(crawl_feeds, cnx)		
			if not next:
				log.warning('No more URLs to crawl (todo must be empty)! Program will exit!!!')
				break;
		#close connection when finished
		cnx.close()
	except:
		log.error('This is really bad. Will exit now! ', exc_info=True)
		exit(3)
	
			