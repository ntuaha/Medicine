from selenium import webdriver
import os
from  PIL import Image 
from io import BytesIO
import numpy as np
import cv2
import base64

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import pprint
import httplib2

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
    crop_img = numpy_array[loc['y']:loc['y']+40,loc['x']:loc['x']+88] 
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

  def extract_links(self,key):   
    input_code = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_TextBox1")
    input_code.send_keys(key)
    summit = self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btSEARCH")
    summit.click()
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

  def get_records(self,file_path):
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

  def run(self):
    self.open_browser()
    records = self.get_records("./list.csv")
    with open('./medicine.csv','w+') as f:
      f.write(",".join(["姓名","性別","證書類別","專科資格","執業登記科別","執登類別","職業縣市","連結","原來姓名","原來縣市","原來職業"])+"\n")

    for record in records:    
      print(record[0])
      print(record[1])
      print(record[2])      
      while 1:
        self.go_main_page()
        self.input_username(record[0])
        img = self.extract_chapcha()
        img_base64 = self.img_numpy_to_base64(img)
        key = self.read_chapcha_text(img_base64)
        print("key:%s"%key)
        try:
          links = self.extract_links(key)
        except selenium.common.exceptions.UnexpectedAlertPresentException:
          cv2.imshow("cropped",img)
          cv2.imwrite('./gg.png',img)
          print("QRcode解讀錯誤")
          continue
        #寫出統計量寫出所有可能  
        with open('./medicine.csv','a+') as f:    
          for link in links:
            print("link:%s"%link)
            data = self.getUserInfo(link)
            data.append(record[0])
            data.append(record[1])
            data.append(record[2])
            f.write(",".join(data)+"\n")
        #寫出統計量
        with open('./stat_medicine.csv','a+') as f:
          data = []
          data.append(record[0])
          data.append(record[1])
          data.append(record[2])
          data.append(str(len(links)))
          f.write(",".join(data)+"\n")
        break

if __name__ == "__main__":
  crawler = Crawler()
  crawler.run()


