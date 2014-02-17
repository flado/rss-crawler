# dict can be used as a true global and changed in other modules and reflected in other imports
GLOBAL_CONFIG = {
	'start_urls' : ['http://www.yahoo.com', 'http://www.infoq.com'],
	'drop_existing_database' : False,
	'log_to_file' : True	
}

MAX_PAGES_PER_DOMAIN = 6 # maxim number of pages per domain to be fetched for parsing

EXCLUDES = [ 'google.com', 'facebook.com', 'youtube.com', 'twitter.com', 'rsvp.com', 'doubleclick.net', 'ebay.com', 'chemspider.com' ]

#exclude RSS URLs that contains the words in this list
RSS_EXCLUDES = [ 'comment', 'porn', 'chemspider' ]

BAD_SUFIXES = ['.pdf', '.doc', '.docx', '.rtf', 
'.mov', '.mp4', '.avi', '.wmv', '.wma', '.asf', '.qt', '.mkv', '.mpeg',
'.mp3', 
'.jpeg', '.jpg', '.bmp']

BAD_PREFIXES = ['mailto:', 'javascript:', '#']

# the dict can be used as a true global and changed in other modules and reflected in other imports
# root database config
ROOT_DB_CONFIG = { 
	'user': 'root', 
	'password': 'ZeroPII', 
	'host': '127.0.0.1', 
	'raise_on_warnings': True
}

#crawler database config
CRAWLER_DB_CONFIG = { 
    'user': 'crawler', 
    'password': '1qa2ws', 
    'host': '127.0.0.1', 
    'database': 'crawlerdb', 
    'raise_on_warnings': True, 
    }

def badPrefix(url):
	for prefix in BAD_PREFIXES:
		if url.startswith(prefix):
			return True
	return False		

def badSufix(url):
	for sufix in BAD_SUFIXES:
		if url.endswith(sufix):
			return True
	return False		

###################################
# determine if an url is good or not for fetching
###################################
def badURL(url):
	if badPrefix(url) or badSufix(url):
		return True
	for exclude_name in EXCLUDES:
		if exclude_name in url:
			return True
	return False	

##### check if RSS url is bad
def badRSS(url):
	for exclude_name in RSS_EXCLUDES:
		if exclude_name in url:
			return True
	return False	
