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



browser = webdriver.Chrome()
href = "https://ma.mohw.gov.tw/masearch/SearchDOC-101-1.aspx"
browser.get(href)

input_name = browser.find_element_by_id("ctl00_ContentPlaceHolder1_txtDOC_NAME")

name = "康巧"
input_name.send_keys(name)

#a = browser.find_element_by_id("ctl00_ContentPlaceHolder1_ImageCheck").get_attribute('src')

#https://stackoverflow.com/questions/25584677/selenium-webdriver-screenshot-as-numpy-array-python
data = browser.get_screenshot_as_png()
img = Image.open(BytesIO(data))
numpy_array = np.asarray(img)


img = browser.find_element_by_id("ctl00_ContentPlaceHolder1_ImageCheck")
loc = img.location
# NOTE: its img[y: y + h, x: x + w] 
crop_img = numpy_array[loc['y']:loc['y']+40,loc['x']:loc['x']+80] 
cv2.imwrite('crop.png',crop_img)

#https://stackoverflow.com/questions/31826335/how-to-convert-pil-image-image-object-to-base64-string
#png file is from numpy array to base64
im = Image.fromarray(crop_img)
buffer = BytesIO()
im.save(buffer, format="PNG")
img_str = base64.b64encode(buffer.getvalue())


def recovery(img_str):
  im2 = Image.open(BytesIO(base64.b64decode(img_str)))
  im2.save('accept.png', 'PNG')

#recovery(img_str)

#import argparse


# The url template to retrieve the discovery document for trusted testers.
DISCOVERY_URL='https://{api}.googleapis.com/$discovery/rest?version={apiVersion}'
credentials = GoogleCredentials.get_application_default()
service = discovery.build('vision', 'v1', credentials=credentials,discoveryServiceUrl=DISCOVERY_URL)

img1 = {}
img1['image'] = {'content':img_str.decode('utf-8')}
img1['features'] = [{"type":"TEXT_DETECTION",'maxResults':10}]
data={}
data['requests'] = [img1]
service_request = service.images().annotate(body=data)
response = service_request.execute()


pprint.pprint(response)
key = response['responses'][0]['textAnnotations'][0]['description'].strip()
input_code = browser.find_element_by_id("ctl00_ContentPlaceHolder1_TextBox1")
input_code.send_keys(key)
summit = browser.find_element_by_id("ctl00_ContentPlaceHolder1_btSEARCH")
summit.click()

b = browser.find_elements_by_xpath("//*[@id='ctl00_ContentPlaceHolder1_gviewMain']//tr//a")
links = [i.get_attribute('href') for i in b[2:]]
for link in links:
  pass

#def
browser.get("https://ma.mohw.gov.tw/masearch/SearchDOC-101-2.aspx?DOC_SEQ=6D26B73ED8C56A82")
#link = links[0]
with open('./medicine.csv','a+') as f:
  f.write(",".join(["姓名","性別","證書類別","專科資格","執業登記科別","執登類別","職業縣市"])+"\n")

for link in links:  
  browser.get(link)
  print(link)
  #姓名
  name = browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Name").text
  #性別
  sex = browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Sex").text
  #證書類別
  ref = browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Ref").text
  #專科資格
  spc = browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Spc").text
  #執業登記科別
  dep = browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Dep").text
  #執登類別
  pro = browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Pro").text
  #執業縣市
  basaddr = browser.find_element_by_id("ctl00_ContentPlaceHolder1_lblDoc_Basaddr").text
  with open('./medicine.csv','a+') as f:
    f.write(",".join([name,sex,ref,spc,dep,pro,basaddr])+"\n")  
    



def run():
  #儲存全景
  browser.save_screenshot('screenshot.png')
  #找出目標物件
  img = browser.find_element_by_id("ctl00_ContentPlaceHolder1_ImageCheck")
  #取出目標物件位置
  loc = img.location
  #讀入全景
  image = cv2.imread('screenshot.png')
  # y1:y2  x1:x2
  #剪下
  crop_img = image[loc['y']:loc['y']+40,loc['x']:loc['x']+80]
  #寫入
  cv2.imshow("cropped",crop_img)
  #寫出
  cv2.imwrite("crop.png",crop_img)





