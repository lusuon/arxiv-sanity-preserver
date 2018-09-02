"""
Queries arxiv API and downloads papers (the query is a parameter).
The script is intended to enrich an existing database pickle (by default db.p),
so this file will be loaded first, and then new results will be added to it.
"""

import os
import time
import pickle
import random
import argparse
import urllib.request
import feedparser

from utils import Config, safe_pickle_dump


#似乎用于重构传入的FeedParserDict，将其转化为简单的dict
def encode_feedparser_dict(d):
  """
  helper function to get rid of feedparser bs with a deep copy.
  I hate when libs wrap simple things in their own classes.

  """
  if isinstance(d, feedparser.FeedParserDict) or isinstance(d, dict):  #如果传入对象为feedparser.FeedParserDict类或dict
    j = {}
    for k in d.keys():#遍历传入对象的键，构造新的dict
      j[k] = encode_feedparser_dict(d[k])
    return j
  elif isinstance(d, list):
    l = []
    for k in d:
      l.append(encode_feedparser_dict(k))
    return l
  else:
    return d
#自网址提取raw id 和版本
def parse_arxiv_url(url):
  """ 
  examples is http://arxiv.org/abs/1512.08756v2
  we want to extract the raw id and the version

  """
  ix = url.rfind('/')#自右开始查找最后一个'/'所在索引
  idversion = url[ix+1:] # extract just the id (and the version)
  parts = idversion.split('v')
  assert len(parts) == 2, 'error parsing url ' + url #如果分割后长度不为2，必定有错，抛出异常
  return parts[0], int(parts[1])

if __name__ == "__main__":

  # --------------------------parse input arguments 给解析器配置参数——Step 1--------------------------
  parser = argparse.ArgumentParser()
  parser.add_argument('--search-query', type=str,
                      default='cat:cs.CV+OR+cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.NE+OR+cat:stat.ML',
                      help='query used for arxiv API. See http://arxiv.org/help/api/user-manual#detailed_examples')
  parser.add_argument('--start-index', type=int, default=5900, help='0 = most recent API result')
  parser.add_argument('--max-index', type=int, default=10000, help='upper bound on paper index we will fetch')
  parser.add_argument('--results-per-iteration', type=int, default=100, help='passed to arxiv API')
  parser.add_argument('--wait-time', type=float, default=5.0, help='lets be gentle to arxiv API (in number of seconds)')
  parser.add_argument('--break-on-no-added', type=int, default=1, help='break out early if all returned query papers are already in db? 1=yes, 0=no')
  args = parser.parse_args()

  # --------------------------misc hardcoded variables 硬编码的变量——Step 2--------------------------
  base_url = 'http://export.arxiv.org/api/query?' # base api query url
  print('Searching arXiv for %s' % (args.search_query, ))

  # --------------------------lets load the existing database to memory 从数据库载入pickle文件到内存中的list：db——Step 3--------------------------
  try:
    db = pickle.load(open(Config.db_path, 'rb'))
  except Exception as e:
    print('error loading existing database:')
    print(e)
    print('starting from an empty database')
    db = {}

  # --------------------------main loop where we fetch the new results 获取新结果的主循环——Step 4--------------------------
  print('database has %d entries at start' % (len(db), ))
  num_added_total = 0


  for i in range(args.start_index, args.max_index, args.results_per_iteration):

    print("Results %i - %i" % (i,i+args.results_per_iteration))
    query = 'search_query=%s&sortBy=lastUpdatedDate&start=%i&max_results=%i' % (args.search_query,
                                                         i, args.results_per_iteration)
    #构造查询url，读取内容后传给parser解析
    with urllib.request.urlopen(base_url+query) as url:
      response = url.read()
    parse = feedparser.parse(response)
    num_added = 0
    num_skipped = 0

    # 尝试不中断，残忍点的话可以尝试30s或15s
    while len(parse.entries) == 0:
        print('Seems we got limited,let\'s wait for a minute,then try to retrive again.')
        time.sleep(60)
        print("Let\'s go!")
        with urllib.request.urlopen(base_url + query) as url:
          response = url.read()
        parse = feedparser.parse(response)

    #遍历解析结果
    for e in parse.entries:
    #j似乎是个论文对象
      j = encode_feedparser_dict(e) #对遍历过程中的对象简化处理

      # extract just the raw arxiv id and version for this paper
      rawid, version = parse_arxiv_url(j['id'])#该函数返回两个值
      j['_rawid'] = rawid
      j['_version'] = version

      # add to our database if we didn't have it before, or if this is a new version 新论文/新版本，则加入数据库
      if not rawid in db or j['_version'] > db[rawid]['_version']:
        db[rawid] = j
        print('Updated %s added %s' % (j['updated'].encode('utf-8'), j['title'].encode('utf-8')))
        num_added += 1
        num_added_total += 1
      else:
        num_skipped += 1

    #--------------------------抓取主循环结束，输出统计数据 Step 5--------------------------


    # print some information
    print('Added %d papers, already had %d.' % (num_added, num_skipped))


    #抓取受限时，能否考虑等待一定时间继续？
    '''
    if len(parse.entries) == 0:
      #原程序为直接终止
      print('Received no results from arxiv. Rate limiting? Exiting. Restart later maybe.')
      print(response)
      break
     '''

    if num_added == 0 and args.break_on_no_added == 1:
      print('No new papers were added. Assuming no new papers exist. Exiting.')
      break

    print('Sleeping for %i seconds' % (args.wait_time , ))
    time.sleep(args.wait_time + random.uniform(0, 3))

  # save the database before we quit, if we found anything new
  if num_added_total > 0:
    print('Saving database with %d papers to %s' % (len(db), Config.db_path))
    safe_pickle_dump(db, Config.db_path) #导出到外置存储

