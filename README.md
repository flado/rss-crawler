# RSS Crawler #

This README file documents whatever steps are necessary to get this application up and running.

### What is this repository for? ###

An RSS Crawler implementation in Phyton and MySQL.

### How do I get set up? ###

1. Install Python 2.7.x
1. dfsf
1. sdfdsfsf
ffffffffffffffffffffffffff
```cd dddd```
1. ggggggg
* dgfdfgfdgfd
1. vgdfggdgd


Install pip
...or download from:  https://bootstrap.pypa.io/get-pip.py
```
	cd pip
	python get-pip.py
```
1. Install dependencies using pip:
	* http://docs.python-requests.org/en/latest/
	* https://pypi.python.org/pypi/beautifulsoup4
	* https://pypi.python.org/pypi/feedparser
```
	pip install beautifulsoup4
	pip install requests
	pip install feedparser
```
1. MySQL database Configuration
```
	crawler_config.py -> contains database configurations for ROOT (ROOT_DB_CONFIG) and CRAWLER_DB (CRAWLER_DB_CONFIG). Update configuration with your values.
```
1. Start MySQL
```
	mysqld (remember to check the port in my.cnf and update ROOT_DB_CONFIG above)
```
1. Configure proxy (if any)
If you're running this app under a proxy please remeber to configure the HTTP_PROXY amd HTTPS_PROXY env variables
```
	$ export HTTP_PROXY="http://user:pass@10.10.1.10:3128/"
	$ export HTTPS_PROXY="http://user:pass@10.10.1.10:3128/"
```	
1. Run 
```
	python rss_crawler.py --db crawler_database
```

### Configuration guidelines ###

The 'rss_crawler.py' script allows for multiple configurations that can be changed in 'crawler_config.py' file:

| Name | Description |
| ------------- | ----------- |
| GLOBAL_CONFIG    | 'start_urls', 'drop_existing_database', 'log_to_file' |
| LOG_SETTINGS     |  'formatters', 'handlers', 'loggers' |
| MAX_PAGES_PER_DOMAIN | max number of pages to check in current domain |
| EXCLUDES | domain names to exclude from crawling |
| RSS_EXCLUDES | keywords that determine if the RSS will be excluded |
| BAD_SUFIXES | deprecated |
| MAX_CONTENT_LENGTH | max size in bytes for a page to be fetched |
| ROOT_DB_CONFIG | MySQL root user and password |
| CRAWLER_DB_CONFIG | Crawler database: user configuration & database name |

Have a look in 'crawler_config.py' for the default values!!


### Contribution guidelines ###

Feel free to contribute to this repo. 

### Who do I talk to? ###

* Repo owner or admin (https://bitbucket.org/flado)

## Licence
Licensed under the permissive MIT license