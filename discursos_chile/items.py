import scrapy


class SenatorItem(scrapy.Item):
    senator_id = scrapy.Field()
    name = scrapy.Field()
    party = scrapy.Field()
    phone = scrapy.Field()
    email = scrapy.Field()
    region = scrapy.Field()
    url = scrapy.Field()


class InterventionItem(scrapy.Item):
    senator_id = scrapy.Field()
    date = scrapy.Field()
    speech = scrapy.Field()
    url = scrapy.Field()
