from lxml import html
from scrapy import Request
import scrapy
from scrapy.item import Item, Field
import moment


class SiteProductItem(Item):

    Date = Field()
    Time = Field()
    VisitorTeam = Field()
    HomeTeam = Field()


class AmazonReviewScraper (scrapy.Spider):
    name = "scrapingdata"
    allowed_domains = ['www.baseball-reference.com']
    DOMAIN_URL = 'https://www.baseball-reference.com'
    START_URL = 'https://www.baseball-reference.com/leagues/MLB/2017-schedule.shtml'

    def __init__(self, **kwargs):
        self.headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
                                      " Chrome/70.0.3538.102 Safari/537.36"}

    def start_requests(self):
        yield Request(url=self.START_URL,
                      callback=self.get_boxscore_urls,
                      headers=self.headers,
                      dont_filter=True
                      )

    def get_boxscore_urls(self, response):

        boxscore_urls = response.xpath('//p[@class="game"]/em/a/@href').extract()

        for boxscore_url in boxscore_urls:
            url = self.DOMAIN_URL + boxscore_url
            yield Request(url=url,
                          callback=self.parse_detail,
                          dont_filter=True,
                          headers=self.headers
                          )

    def parse_detail(self, response):

        product = SiteProductItem()

        Date = self._parse_Date(response)
        product['Date'] = Date

        Time = self._parse_Time(response)
        product['Time'] = Time

        VisitorTeam = self._parse_VisitorTeam(response)
        product['VisitorTeam'] = VisitorTeam

        HomeTeam = self._parse_HomeTeam(response)
        product['HomeTeam'] = HomeTeam

        yield product

    @staticmethod
    def _parse_VisitorTeam(response):
        team_names = response.xpath('//div[@class="scorebox"]//strong/a/text()').extract()
        visitor_team_name = str(team_names[0]) if team_names else None

        score_theader = response.xpath('//table/thead//th/text()').extract()
        score_visitor_tr = response.xpath('//table/tbody/tr')[0]
        score_visitor_score_values = score_visitor_tr.xpath('./td/text()').extract()
        visitor_scores = {}
        for index in range(2, len(score_visitor_score_values)):
            key = str(score_theader[index])
            score_value = str(score_visitor_score_values[index])
            try:
                visitor_scores[key] = int(score_value)
            except:
                visitor_scores[key] = 0

        visitor_team_tabble_id = visitor_team_name.replace(' ', '') + 'batting'
        theader = html.fromstring(response.body.replace('<!--', '').replace('--!>', '')).xpath(
            '//table[@id="%s"]/thead//th/text()' % visitor_team_tabble_id)
        tfoot_td = html.fromstring(response.body.replace('<!--', '').replace('--!>', '')).xpath(
            '//table[@id="%s"]/tfoot//td/text()' % visitor_team_tabble_id)
        visitor_state = {}
        for index, value in enumerate(tfoot_td):
            try:
                parsed_value = int(value)
            except:
                parsed_value = float(value)
            visitor_state[theader[index+1]] = parsed_value
        visitor_team_info = {
            'name': visitor_team_name,
            'stat': visitor_state,
            'scores': visitor_scores
        }

        return visitor_team_info

    @staticmethod
    def _parse_HomeTeam(response):
        team_names = response.xpath('//div[@class="scorebox"]//strong/a/text()').extract()
        home_team_name = str(team_names[1]) if team_names else None

        score_theader = response.xpath('//table/thead//th/text()').extract()
        score_home_tr = response.xpath('//table/tbody/tr')[1]
        score_home_score_values = score_home_tr.xpath('./td/text()').extract()
        home_scores = {}
        for index in range(2, len(score_home_score_values)):
            key = str(score_theader[index])
            score_value = str(score_home_score_values[index])
            try:
                home_scores[key] = int(score_value)
            except:
                home_scores[key] = 0

        home_team_tabble_id = home_team_name.replace(' ', '') + 'batting'
        theader = html.fromstring(response.body.replace('<!--', '').replace('--!>', '')).xpath(
            '//table[@id="%s"]/thead//th/text()' % home_team_tabble_id)
        tfoot_td = html.fromstring(response.body.replace('<!--', '').replace('--!>', '')).xpath(
            '//table[@id="%s"]/tfoot//td/text()' % home_team_tabble_id)
        home_state = {}
        for index, value in enumerate(tfoot_td):
            try:
                parsed_value = int(value)
            except:
                parsed_value = float(value)
            home_state[theader[index + 1]] = parsed_value
        home_team_info = {
            'name': home_team_name,
            'stat': home_state,
            'scores': home_scores
        }

        return home_team_info

    @staticmethod
    def _parse_Date(response):
        game_infos = response.xpath('//div[@class="scorebox_meta"]/div/text()').extract()
        date_info = str(game_infos[0]) if game_infos else None
        result_date = moment.date(date_info)
        year = result_date.year
        month = result_date.month
        day = result_date.day
        final_date = {
            'year': year,
            'month': month,
            'day': day
        }

        return final_date

    @staticmethod
    def _parse_Time(response):
        game_infos = response.xpath('//div[@class="scorebox_meta"]/div/text()').extract()
        return str(game_infos[1]) if game_infos else None
