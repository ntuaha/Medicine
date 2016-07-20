from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException
import os
from  PIL import Image 
from io import BytesIO
import numpy as np
import cv2
import base64
import xlrd
import xlsxwriter as xw
import time

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import pprint
import httplib2
import re

class Crawler:
  def __init__(self):
    self.open_browser()
    self.set_google_vis_tool()

  def open_browser(self):
    self.browser = webdriver.Chrome()

  def go_main_page(self):
    href = "https://ma.mohw.gov.tw/masearch/SearchDOC-101-1.aspx"
    self.browser.get(href)
 
  def input_username(self,name):
    input_name = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_txtDOC_NAME")    
    input_name.send_keys(name)

  def extract_chapcha(self):
    #https://stackoverflow.com/questions/25584677/selenium-webdriver-screenshot-as-numpy-array-python
    #儲存全景
    data = self.browser.get_screenshot_as_png()
    #讀入全景
    full_screen = Image.open(BytesIO(data))
    numpy_array = np.asarray(full_screen)
    #找出目標物件
    chapcha = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_ImageCheck")
    #取出目標物件位置
    loc = chapcha.location
    # NOTE: its img[y: y + h, x: x + w]
    # 剪下 寬88 高40 
    # retina上跑要*2
    t = 2
    crop_img = numpy_array[loc['y']*t:loc['y']*t+40*t,loc['x']*t:loc['x']*t+88*t] 
    #cv2.imwrite('crop.png',crop_img)
    return crop_img
  
  def img_numpy_to_base64(self,crop_img):
    #https://stackoverflow.com/questions/31826335/how-to-convert-pil-image-image-object-to-base64-string
    #png file is from numpy array to base64
    im = Image.fromarray(crop_img)
    buffer = BytesIO()
    im.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue())
    return img_base64


  def img_base64_to_png(self,img_str,filenpath='accept.png'):
    im2 = Image.open(BytesIO(base64.b64decode(img_str)))
    im2.save(filepath, 'PNG')

  def set_google_vis_tool(self):
    # The url template to retrieve the discovery document for trusted testers.
    DISCOVERY_URL='https://{api}.googleapis.com/$discovery/rest?version={apiVersion}'
    credentials = GoogleCredentials.get_application_default()
    self.service = discovery.build('vision', 'v1', credentials=credentials,discoveryServiceUrl=DISCOVERY_URL)
  
  def read_chapcha_text(self,img_base64):
    img1 = {}
    img1['image'] = {'content':img_base64.decode('utf-8')}
    img1['features'] = [{"type":"TEXT_DETECTION",'maxResults':10}]
    data={}
    data['requests'] = [img1]
    service_request = self.service.images().annotate(body=data)
    response = service_request.execute()
    key = response['responses'][0]['textAnnotations'][0]['description'].strip()
    # remove 所有空白
    return key.replace(" ","")
    #pprint.pprint(response)

  def input_key(self,key):
    #輸入驗證碼   
    input_code = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_TextBox1")
    input_code.send_keys(key)
    summit = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btSEARCH")
    summit.click()

  def extract_links(self):          
    b = self.browser.find_elements_by_xpath("//*[@id='ctl00_ContentPlaceHolder1_gviewMain']//tr//a")
    links = [i.get_attribute('href') for i in b[2:]]
    return links
    
  
  
  def getUserInfo(self,link):
    self.browser.get(link)
    #姓名
    name = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Name").text
    #性別
    sex = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Sex").text
    #證書類別
    ref = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Ref").text
    #專科資格
    spc = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Spc").text
    #執業登記科別
    dep = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Dep").text
    #執登類別
    pro = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Pro").text
    #執業縣市
    basaddr = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Basaddr").text
    return [name,sex,ref,spc,dep,pro,basaddr,link]

  def get_records_with_plain(self,file_path):
    records = []
    with open(file_path,'r') as f:
      i=0
      for line in f.readlines():
        i = i + 1        
        if i==1:
          continue
        else:
          records.append(line.strip().split(","))
    return records

  def get_records_with_xlsx(self,file_path):
    records = []
    file = xlrd.open_workbook(file_path)
    sheet = file.sheets()[0]
    nrows = sheet.nrows
    for n in range(1,sheet.nrows):
      data = [sheet.cell(n,i).value for i in range(3)]
      records.append(data)
    return records
  
  def initiaze_output_file(self,file_path):
    file = xw.Workbook(file_path)
    sheet = file.add_worksheet()
    header = ["姓名","性別","證書類別","專科資格","執業登記科別","執登類別","職業縣市","連結","原來序號","原來姓名","原來性別","可能是"]
    for i in range(len(header)):
      sheet.write(0,i,header[i])
    file.close()

  def initiaze_output_file_plain(self,file_path):
    with open(file_path,"w+") as f:
      header = ["姓名","性別","證書類別","專科資格","執業登記科別","執登類別","職業縣市","連結","原來序號","原來姓名","原來性別","可能是"]
      f.write(",".join(header)+"\n")
    

  def run(self):
    #self.open_browser()
    records = self.get_records_with_xlsx("./1.xlsx")
    #records = [records[302],records[775]]
    mutiple_list = [52, 103, 159, 166, 207, 223, 233, 254, 296, 432, 525, 534, 629, 644, 708, 749, 787, 847, 919, 927, 998, 1023, 1034, 1040, 1043, 1059, 1155, 1209, 1318, 1391, 1458, 1488, 1501, 1516, 1552, 1565, 1573, 1661, 1729, 1731, 1736, 1770, 1839, 1843, 1845, 1846, 1902, 1903, 1922, 1934, 1943, 1987, 1995, 1999, 2058, 2118, 2122, 2160, 2255, 2265, 2270, 2291, 2300, 2301, 2310, 2361, 2410, 2443, 2480, 2568, 2578, 2583, 2603, 2639, 2644, 2665, 2674, 2760, 2799, 2822, 2901, 2939]
    #records = [records[0],records[51],records[103]]
    r = []
    for m in mutiple_list:
      r.append(records[m-1])
    records = r
    self.initiaze_output_file_plain("./medicine.csv")

    for record in records:    
      [index,name,gender] = record
      index = int(index)
      print(index)
      print(name)
      print(gender)      
      while 1:
        self.go_main_page()
        self.input_username(name)
        img = self.extract_chapcha()
        img_base64 = self.img_numpy_to_base64(img)
        key = self.read_chapcha_text(img_base64)
        print("key:%s"%key)
        try:
          self.input_key(key)
          links = []
          ls = self.extract_links()
          if len(ls)>0:
            links.extend(ls)
            count_links = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_NetPager1_lblPageCount").text
            count_links = int(re.search("(\d+)",count_links).group(0))
            index_links = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_NetPager1_lblCurrentIndex").text
            index_links = int(re.search("(\d+)",index_links).group(0))            
            while  index_links < count_links :
              self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_NetPager1_lnkbtnNext").click()
              ls = self.extract_links()
              links.extend(ls)
              count_links = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_NetPager1_lblPageCount").text
              count_links = int(re.search("(\d+)",count_links).group(0))
              index_links = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_NetPager1_lblCurrentIndex").text
              index_links = int(re.search("(\d+)",index_links).group(0))
          print("# of links %d"%len(links))

        except UnexpectedAlertPresentException:
          cv2.imshow("cropped",img)
          cv2.imwrite('./gg.png',img)
          self.browser.quit()
          self.open_browser()
          print("QRcode解讀錯誤")
          time.sleep(2)
          continue
        #寫出統計量寫出所有可能  
        count = 0
        with open('./medicine.csv','a+') as f:    
          for link in links:
            print("link:%s"%link)
            data = self.getUserInfo(link)
            data.append(str(index))
            data.append(name)
            data.append(gender)
            #轉換性別
            if data[1]=="男":
              data[1] = "M"
            elif data[1] == "女":
              data[1] = "F"
            #判斷真偽
            if gender == data[1] and data[0] == name:
              data.append("Y") 
              count = count + 1
            else:
              data.append("F")
            f.write(",".join(data)+"\n")      
            f.flush()      
        #寫出統計量
        #寫出資料
        with open("./stat_medicine.csv","a+") as f:                
          f.write(",".join([str(index),name,gender,str(count)])+"\n")
        
        break
      
      
if __name__ == "__main__":
  crawler = Crawler()
  crawler.run()


