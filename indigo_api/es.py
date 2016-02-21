# ElasticSearch support routines
from django.http import JsonResponse
from django.conf import settings

from elasticsearch import Elasticsearch


def search_view(request):
    # TODO: cross origin

    es = Elasticsearch(settings.ELASTICSEARCH_URL)

    q = (request.GET.get('q') or '').strip()
    region_name = request.GET.get('region_name')
    try:
        from_i = int(request.GET.get('from') or '0')
    except ValueError:
        from_i = 0
    try:
        size = int(request.GET.get('size') or '10')
    except ValueError:
        size = 10

    if q:
        filters = {}
        if region_name:
            filters = {'term': {'region_name': region_name}}

        # We do two queries, one is a general term query across the fields,
        # the other is a phrase query. At the very least, items *must*
        # match the term search, and items are preferred if they
        # also match the phrase search.
        query = {
            'bool': {
                'must': {
                    # best across all the fields
                    'multi_match': {
                        'query': q,
                        'type': 'best_fields',
                        'fields': ['title', 'content'],
                        # this helps skip stopwords, see
                        # http://www.elasticsearch.org/blog/stop-stopping-stop-words-a-look-at-common-terms-query/
                        'cutoff_frequency': 0.0007,
                        'operator': 'and',
                    },
                },
                'should': {
                    # try to match to a phrase
                    'multi_match': {
                        'query': q,
                        'fields': ['title', 'content'],
                        'type': 'phrase',
                    },
                },
            }
        }

        results = es.search(
            index=settings.ELASTICSEARCH_INDEX,
            body={
                'query': query,
                'fields': ['frbr_uri', 'repealed', 'published_on', 'title', 'url', 'region_name', 'region'],
                'from': from_i,
                'size': size,
                'sort': {'_score': {'order': 'desc'}},
                # filter after searching so filtering doesn't impact aggs
                'post_filter': filters,
                # count by region name
                'aggs': {'region_names': {'terms': {'field': 'region_name'}}},
                'highlight': {
                    'pre_tags': ['<mark>'],
                    'post_tags': ['</mark>'],
                    'order': "score",
                    'no_match_size': 0,
                    'fields': {
                        'content': {
                            'number_of_fragments': 1,
                        },
                        'title': {
                            'number_of_fragments': 0,  # entire field
                        }
                    },
                },
            })
    else:
        results = {
            'hits': {'total': 0},
            'took': 0,
        }

    return JsonResponse(results)
