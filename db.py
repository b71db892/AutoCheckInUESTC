from logger import logger
import sqlite3
import os


class DB:
    '''
    这是一个存储滑动验证码图片的数据库。所有图片以base64字符串形式存储。
    由于学工系统验证码图片数量很有限，该库已经收集了所有完整的验证图片。
    图片验证算法会自动把没见过的图片加入数据库。

    图片有三种：
            RAW_IMGS    :原始验证图片，一般尺寸：高*宽=360*590左右，大小不固定
            BLOCK_IMGS  :原始滑块图片，一般尺寸：高*宽=360*93左右，大小不固定
            COOKED_IMGS :经过算法拼合的验证图片，一般尺寸：高*宽=360*590左右，大小不固定
    拼合算法：
        很无脑，类似于不断试错。
    '''

    def __init__(self, db=os.path.join(os.path.split(os.path.realpath(__file__))[0], 'imgs.db')):
        # 连接到SQlite数据库
        # 数据库文件是test.db，不存在，则自动创建
        logger.info(f'DataBase 路径：{db}')
        self._conn = sqlite3.connect(db)
        self._conn.execute('pragma foreign_keys=on')
        self._cursor = self._conn.cursor()
        self._init_db()

    def _init_db(self):
        # 查询已有的表
        self._cursor.execute("select name from sqlite_master where type='table' order by name")
        r = self._cursor.fetchall()
        logger.info(f'DataBase Tables:{r}')
        # 此表存储了所有经过拼合的验证图片（不一定完整，一般需要若干张有缺口的图片才能拼合成一张完整的）
        # （此表是GroundTruth答案集合，请不要删除）
        COOKED_IMGS = '''CREATE TABLE COOKED_IMGS
                                    (ID            INTEGER PRIMARY KEY AUTOINCREMENT,
                                    MD5            CHAR(50)            NOT NULL UNIQUE,
                                    BASE64         TEXT                NOT NULL,
                                    WIN_START      INTEGER             NOT NULL,
                                    WIN_END        INTEGER             NOT NULL);'''

        # 此表存储了所有没有经过拼合的原始验证图片（若数据库占用空间过大，可删除此表）
        RAW_IMGS = '''CREATE TABLE RAW_IMGS
                                    (ID            INTEGER PRIMARY KEY AUTOINCREMENT,
                                    MD5            CHAR(50)            NOT NULL UNIQUE,
                                    BASE64         TEXT                NOT NULL,
                                    WIN_START      INTEGER             NOT NULL,
                                    WIN_END        INTEGER             NOT NULL,
                                    COOKED_IMG_ID  INTEGER             REFERENCES COOKED_IMGS(ID) 
                                                                       ON UPDATE CASCADE
                                                                       ON DELETE SET NULL);'''

        # 此表存储了所有滑动块的原始图片（若数据库占用空间过大，可删除此表）
        BLOCK_IMGS = '''CREATE TABLE BLOCK_IMGS
                                    (ID                INTEGER PRIMARY KEY AUTOINCREMENT,
                                    MD5                CHAR(50)            NOT NULL UNIQUE,
                                    BASE64             TEXT                NOT NULL,
                                    RAW_IMG_ID         INTEGER             REFERENCES RAW_IMGS(ID) 
                                                                           ON UPDATE CASCADE
                                                                           ON DELETE SET NULL);'''

        def check_table(table_name, comm=None):
            if tuple([table_name, ]) in r:
                logger.info(f"{table_name} exists.")
            else:
                logger.info(f"create table {table_name}.")
                self._cursor.execute(comm)

        check_table('COOKED_IMGS', comm=COOKED_IMGS)
        check_table('RAW_IMGS', comm=RAW_IMGS)
        check_table('BLOCK_IMGS', comm=BLOCK_IMGS)

    def _select(self, table, columns: list):
        comm = f'SELECT {", ".join(["`" + c + "`" for c in columns])} FROM {table};'
        # print(comm)
        self._cursor.execute(comm)
        result = self._cursor.fetchall()
        # print(f'select {len(result)} imgs.')
        return result

    def save_raw_img(self, md5_str: str, base64_src: str, win: list, cooked_id: int):
        win_start, win_end = win
        if tuple([md5_str, ]) in self._select('RAW_IMGS', ['MD5']):
            print(f' duplicate!')
            return
        comm = f'insert into RAW_IMGS  (MD5, BASE64, WIN_START, WIN_END, COOKED_IMG_ID)' \
               f' values ("{str(md5_str)}", "{str(base64_src)}", {int(win_start)}, {int(win_end)}, {int(cooked_id)})'
        # print(comm)
        self._cursor.execute(comm)
        self._conn.commit()

    def save_cooked_img(self, md5_str: str, base64_src: str, win: list, ):
        win_start, win_end = win
        if tuple([md5_str, ]) in self._select('COOKED_IMGS', ['MD5']):
            print(f' duplicate!')
            return
        comm = f'insert into COOKED_IMGS  (MD5, BASE64, WIN_START, WIN_END)' \
               f' values ("{str(md5_str)}", "{str(base64_src)}", {int(win_start)}, {int(win_end)})'
        # print(comm)
        self._cursor.execute(comm)
        self._conn.commit()

    def save_block_img(self, md5_str: str, base64_src: str, raw_id: int):
        if tuple([md5_str, ]) in self._select('BLOCK_IMGS', ['MD5']):
            print(f' duplicate!')
            return
        comm = f'insert into BLOCK_IMGS  (MD5, BASE64, RAW_IMG_ID) ' \
               f'values ("{str(md5_str)}", "{str(base64_src)}", {int(raw_id)})'
        # print(comm)
        self._cursor.execute(comm)
        self._conn.commit()

    def update_cooked_img(self, id, md5_str, base64_src, win: list):
        # 如果算法拼合出一张【新的】验证图片（不一定完整，但比旧的图片更接近完整），需要存进数据库。
        comm = f'UPDATE COOKED_IMGS SET `MD5` = "{str(md5_str)}", `BASE64` = "{str(base64_src)}", ' \
               f'`WIN_START` = {int(win[0])}, `WIN_END` = {str(win[1])} WHERE `ID` = {int(id)};'
        # print(comm)
        self._cursor.execute(comm)
        print(f'update {self._cursor.rowcount} imgs')
        self._conn.commit()

    def close(self):
        try:
            # # 关闭Cursor:
            # self._cursor.close()
            # 提交事务：
            self._conn.commit()
            # 关闭connection：
            self._conn.close()
        except Exception as e:
            print("error when closing db.")

    def get_cooked_img_id(self, md5):
        return self._get_img_id('COOKED_IMGS', md5)

    def get_raw_img_id(self, md5):
        return self._get_img_id('RAW_IMGS', md5)

    def _get_img_id(self, table, md5):
        comm = f'SELECT  ID  FROM  {table} WHERE MD5 = "{md5}";'
        # print(comm)
        self._cursor.execute(comm)
        result = self._cursor.fetchone()[0]
        # print(f' img id : {result}')
        return result

    def get_cooked_imgs(self):
        return self._select('COOKED_IMGS', ['ID', 'MD5', 'BASE64', 'WIN_START', 'WIN_END'])

    def get_raw_imgs(self):
        return self._select('RAW_IMGS', ['ID', 'MD5', 'BASE64', 'WIN_START', 'WIN_END', 'COOKED_IMG_ID'])

    def __del__(self):
        self.close()
