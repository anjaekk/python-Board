import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import random

# 몽고DB
client = MongoClient(host="localhost", port=27017)
# myweb 데이터베이스
db = client.myweb
# board 컬렉션
col = db.board

# 구글 검색시 헤더값을 설저하지 않으면 브라우저에서 보이는것과 다른 결과가 나옴
header = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"}
# 검색 결과의 5페이지까지만 수집
for i in range(6):
      # 구글 검색 URL, 검색어는 파이썬
      url = "https://www.google.com/search?q={}&start={}".format("파이썬", i * 10)
      # url 접속
      r = requests.get(url, headers=header)
      # 웹페이지의 검색 결과를 파싱하기 위한 준비, lxml라이브러리 사용
      bs = BeautifulSoup(r.text, "lxml")
      # 검색 결과는 div 태그의 g 클래스 단위로 반복됨
      lists = bs.select("div.g")

      for l in lists:
            # 게시물 작성시간 기록을 위해 현재시간 저장 (utc 타임)
            current_utc_time = round(datetime.utcnow().timestamp() * 1000)
            try:
                # 검색 결과의 제목은 h3 태그의 LC20lb.DKV0Md 클래스에 있음
                title = l.select_one("h3.LC20lb.DKV0Md").text
                # 검색결과의 요약내용은 div 태그의 IsZvec 클래스에 있음
                contents = l.select_one("div.IsZvec").text
                col.insert_one({
                    "name": "테스트",
                    "title": title,
                    "contents": contents,
                    "view": 0,
                    "pubdate": current_utc_time
                    })
            except:
                pass

            