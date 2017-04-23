# coding: utf-8
from bs4 import BeautifulSoup

class HTMLParser:
  def pull_text_from_html(self, html):
    parser = BeautifulSoup(html, 'html.parser')
    for script in parser(["script", "style"]):
      script.extract()
      
    raw_string = parser.get_text(separator=u' ')
    return raw_string.strip().replace(u'\xa0', u' ')