from mock import patch
from nose.tools import *  # noqa
from rest_framework.test import APITestCase
from django.test.utils import override_settings

from indigo_api.renderers import PDFRenderer


# Disable pipeline storage - see https://github.com/cyberdelia/django-pipeline/issues/277
@override_settings(STATICFILES_STORAGE='pipeline.storage.PipelineStorage', PIPELINE_ENABLED=False)
class PublishedAPITest(APITestCase):
    fixtures = ['user', 'published', 'colophon']

    def test_published_json(self):
        response = self.client.get('/api/za/act/2014/10')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['frbr_uri'], '/za/act/2014/10')

        response = self.client.get('/api/za/act/2014/10.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['frbr_uri'], '/za/act/2014/10')

        response = self.client.get('/api/za/act/2014/10/eng.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['frbr_uri'], '/za/act/2014/10')

    def test_published_xml(self):
        response = self.client.get('/api/za/act/2014/10.xml')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/xml')
        assert_in('<akomaNtoso', response.content)

        response = self.client.get('/api/za/act/2014/10/eng.xml')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/xml')
        assert_in('<akomaNtoso', response.content)

    @patch.object(PDFRenderer, '_wkhtmltopdf', return_value='pdf-content')
    def test_published_pdf(self, mock):
        response = self.client.get('/api/za/act/2014/10.pdf')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/pdf')
        assert_in('pdf-content', response.content)

        response = self.client.get('/api/za/act/2014/10/eng.pdf')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/pdf')
        assert_in('pdf-content', response.content)

    def test_published_epub(self):
        response = self.client.get('/api/za/act/2014/10.epub')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/epub+zip')
        assert_true(response.content.startswith('PK'))

        response = self.client.get('/api/za/act/2014/10/eng.epub')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/epub+zip')
        assert_true(response.content.startswith('PK'))

    def test_published_html(self):
        response = self.client.get('/api/za/act/2014/10.html')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'text/html')
        assert_not_in('<akomaNtoso', response.content)
        assert_in('<div', response.content)

        response = self.client.get('/api/za/act/2014/10/eng.html')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'text/html')
        assert_not_in('<akomaNtoso', response.content)
        assert_not_in('<body', response.content)
        assert_in('<div', response.content)

    def test_published_html_standalone(self):
        response = self.client.get('/api/za/act/2014/10.html?standalone=1')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'text/html')
        assert_not_in('<akomaNtoso', response.content)
        assert_in('<body  class="standalone"', response.content)
        assert_in('class="colophon"', response.content)
        assert_in('class="toc"', response.content)

    def test_published_listing(self):
        response = self.client.get('/api/za/')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(len(response.data['results']), 4)

        response = self.client.get('/api/za/act/')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(len(response.data['results']), 4)

        response = self.client.get('/api/za/act/2014')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(len(response.data['results']), 1)

    @patch.object(PDFRenderer, '_wkhtmltopdf', return_value='pdf-content')
    def test_published_listing_pdf(self, mock):
        response = self.client.get('/api/za/act.pdf')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/pdf')
        assert_in('pdf-content', response.content)

    def test_published_listing_pagination(self):
        response = self.client.get('/api/za/')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(set(response.data.keys()), set(['next', 'previous', 'count', 'results', 'links']))

    def test_published_listing_html_404(self):
        # explicitly asking for html is bad
        response = self.client.get('/api/za/act.html')
        assert_equal(response.status_code, 404)
        assert_equal(response.accepted_media_type, 'text/html')

    def test_published_listing_pdf_404(self):
        response = self.client.get('/api/za/act/bad.pdf')
        assert_equal(response.status_code, 404)

    def test_published_listing_epub_404(self):
        response = self.client.get('/api/za/act/bad.epub')
        assert_equal(response.status_code, 404)

    def test_published_atom(self):
        response = self.client.get('/api/za/summary.atom')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/atom+xml')

        response = self.client.get('/api/za/full.atom')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/atom+xml')

        response = self.client.get('/api/za/act/2014/full.atom')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/atom+xml')

    def test_published_atom_404(self):
        response = self.client.get('/api/uk/summary.atom')
        assert_equal(response.status_code, 404)
        assert_equal(response.accepted_media_type, 'text/html')

    def test_published_missing(self):
        assert_equal(self.client.get('/api/za/act/2999/22').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2999/22.html').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2999/22.xml').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2999/22.json').status_code, 404)

        assert_equal(self.client.get('/api/za/act/2999/22/eng').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2999/22/eng.html').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2999/22/eng.xml').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2999/22/eng.json').status_code, 404)

    def test_published_wrong_language(self):
        assert_equal(self.client.get('/api/za/act/2014/10/fre').status_code, 404)
        assert_equal(self.client.get('/api/za/act/2014/10/fre.html').status_code, 404)

    def test_published_listing_missing(self):
        assert_equal(self.client.get('/api/za/act/2999/').status_code, 404)
        assert_equal(self.client.get('/api/zm/').status_code, 404)

    def test_published_toc(self):
        response = self.client.get('/api/za/act/2014/10/eng/toc.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['toc'], [
            {'id': 'section-1', 'type': 'section', 'num': '1.',
                'component': 'main', 'subcomponent': 'section/1',
                'url': 'http://testserver/api/za/act/2014/10/eng/main/section/1',
                'title': 'Section 1.'}])

        response = self.client.get('/api/za/act/2014/10/toc.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['toc'], [
            {'id': 'section-1', 'type': 'section', 'num': '1.',
                'component': 'main', 'subcomponent': 'section/1',
                'url': 'http://testserver/api/za/act/2014/10/eng/main/section/1',
                'title': 'Section 1.'}])

    def test_published_subcomponents(self):
        response = self.client.get('/api/za/act/2014/10/eng/main/section/1.xml')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/xml')
        assert_equal(response.content, '<section xmlns="http://www.akomantoso.org/2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="section-1">\n  <num>1.</num>\n  <content>\n    <p>tester</p>\n  </content>\n</section>\n')

        response = self.client.get('/api/za/act/2014/10/eng/main/section/1.html')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'text/html')
        assert_equal(response.content, '<section class="akn-section" id="section-1"><h3>1. </h3><span class="akn-content"><span class="akn-p">tester</span></span></section>')

    def test_at_expression_date(self):
        response = self.client.get('/api/za/act/2010/1/eng@2011-01-01.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['expression_date'], '2011-01-01')

        # doesn't exist
        response = self.client.get('/api/za/act/2011/5/eng@2099-01-01.json')
        assert_equal(response.status_code, 404)

    def test_before_expression_date(self):
        # at or before 2015-01-01
        response = self.client.get('/api/za/act/2010/1/eng:2015-01-01.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['expression_date'], '2012-02-02')

        # at or before 2012-01-01
        response = self.client.get('/api/za/act/2010/1/eng:2012-01-01.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['expression_date'], '2011-01-01')

        # doesn't exist
        response = self.client.get('/api/za/act/2010/1/eng:2009-01-01.json')
        assert_equal(response.status_code, 404)

    def test_latest_expression(self):
        response = self.client.get('/api/za/act/2010/1/eng.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['expression_date'], '2012-02-02')

    def test_earliest_expression(self):
        response = self.client.get('/api/za/act/2010/1/eng@.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['expression_date'], '2011-01-01')

    def test_published_amended_versions(self):
        response = self.client.get('/api/za/act/2010/1/eng@.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['frbr_uri'], '/za/act/2010/1')
        assert_equal(response.data['amended_versions'], [{
            'id': 2,
            'expression_date': '2011-01-01',
            'published_url': 'http://testserver/api/za/act/2010/1/eng@2011-01-01',
        }, {
            'id': 3,
            'expression_date': '2012-02-02',
            'published_url': 'http://testserver/api/za/act/2010/1/eng@2012-02-02',
        }])

    def test_published_repealed(self):
        response = self.client.get('/api/za/act/2001/8/eng.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')
        assert_equal(response.data['repeal'], {
            'date': '2014-02-12',
            'repealing_uri': '/za/act/2014/10',
            'repealing_title': 'Repeal',
            'repealing_id': 1,
        })

    def test_published_alternate_links(self):
        response = self.client.get('/api/za/act/2001/8/eng.json')
        assert_equal(response.status_code, 200)
        assert_equal(response.accepted_media_type, 'application/json')

        links = response.data['links']
        links.sort(key=lambda k: k['title'])

        assert_equal(links, [
            {'href': 'http://testserver/api/za/act/2001/8/eng.xml', 'mediaType': 'application/xml', 'rel': 'alternate', 'title': 'Akoma Ntoso'},
            {'href': 'http://testserver/api/za/act/2001/8/eng.html', 'mediaType': 'text/html', 'rel': 'alternate', 'title': 'HTML'},
            {'href': 'http://testserver/api/za/act/2001/8/eng.pdf', 'mediaType': 'application/pdf', 'rel': 'alternate', 'title': 'PDF'},
            {'href': 'http://testserver/api/za/act/2001/8/eng.html?standalone=1', 'mediaType': 'text/html', 'rel': 'alternate', 'title': 'Standalone HTML'},
            {'href': 'http://testserver/api/za/act/2001/8/eng/toc.json', 'mediaType': 'application/json', 'rel': 'alternate', 'title': 'Table of Contents'},
            {'href': 'http://testserver/api/za/act/2001/8/eng.epub', 'mediaType': 'application/epub+zip', 'rel': 'alternate', 'title': 'ePUB'},
        ])
