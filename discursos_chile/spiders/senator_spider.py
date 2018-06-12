import scrapy
from scrapy.selector import Selector
from discursos_chile.items import SenatorItem, InterventionItem
from html2text import html2text
from datetime import datetime


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
        item['url'] = response.request.url
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

        for year in range(2004, datetime.now().year + 1):
            yield scrapy.FormRequest(
                'http://www.senado.cl/appsenado/index.php',
                self.parse_intervention_list,

                formdata=dict(
                    mo='senadores',
                    ac='intervenciones_senador',
                    parlamentario=item['senator_id'],
                    ano=str(year),
                ),
                method='GET',
                meta={'senator_id': item['senator_id']}
            )

    def parse_intervention_list(self, response):
        for intervencion in response.xpath('//a[contains(text(),"Intervenci")]'):
            url = intervencion.xpath('@href').extract_first()
            date = intervencion.xpath('../../td[2]/text()').extract_first()
            response.meta['date'] = date + 'T00:00'
            yield scrapy.Request(response.urljoin(url), self.parse_intervention, meta=response.meta)

    def parse_intervention(self, response):
        speech = html2text(response.xpath('//article/div').extract_first()).split('.- ')[1:]
        speech = ' '.join(speech)
        intervention = InterventionItem()
        intervention['senator_id'] = response.meta['senator_id']
        intervention['speech'] = speech.replace('\n', ' ')
        intervention['date'] = response.meta['date']
        intervention['url'] = response.request.url

        yield intervention
