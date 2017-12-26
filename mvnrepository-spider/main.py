#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import signal
from logging import handlers

from psycopg2.pool import SimpleConnectionPool
from redis import ConnectionPool, Redis

from maven import Artifact

LOG_FILE = 'test.log'

handler = handlers.RotatingFileHandler(LOG_FILE, maxBytes=1024 * 1024, backupCount=5)  # 实例化handler
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'

formatter = logging.Formatter(fmt)  # 实例化formatter
handler.setFormatter(formatter)  # 为handler添加formatter

logger = logging.getLogger('test')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

stop = False


def handle_stop(signum, frame):
    global stop
    stop = True
    logger.info('stop')


signal.signal(signal.SIGINT, handle_stop)
signal.signal(signal.SIGTERM, handle_stop)

redis_pool = ConnectionPool(max_connections=5, host='39.106.110.159', port=6379, db=0, password='enbug')

pg_pool = SimpleConnectionPool(
    3, 5, database='leaf', user='leaf', password='enbug', host='39.106.110.159', port='5432'
)


def get_next():
    r = Redis(connection_pool=redis_pool)
    return r.incr('current_index')


def read_db(index):
    conn = pg_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, group_id, artifact_id, version FROM m2_index WHERE id = %s', (index,))
            return cur.fetchone()
    finally:
        pg_pool.putconn(conn)


def fill_db(location, artifact):
    conn = pg_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO m2_package(index_id, name, description, home_page, license, organization, date) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (
                    location[0], artifact.name, artifact.description, artifact.home_page,
                    artifact.license, artifact.organization, artifact.date
                )
            )
            for dependency in artifact.dependencies:
                if dependency.scope == 'system' or dependency.version is None:
                    cur.execute(
                        'INSERT INTO m2_dependency(index_id, dependency_index_id, group_id, artifact_id, version) '
                        'VALUES (%s, %s, %s, %s, %s)',
                        (location[0], None, dependency.group_id, dependency.artifact_id, dependency.version)
                    )
                else:
                    cur.execute(
                        'SELECT id FROM m2_index WHERE group_id = %s AND artifact_id = %s AND version = %s',
                        (dependency.group_id, dependency.artifact_id, dependency.version)
                    )
                    d = cur.fetchone()
                    if d is None:
                        cur.execute(
                            'INSERT INTO m2_dependency(index_id, dependency_index_id, group_id, artifact_id, version) '
                            'VALUES (%s, %s, %s, %s, %s)',
                            (location[0], None, dependency.group_id, dependency.artifact_id, dependency.version)
                        )
                    else:
                        index_id = d[0]
                        cur.execute(
                            'INSERT INTO m2_dependency(index_id, dependency_index_id, group_id, artifact_id, version) '
                            'VALUES (%s, %s, %s, %s, %s)',
                            (location[0], index_id, None, None, None)
                        )
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        pg_pool.putconn(conn)


def start():
    global stop
    while not stop:
        location = read_db(get_next())
        if location is None:
            break
        try:
            artifact = Artifact(location[1:])
            fill_db(location, artifact)
        except BaseException as e:
            logger.error("%s\n%s\n\n", location, e, exc_info=1)


start()

redis_pool.disconnect()
pg_pool.closeall()
