# coding=utf-8
from peewee import Model, ModelOptions, Database, DoesNotExist
from playhouse.postgres_ext import PostgresqlExtDatabase
from .utils.log import logger
from redis import StrictRedis
import cPickle

ObjectDoesNotExist = object()


class DumyCacheClient(object):
    @staticmethod
    def set(key, value):
        del key, value

    @staticmethod
    def get(key):
        del key
        return ObjectDoesNotExist

    @staticmethod
    def flush(key):
        del key


class CacheModel(Model):

    @classmethod
    def create_or_get(cls, **kwargs):
        raise RuntimeError("CacheModel don't support create_or_get")

    @classmethod
    def get_or_create(cls, **kwargs):
        raise RuntimeError("CacheModel don't support get_or_create")

    @classmethod
    def create(cls, **query):
        logger.debug('creating')
        if cls.get_meta().database.transaction_depth() == 0:
            raise RuntimeError("create is only allowed in transaction")
        inst = super(CacheModel, cls).create(**query)
        return inst

    def cache_set(self):
        logger.debug('setting %s', self)
        self._cache_set(self.get_cache_key(), cPickle.dumps(self.to_dict()))

    @staticmethod
    def _cache_set(key, value):
        del key, value

    @staticmethod
    def _cache_get(key):
        del key

    @staticmethod
    def _cache_flush(key):
        del key

    def get_cache_key(self):
        primary_key_name = self.get_meta().primary_key.name
        primary_key = getattr(self, primary_key_name)
        return u'{}.{}|{}'.format(self.__class__.__module__, self.__class__.__name__, primary_key)

    @classmethod
    def get_cache_key_by_primary_key(cls, id_):
        return u'{}.{}|{}'.format(cls.__module__, cls.__name__, id_)

    @classmethod
    def get_meta(cls):
        """
        :rtype: ModelOptions
        """
        return getattr(cls, "_meta")

    def to_dict(self):
        return self._data

    @classmethod
    def from_dict(cls, dict_):
        return cls(**dict_)

    def __str__(self):
        try:
            tmp = [u"{}.{}".format(self.__class__.__module__, self.__class__.__name__), u"("]
            meta = getattr(self, "_meta")
            for i, k in enumerate(meta.sorted_field_names):
                v = getattr(self, k)
                if i == 0:
                    tmp.append(u'{}={}'.format(k, v))
                else:
                    tmp.append(u', {}={}'.format(k, v))
            tmp.append(u")")
            return u"".join(tmp)
        except:
            return super(CacheModel, self).__str__()

    @classmethod
    def get_from_db_by_pk(cls, pk):
        """
        :rtype: CacheModel
        """
        meta = getattr(cls, "_meta")
        rv = cls.select().where(getattr(cls, meta.primary_key.name) == pk).get()
        return rv

    @classmethod
    def get_from_cache_by_pk(cls, id_):
        logger.debug('getting %s %s', cls, id_)
        v = cls._cache_get(cls.get_cache_key_by_primary_key(id_))
        if v is not None:
            rv = cls.from_dict(cPickle.loads(v))
            rv._is_from_cache = True
            return rv
        rv = cls.get_from_db_by_pk(id_)
        rv._is_from_cache = True
        rv.cache_set()
        return rv

    @classmethod
    def get_by_pk(cls, pk):
        meta = getattr(cls, "_meta")
        logger.debug(meta.database.transaction_depth())
        if meta.database.transaction_depth() > 0:
            return cls.get_from_db_by_pk(pk)
        rv = cls.get_from_cache_by_pk(pk)
        return rv

    def flush_cache(self):
        key = self.get_cache_key()
        self._cache_flush(key)

    @classmethod
    def flush_cache_by_primary_key(cls, id_):
        key = cls.get_cache_key_by_primary_key(id_)
        cls._cache_flush(key)

    def save(self, force_insert=False, only=None):
        logger.debug("saving")
        if self.get_meta().database.transaction_depth() == 0:
            raise RuntimeError("save is only allowed in transaction")
        if hasattr(self, "_is_from_cache"):
            raise RuntimeError("can't save cached object")
        rv = super(CacheModel, self).save(force_insert, only)
        meta = getattr(self, "_meta")
        meta.database.refresh_object_sets.add((self.__class__, self.get_id()))
        return rv

    def delete_instance(self, recursive=False, delete_nullable=False):
        assert not recursive, "only support recursive == False"
        if self.get_meta().database.transaction_depth() == 0:
            raise RuntimeError("delete_instance is only allowed in transaction")
        meta = getattr(self, "_meta")
        meta.database.refresh_object_sets.add((self.__class__, self.get_id()))
        super(CacheModel, self).delete_instance(recursive, delete_nullable)


class RedisCacheModel(CacheModel):
    _RedisClient = None

    @classmethod
    def get_redis_client(cls):
        """
        :rtype: StrictRedis
        """
        return cls._RedisClient

    @classmethod
    def initialize(cls, redis_client):
        cls._RedisClient = redis_client

    @classmethod
    def _cache_set(cls, key, value):
        cls.get_redis_client().set(key, value)

    @classmethod
    def _cache_get(cls, key):
        return cls.get_redis_client().get(key)

    @classmethod
    def _cache_flush(cls, key):
        cls.get_redis_client().delete(key)


class CacheDatabaseMixin(Database):
    def __init__(self, *args, **kwargs):
        super(CacheDatabaseMixin, self).__init__(*args, **kwargs)
        self.refresh_object_sets = set()
        self.committing = False

    def commit(self):
        logger.debug("committing")
        super(CacheDatabaseMixin, self).commit()
        if self.committing:
            return
        try:
            self.committing = True
            logger.debug(self.refresh_object_sets)
            for cls, id_ in self.refresh_object_sets:
                logger.debug("update %s(%s) cache", cls, id_)
                assert issubclass(cls, CacheModel), cls
                try:
                    obj = cls.get_from_db_by_pk(id_)
                    obj.cache_set()
                except DoesNotExist:
                    cls.flush_cache_by_primary_key(id_)
            self.refresh_object_sets = set()
        finally:
            self.committing = False

    def rollback(self):
        self.refresh_object_sets = set()
        super(CacheDatabaseMixin, self).rollback()


class CachePostgresqlExtDatabase(CacheDatabaseMixin, PostgresqlExtDatabase):
    pass
