import re

class URLParser:
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