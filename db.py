#!/usr/bin/env python
# encoding: utf-8

import sqlite3

# settings
db_name = 'cars.db'


def db_init():

    sql_drop_table = 'drop table if exists t_cars'
    sql_create_table = '''create table t_cars (series_id varchar(10), series_link varchar(40), series_name varchar(100), 
        official_config varchar(512), spec_id varchar(10), spec_link varchar(50))'''
    sql_insert = 'insert into t_cars values ("车系编号", "车系链接", "车系", "官方配置表", "车型编号", "车型链接")'

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        cursor.execute(sql_drop_table)
        cursor.execute(sql_create_table)
        cursor.execute(sql_insert)
        conn.commit()
    except sqlite3.Error as e:
        print('db_init error:' + e.args[0])
    finally:
        cursor.close()
        conn.rollback()
        conn.close()


def db_get_columns():

    sql_get_columns = 'select sql from sqlite_master where tbl_name = "t_cars" and type="table"'

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        cursor.execute(sql_get_columns)
        res = cursor.fetchone()
        if res:
            return res[0]
        else:
            return ''
    except sqlite3.Error as e:
        print('db_get_columns error:' + e.args[0])
    finally:
        cursor.close()
        conn.close()


def db_get_series_ids_done():

    sql_get_columns = "select distinct series_id from t_cars where rowid>1"

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        cursor.execute(sql_get_columns)
        res = cursor.fetchall()
        return [x[0] for x in res]
    except sqlite3.Error as e:
        print('db_get_columns error:' + e.args[0])
    finally:
        cursor.close()
        conn.close()


def db_add_columns(columns_todo):

    sql_alter_table = 'alter table t_cars add column %s varchar(100)'
    sql_update = 'update t_cars set %s = "%s" where rowid=1'

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        for one_column in columns_todo:
            cursor.execute(sql_alter_table % one_column[0])
            cursor.execute(sql_update % (one_column[0], one_column[1]))
        conn.commit()
    except sqlite3.Error as e:
        print('db_add_columns error:' + e.args[0])
    finally:
        cursor.close()
        conn.rollback()
        conn.close()


def db_insert(list_specs_columns, list_specs):
    sql_insert = 'insert into t_cars (%s) values ("%s")'
    sql = ''

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        for one_column, one_spec in zip(list_specs_columns, list_specs):
            sql_column = ','.join(one_column)
            sql_value = '","'.join(one_spec)
            sql = sql_insert % (sql_column, sql_value)
            cursor.execute(sql)
        conn.commit()
    except sqlite3.Error as e:
        print('db_insert error:' + e.args[0] + ',sql:' + sql)
    finally:
        cursor.close()
        conn.rollback()
        conn.close()


# 插入一条空记录 以便记录是否已处理该车型
def db_insert_nodata(series_id, series_link, series_name):
    sql_insert = 'insert into t_cars (series_id, series_link, series_name, item_567) values ("%s", "%s", "%s", "没有记录")'
    sql = ''

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    try:
        sql = sql_insert % (series_id, series_link, series_name)
        cursor.execute(sql)
        conn.commit()
    except sqlite3.Error as e:
        print('db_insert_nodata error:' + e.args[0] + ',sql:' + sql)
    finally:
        cursor.close()
        conn.rollback()
        conn.close()
