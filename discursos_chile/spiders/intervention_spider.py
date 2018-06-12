# -*- coding: utf-8 -*-
import scrapy
import html2text
import ipdb


class InterventionSpider(scrapy.Spider):
    name = 'intervention'
    allowed_domains = ['senado.cl']
    start_urls = [
        'http://www.senado.cl/appsenado/index.php?mo=senadores&ac=intervenciones_senador&parlamentario=1119&ano=2017']

    def parse_intervention_list(self, response):
        scrapy.shell.inspect_response(response, self)
        for url in response.xpath('//a[contains(text(),"Intervención")]/@href'):
            yield scrapy.Request(url, parse_intervention)

    def parse_intervention(self, response):
        import ipdb
        ipdb.set_trace()
        html2text.html2text(response.xpath('//article/div').extract_first())
