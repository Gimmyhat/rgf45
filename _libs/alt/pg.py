import psycopg2
import psycopg2.extras
import time
from alt.dict_ import dict_

class DB:

    def __init__(self, host='127.0.0.1', port=5432, user=None, pwd=None, db=None, n_try=1, schema='public'):

        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.db = db
        if schema!='public':
            schema = schema + ',public'
        self.schema = schema
        if n_try is None:
            try:
                __IPYTHON__
                n_try = 1
            except:
                n_try = 10
        self.n_try = n_try
        self.connect()

    def connect(self):

        # print('Connect')
        itry = 1
        while True:
            try:
                self.conn = psycopg2.connect(host=self.host, port=self.port, user=self.user,
                    password=self.pwd, database=self.db,
                    options='-c statement_timeout=30s -c search_path=%s' % self.schema)
                self.conn.autocommit = True
                break
            except (psycopg2.OperationalError, psycopg2.InterfaceError):
                if itry==self.n_try:
                    raise
                print('OperationalError', itry)
            itry += 1
            time.sleep(1)

    def sql(self, sql, params=None, return_id=None, return_one=False, debug=False):

        if not isinstance(params, (tuple, list, dict)):
            params = (params,)
        # print(sql, params)
        itry = 1
        while True:
            try:
                cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                if return_id:
                    if not sql.strip().lower().startswith('insert'):
                        raise Exception('return_id only for insert')
                    sql += ' RETURNING ' + return_id
                cur.execute(sql, params)
                if debug:
                    print(cur.mogrify(sql, params).decode('utf-8'))
                if sql.strip().lower().startswith('select'):
                    rows = [dict_(row) for row in cur.fetchall()]
                    if return_one:
                        if len(rows)==0:
                            return None
                        if len(rows)>1:
                            raise Exception('Return more than one')
                        return rows[0]
                    return rows
                if return_id:
                    return cur.fetchone()[0]
                break
            except (psycopg2.OperationalError, psycopg2.InterfaceError):
                if itry>=self.n_try:
                    raise
                print('OperationalError', itry)
                self.connect()
            itry += 1
            time.sleep(1)

    def insert(self, table, row, return_id=None):

        sql = "insert into %s (%s) values (%s)"
        fields, values, params = [], [], []
        for key, value in row.items():
            fields.append(key)
            values.append('%s')
            params.append(value)
        sql = sql % (table, ','.join(fields), ','.join(values))
        id = self.sql(sql, params, return_id=return_id)

        return id

    def update(self, table, row, row_id):

        sql = "update %s set (%s)=(%s) where " + row_id + "=%s"
        fields, values, params = [], [], []
        for key, value in row.items():
            fields.append(key)
            values.append('%s')
            params.append(value)
        sql = sql % (table, ','.join(fields), ','.join(values), row[row_id])
        self.sql(sql, params)
