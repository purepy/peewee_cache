#!/usr/bin/env python
# coding=utf-8
import peewee_cache
import unittest
import peewee
from redis import StrictRedis
from peewee_cache.base import RedisCacheModel, CachePostgresqlExtDatabase, CacheModel
from peewee_cache.utils.log import logger

__author__ = 'chenfengyuan'
assert peewee_cache


class TestStringMethods(unittest.TestCase):
    def test_simple_select(self):
        db = CachePostgresqlExtDatabase("postgres", register_hstore=False)

        class _CacheModel(RedisCacheModel):
            class Meta(object):
                database = db

        class User(_CacheModel):
            username = peewee.CharField(unique=True, index=True)

        RedisCacheModel.initialize(StrictRedis())
        db.drop_tables([User], True)
        db.create_tables([User])
        with db.transaction():
            obj = User.create(username='a')
        obj.flush_cache()
        obj = User.get_by_pk(1)
        logger.debug(obj._is_from_cache)
        self.assertEqual(obj.username, 'a')
        with db.transaction():
            obj = User.get_by_pk(1)
            self.assertEqual(obj.username, 'a')
            obj.username = 'b'
            obj.save()
        obj = User.get_by_pk(1)
        self.assertEqual(obj.username, 'b')
        obj.username = 'z'
        id_ = User.select(User.id).where(User.username == 'b').scalar()
        self.assertEqual(id_, 1)
        with db.transaction():
            obj.delete_instance()
        with self.assertRaises(User.DoesNotExist):
            User.get_by_pk(1)


if __name__ == '__main__':
    unittest.main()
