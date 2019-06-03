import json
import re
import urllib
from http_util import HttpRequest
from lxml import html
from amazon_captcha_resolver import resolve_captcha


class AmazonPage(object):
    BASE_URL = 'https://www.amazon.cn/'

    def __init__(self):
        self.request = HttpRequest()
        return

    @staticmethod
    def get_abs_link(url):
        if not url:
            return ""
        if not url.startswith('http'):
            url = urllib.parse.urljoin(AmazonPage.BASE_URL, url)
        return url

    @staticmethod
    def is_product_link(url):
        url = AmazonPage.get_abs_link(url)
        return url.startswith('https://www.amazon.cn/dp/')


    @staticmethod
    def normalize_product_link(url):
        if url:
            m = re.search(r'https://www\.amazon\.cn/dp/[a-zA-Z0-9]+', url)
            if m:
                return m.group(0)

    def navigate_to(self, url, auto_resolve_captcha=True):
        try:
            self.url = AmazonPage.get_abs_link(url)
            self.page_content = self.request.get(self.url)
            self.tree = html.fromstring(self.page_content)

            if self.has_captcha():
                if auto_resolve_captcha:
                    for _ in range(10):
                        self.resolve_captcha()
                        if self.navigate_to(url, False) and self.has_captcha() == False:
                            return True
                    return False

            return True
        except Exception as e:
            print(e)

            self.url = None
            self.page_content = None
            self.tree = None

        return False

    def get_page_data(self, url):
        if not self.navigate_to(url):
            return

        m = re.findall(r'window\.\$Nav && \$Nav\.when\("data"\)\.run\(function\(data\) \{ data\(([ \t\S]+)\); \}\);', self.page_content)
        if not m:   # Cannot parse
            return

        return json.loads(m[-1])

    def has_captcha(self):
        return self.page_content and self.page_content.find('captcha') > 0

    def resolve_captcha(self):
        form_element = self.tree.xpath('//form[@action="/errors/validateCaptcha"]') if self.tree is not None else None
        if not form_element:
            return
        else:
            form_element = form_element[0]

        print("Trying to resolve captcha:", self.url)

        captcha_link = form_element.xpath('.//img/@src')
        if captcha_link:
            page_link = self.get_abs_link(form_element.attrib['action']) + '?'
            for param in form_element.xpath('./input'):
                name = param.attrib['name']
                if name == 'amzn-r':
                    value = '%2F'   # Set redirect url to '/'
                else:
                    value = urllib.parse.quote(param.attrib['value'])
                page_link += "{name}={value}&".format(name=name, value=value)

            page_link += '&field-keywords=' + resolve_captcha(captcha_link[0])

        if self.navigate_to(page_link, False) and self.has_captcha() is False:
            return True

        return False


class AmazonProductsSpider(object):
    def __init__(self):
        self.page = AmazonPage()

    def parse(self, url):
        product = {}
        if not self.page.navigate_to(url):
            return
        self.page


if __name__ == '__main__':
    amazonproduct = AmazonProductsSpider()
    url = 'https://www.amazon.com/Transformers-Last-Knight-Mark-Wahlberg/product-reviews/B07215NWRL/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews'
    amazonproduct.parse(url)
