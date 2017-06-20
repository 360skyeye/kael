# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
import sys


def patch_flask_route(bl=None):
    def _route(self, rule, **options):
        def decorator(f, rule=rule):
            versions = options.pop('versions', None)
            if not versions:
                versions = [1]
            endpoint = options.pop("endpoint", f.__name__)

            # blueprint = self.name.rsplit('.', 1)[1]
            # mapping_endpoint = 'mapping_%s' % endpoint
            # if mapping_endpoint not in _mapping_view_cache:
            #     _mapping_view_cache[mapping_endpoint] = lambda: get_mapping(blueprint, endpoint)

            for v in versions:
                v_rule = '/v%d%s' % (v, rule)
                self.add_url_rule(v_rule, endpoint, f, **options)
                # if rule.endswith('/'):
                #     v_mapping_rule = '/v%d%s_mapping' % (v, rule)
                # else:
                #     v_mapping_rule = '/v%d%s/_mapping' % (v, rule)
                # options['methods'] = ['GET']
                # self.add_url_rule(v_mapping_rule, 'mapping_%s' % endpoint,
                #                   _mapping_view_cache[mapping_endpoint], **options)
            return f

        return decorator

    if bl:
        bl.__class__.route = _route
    else:
        sys.modules['flask'].Flask.route = _route
        sys.modules['flask'].Blueprint.route = _route
