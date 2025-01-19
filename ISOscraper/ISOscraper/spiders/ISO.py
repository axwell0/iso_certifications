import re

import scrapy
from ..items import IsoscraperItem


class ISOScraper(scrapy.Spider):
    name = 'ISO'
    start_urls = ['https://www.iso.org/standards-catalogue/browse-by-ics.html']

    def start_requests(self):
        yield scrapy.Request(url=self.start_urls[0], callback=self.parse_category)

    def parse_iso(self, response):
        final = IsoscraperItem()

        if "Abstract" in response.css('h2::text').getall():
            abstract = response.css('div[itemprop="description"]').xpath('string(.)').get().strip()
            final['abstract'] = abstract
        else:
            c = []
            for h2 in response.css('h2'):
                if h2.css('::text').get() != "Benefits":
                    hol = ''

                    for sibling in h2.xpath('following-sibling::*'):
                        if sibling.root.tag == 'p':
                            hol += re.sub(r'<[^>]+>', '', sibling.get()).replace(u'\xa0', u'') + "\n"
                        else:
                            break
                    c.append({h2.css('::text').get():hol})
            if c:
                final["content"] = c

        status = response.css('#publicationStatus span::text').get()
        if status:
            status = status.strip()

        publication_date = response.css('#publicationDate [itemprop="releaseDate"]::text').get()
        if publication_date:
            publication_date = publication_date.strip()

        stage_raw = response.css('#stageId::text').getall()
        stage = ' '.join([txt.strip() for txt in stage_raw]).replace('Stage : ', '')
        stage = stage.strip()
        second_row = [x for x in [s.replace(u'\xa0', u' ').strip().lstrip(':').strip() for s in
                                  response.css('ul.refine > li:nth-child(2) div::text').getall()] if x != '']

        if 'Edition' in second_row:
            edition = second_row[second_row.index('Edition') + 1]
        else:
            edition = None
        if "Number of pages" in second_row:
            number_of_pages = second_row[second_row.index('Number of pages') + 1]
        else:
            number_of_pages = None
        technical_committee = response.xpath(
            '//div[div[@class="entry-label" and contains(., "Technical Committee")]]'
            '//span[@class="entry-name entry-block"]/a/text()'
        ).get()
        if technical_committee:
            technical_committee = technical_committee.strip()
        ics = response.xpath(
            '//div[div[@class="entry-label" and contains(.,"ICS")]]'
            '//span[@class="entry-name entry-block"]/a/text()'
        ).get()
        if ics:
            ics = ics.strip()
        """re.sub(r'</?strong>', '', re.sub(r'\s{3,}', '', response.css('div.accordion.faqs h3 + div.accordion-collapse div.accordion-body')[1].get().strip()))"""

        final['Iso'] = response.meta.get('iso')
        final['Category'] = response.meta.get('Category')
        final['SubCategory'] = response.meta.get('Subcategory')
        final['description'] = response.meta.get('description').replace(u'\xa0', u' ')

        final['publication_date'] = publication_date
        final['stage'] = stage.lstrip(':').strip()
        final['edition'] = edition
        final['number_of_pages'] = number_of_pages
        final['technical_committee'] = technical_committee
        final['ics'] = ics
        final['url'] = response.url
        yield final

    def parse_iso_listings(self, response):
        for item in response.css("table#datatable-ics-projects tr[ng-show='pChecked || pChecked == null']"):
            url = item.css('div.fw-semibold a::attr(href)').get()
            iso = item.css('span.entry-name::text').get()
            description = item.css('div.entry-description::text').get()
            yield scrapy.Request(url=f"https://www.iso.org{url}", callback=self.parse_iso,
                                 meta={"Category": response.meta.get('Category'),
                                       "Subcategory": response.meta.get('Subcategory'), "iso": iso,
                                       "description": description}, )

    def parse_subcategory(self, response):
        urls = [s.strip() for s in response.css("table tr td[data-title='ICS'] a::attr(href)").getall()]
        categories = [s.strip() for s in response.css("table tr td[data-title='Field']::text").getall()]
        for cat, url in zip(categories, urls):
            yield scrapy.Request(url=f"https://www.iso.org{url}", callback=self.parse_iso_listings,
                                 meta={"Category": response.meta.get("Category"), "Subcategory": cat})

    def parse_category(self, response):

        urls = [s.strip() for s in response.css("table tr td[data-title='ICS'] a::attr(href)").getall()]
        categories = [s.strip() for s in response.css("table tr td[data-title='Field']::text").getall()]
        for cat, url in zip(categories, urls):
            yield scrapy.Request(url=f"https://www.iso.org{url}", callback=self.parse_subcategory,
                                 meta={"Category": cat})
