import cv2
import unittest
from crawler import Crawler


class OneRecordTest(unittest.TestCase):
  def setUp(self):
    #self.browser = webdriver.Chrome()
    self.crawler = Crawler()
    pass

  def setDown(self):
    #self.browser.quit()
    pass

  def test_find_records(self):
    # 開啟瀏覽器
    self.crawler.open_browser()    
    # 讀取第一筆清單上的名稱  list.csv
    records = self.crawler.get_records("./list.csv")
    self.assertEqual(len(records),2)
    # 讀取最後一筆已經比對成功的名單 list_success.csv
    # 找出接下來要進行的清單
    # 迴圈開始
    # 拉出第一筆
    # 填入姓名
    # 抓出驗證碼圖檔
    # 透過Google API 便是圖形驗證碼
    # 填入圖形驗證碼
    # 抓出所有連結
    # 掃過所有連結
    # 比對職業縣市,姓名,性別
    # 寫出檔案
    # 看看是否還有其他內容
    # 如果沒有，結束流程

if __name__ == "__main__":
  unittest.main()

