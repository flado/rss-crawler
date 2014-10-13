# RSS Crawler #

This README file documents whatever steps are necessary to get this application up and running.

### What is this repository for? ###

An RSS Crawler implementation in Phyton and MySQL.

### How do I get set up? ###

1. Install Python 2.7.x

2. Install pip
	* or download from:  https://bootstrap.pypa.io/get-pip.py
```
	cd pip
	python get-pip.py
```

3. Install dependencies using pip:
	* http://docs.python-requests.org/en/latest/
	* https://pypi.python.org/pypi/beautifulsoup4
	* https://pypi.python.org/pypi/feedparser
```
	pip install beautifulsoup4
	pip install requests
	pip install feedparser
```

4. MySQL database Configuration
```
	crawler_config.py -> contains database configurations for ROOT (ROOT_DB_CONFIG) and CRAWLER_DB (CRAWLER_DB_CONFIG). Update configuration with your values.
```

5. Start MySQL
```
	mysqld (remember to check the port in my.cnf and update ROOT_DB_CONFIG above)
```

6. Configure proxy (if any)
	* if you're running this app under a proxy please remeber to configure the HTTP_PROXY amd HTTPS_PROXY env variables
```
	$ export HTTP_PROXY="http://user:pass@10.10.1.10:3128/"
	$ export HTTPS_PROXY="http://user:pass@10.10.1.10:3128/"
```	

7. Run 
```
	python rss_crawler.py --db crawler_database
```


### Configuration guidelines ###
	* The script allows for multiple configurations that can be changed in crawler_config.py file:

| Name | Properties          |
| ------------- | ----------- |
| GLOBAL_CONFIG      | 'start_urls', 'drop_existing_database', 'log_to_file' |
| Close     | Closes a window    


### Contribution guidelines ###

Feel free to contribute to this repo. 

### Who do I talk to? ###

* Repo owner or admin (flado)

## Licence
Licensed under the permissive MIT license