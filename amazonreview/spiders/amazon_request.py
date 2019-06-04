import json
import re
import urllib
from lxml import html
from amazonreview.spiders.amazon_captcha_resolver import resolve_captcha
from http_util import HttpRequest
import scrapy
from scrapy import Request
from scrapy.item import Item, Field


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


class ProductItem(Item):
    comment = Field()
    writer_name = Field()
    rating = Field()
    date = Field()
    movie_name = Field()


class AmazonProductsSpider(scrapy.Spider):
    name = "scrapingdata"
    allowed_domains = ['www.amazon.com']
    START_URL = 'https://www.amazon.com/Transformers-Last-Knight-Mark-Wahlberg/product-reviews/B07215NWRL' \
                '/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews'

    def __init__(self):
        self.page = AmazonPage()

    def start_requests(self):
        yield Request(url=self.START_URL,
                      callback=self.parse,
                      dont_filter=True
                      )

    def parse(self, response):

        for page_num in range(0, 5):
            url = self.START_URL + '&pageNumber=' + str(page_num)

            if not self.page.navigate_to(url):
                return

            assert_urls = self.page.tree.xpath('//div[@class="a-row"]//a[@class="a-link-normal"]/@href')
            page_urls = []
            for assert_url in assert_urls:
                page_url = 'https://www.amazon.com' + assert_url
                page_urls.append(page_url)

            for page_url in page_urls:
                page_content = HttpRequest().get(page_url)
                page_content_tree = html.fromstring(page_content)

                product = ProductItem()

                try:
                    comment = page_content_tree.xpath(
                        '//span[@class="a-size-base review-text review-text-content"]/span/text()')[0]
                except:
                    comment = ''

                try:
                    writer_name = page_content_tree.xpath(
                        '//span[@class="a-profile-name"]//text()')[0]
                except:
                    writer_name = ''

                try:
                    rating = page_content_tree.xpath('//i[@data-hook="review-star-rating"]/span/text()')[0].split(' ')[0]
                except:
                    rating = ''

                try:
                    date = page_content_tree.xpath('//span[@data-hook="review-date"]//text()')[0]
                except:
                    date = ''

                product['comment'] = comment
                product['writer_name'] = writer_name
                product['rating'] = rating
                product['date'] = date

                if comment:
                    yield product


# if __name__ == '__main__':
#     amazonproduct = AmazonProductsSpider()
#     url = 'https://www.amazon.com/Transformers-Last-Knight-Mark-Wahlberg/product-reviews/B07215NWRL/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews'
#     amazonproduct.parse(url)
