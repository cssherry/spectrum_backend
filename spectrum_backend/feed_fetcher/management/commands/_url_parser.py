import re
from urlparse import urlparse

class URLParser:
  def clean_url(self, raw_url):
    url_parameter_delimiter = "?"
    path = raw_url.split(url_parameter_delimiter)[0]
    return 

  def pull_description_from_url(self, url):
    regex_to_find = (
    '^.+\/([a-zA-Z0-9\-]+).html$', # Fox News
    '\/[0-9]{8}-([a-z-]+)$' # The Economist
    )
    for regex in regex_to_find:
      matches = re.search(regex, url)
      if matches:
        return matches.group(1).replace("-", " ")
      else:
        return ""

  def shorten_url(self, raw_url):
    p = urlparse(url_string)
    return p.hostname + p.path

  def is_base_url(self, raw_url):
    p = urlparse(raw_url)
    return p.path == "" or p.path == "/"