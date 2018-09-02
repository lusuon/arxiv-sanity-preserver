import pickle
import pymysql
import traceback


pkl_file = open('db.p', 'rb')
data = pickle.load(pkl_file)
error = 0
success = 0
# 打开数据库连接
db = pymysql.connect('localhost','root','qpalzm','paper_data')
db.set_charset('utf8mb4')
cursor = db.cursor()
cursor.execute('alter table test_design convert to character set utf8mb4;') #避免一堆小语种人名无法插入，你也可以在workbench更改


def transferContent(content):
    if content is None:
        return None
    else:
        string = ""
        for c in content:
            if c == '"':
                string += '\\\"'
            elif c == "'":
                string += "\\\'"
            elif c == "\\":
                string += "\\\\"
            else:
                string += c
        return string

# insert the info
for key, value in data.items():
    authors = ''
    id = value['_rawid']
    version = value['_version']
    link = value['link']
    title =value['title']
    updated = value['updated']
    published = value['published']
    tag = value['tags'][0]['term']
    pdf_link = value['links'][1]['href'].replace('abs','pdf')
    for i in value['authors']:
        authors += i['name']
    authors =authors[:-1]

    # 使用cursor()方法获取操作游标

    #print("INSERT INTO test_design values (%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (id, version, link, title, updated, published, tag, pdf_link, authors))

    try:
        # 执行sql语句
        cursor.execute("INSERT IGNORE INTO test_design values ('%s','%s','%s','%s','%s','%s','%s','%s','%s')"%(id,version,link,transferContent(title),updated,published,tag,pdf_link,transferContent(authors)))
        # 提交到数据库执行
        db.commit()
        success+=1
        print("success:"+str(success))
    except:
        # 如果发生错误则回滚
        db.rollback()
        traceback.print_exc()
        print("INSERT INTO test_design values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"%(id,version,link,transferContent(title),updated,published,tag,pdf_link,transferContent(authors)))
        error +=1

# 关闭数据库连接
db.close()
print('errors:',error)

#5th:186






