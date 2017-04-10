# coding: utf-8

import re
from bs4 import BeautifulSoup

class HTMLParser:
  def pull_content_from_html(self, content):
    parsed_html = self.pull_text_from_html(content)
    return self.__content_with_non_article_text_removed(parsed_html)

  def pull_text_from_html(self, html):
    parser = BeautifulSoup(html, 'html.parser')
    for script in parser(["script", "style"]):
      script.extract()
      
    raw_string = parser.get_text(separator=u' ')
    return raw_string.strip().replace(u'\xa0', u' ')

  def __content_with_non_article_text_removed(self, content):
    regex_to_remove = (
      ('continue reading$', True),                    # Economist
      ('^([A-Z]+,?.+ )?\(.*Reuters.*\) [-―] ', True), # Reuters + HuffPo, e.g. "BATON ROGUE, La. (Reuters) - ", "WASHINGTON, Dec 11 (Reuters) - ", "(Reuters) -", "WASHINGTON -"
      ('^[A-Z]+ [-―]', False),                        # HuffPo, e.g. "WASHINGTON -"
      ('^BY [A-Z ]+[-_:]+', True),                    # Remove author, e.g. "BY CYNTHIA ANDERSON -"
      ('^[A-Z ]+, [A-Z]+ - [A-Z]+ [0-9]{1,2}:', True) # Forbes, e.g. 'LOS ANGELES, CA - NOVEMBER 29:'
    )
    for regex in regex_to_remove:
      flags = re.IGNORECASE if regex[1] else 0
      content = re.sub(regex[0], "", content, flags=flags)

    return content.strip()