# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/7
from kael import MQ
from uuid import uuid4
import yaml
import jsonschema
from validate import formatchecker


class Producer(MQ):
    def __init__(self, name, auri, channel="center"):
        super(Producer, self).__init__(channel=channel, extype="topic", auri=auri)
        self.id = "producer-{0}_{1}".format(name, str(uuid4()))
        self.schema = {}

    def pub(self, topic, data, schema_type=None, ttl=0):
        schema = self.schema.get(topic, {}).get(schema_type, {})
        if schema:
            try:
                jsonschema.validate(data, schema, format_checker=formatchecker, )
            except Exception, e:
                print "format erro", e
                return
            data = {"schema": schema, "data": data}
            self.push_msg(self.id, topic, data, ttl=ttl)

    def load_schema(self, file_path):
        f = open(file_path, "r")
        schema = yaml.load(f)
        f.close()
        self.schema.update(schema)
