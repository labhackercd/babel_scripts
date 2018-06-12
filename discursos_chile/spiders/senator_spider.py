import scrapy
from scrapy.selector import Selector
from discursos_chile.items import SenatorItem
from datetime import date
import intervention_spider


class SenatorSpider(scrapy.Spider):
    name = "senators"
    start_urls = [
        'http://senado.cl/prontus_senado/site/edic/base/port/senadores.html',
    ]

    def parse(self, response):
        for senator in Selector(response=response).xpath('//*[@id="main"]/section/div'):
            senator_page = senator.xpath('a/@href').extract_first()
            yield(scrapy.Request(response.urljoin(senator_page), self.parse_senators))

    def parse_senators(self, response):
        item = SenatorItem()
        item['senator_id'] = response.xpath('//*[@id="parlid"]/@value').extract_first()
        item['name'] = response.xpath('//div[@class="datos"]/../h1/text()').extract_first()
        item['party'] = response.xpath(
            '//strong[contains(text(),"Partido")]/following-sibling::text()').extract_first().strip()
        item['phone'] = response.xpath(
            '//strong[contains(text(),"Teléfono")]/following-sibling::text()').extract_first().strip()
        item['email'] = response.xpath(
            '//strong[contains(text(),"Mail")]/following-sibling::text()').extract_first().strip()
        item['region'] = response.xpath(
            '//*[@id="main"]/section[1]/div[1]/div[2]/h2[2]/text()').extract_first()

        yield item

        for year in range(2004, date.today().year + 1):
            yield scrapy.FormRequest(
                'http://www.senado.cl/appsenado/index.php',
                intervention_spider.InterventionSpider().parse_intervention_list,

                formdata=dict(
                    mo='senadores',
                    ac='intervenciones_senador',
                    parlamentario=item['senator_id'],
                    ano=str(year),
                ),

            )
