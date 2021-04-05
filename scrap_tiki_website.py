!pip install selenium
!apt install chromium-chromedriver
!cp /usr/lib/chromium-browser/chromedriver /usr/bin
!pip install webdriver-manager

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import json
import pandas as pd


# Set driver for Chrome
options = webdriver.ChromeOptions()
options.add_argument('-headless')
options.add_argument('-no-sandbox')
options.add_argument('-disable-dev-shm-usage')

#get data of 1 page
def selenium_scrap(tiki_url):
  driver = webdriver.Chrome('chromedriver',options=options)        # Define the chrome drivers with setting options we define above  
  driver.implicitly_wait(20)                                       # We let selenium to wait for 30 seconds for all javascript script done before return the result of HTML
                                     
  driver.get(tiki_url)                                             # Open the browser again to get web page
  html_data = driver.page_source                                   # After driver.get() is done, you can get back HTML string by using .page_source
  driver.close()                                                   # Close the driver after retrieving the web page
                                        
  soup = BeautifulSoup(html_data, 'html.parser')                   # Do your beautifulsoup business like the usual

  return soup

#scrap 1 page
def page_scrap(url):

  data = []
  soup = selenium_scrap(url)

  products = soup.find_all('a', {'class':'product-item'})
  script = None
  scripts_list = []

  while True: #check if page with no product
    if len(products) == 0:
      data.append('Stop')
      return data
    else:
      for ldjson in soup.find_all('script'):
        if '"@type":"Product"' in ldjson.text:
          script = json.loads(ldjson.text)
          scripts_list.append(script)

      i = 0
      for product in products:

        d = {'title':'' , 'price':'' , 'tikinow':'' , 'freeship':'' , 'reviews':'' , 'product_id':'' ,
            'link':'' , 'rating_value':'' , 'image url':'',
            'badge under price': '', 'discount percentage': '', 'installment':'', 'free gifts': ''}
        
        #product name
        d['title'] = product.find('div',{'class' : 'name'}).text

        #product price
        d['price'] = int(re.sub('[. ₫]','', product.find('div',{'class':'price-discount__price'}).text))

        #product id / sku
        d['product_id'] = scripts_list[i]['sku']

        #product url
        d['link'] = scripts_list[i]['url']

        #discount percentage #Chinh: get only number of discount
        try:
          d['dis_percentage'] = int(re.sub('[-%]','', product.find('div',{'class':'price-discount__discount'}).text))
        except:
          d['dis_percentage'] = 0
        
        #tikinow
        try:
          d['tikinow'] = product.find('div',{'class':'badge-service'}).img['src'].replace("https://salt.tikicdn.com/ts/upload/9f/32/dd/8a8d39d4453399569dfb3e80fe01de75.png","Yes")
        except:
          d['tikinow'] = 'No'

        #freeship
        try:
          if product.find('div',{'class':'badge-top'}).text == 'Freeship':
            d['freeship'] = 'Yes'
          else:
            d['freeship'] = 'No'
        except: 
          d['freeship'] = 'No'
        
        #reviews number
        try:
          d['reviews'] = int(re.sub('[()]','', product.find('div',{'class':'review'}).text))
        except:
          d['reviews'] = 0
        
        #rating value
        try:
          d['rating_value'] = int(scripts_list[i]['aggregateRating']['ratingValue'])
        except:
          d['rating_value'] = 0

        #Nhu part
        #img url
        try:
          d['image url'] = product.img['src'] 
        except:
          d['image url'] = 'No'

        # try:
        #   d['page url'] = product['href'] 
        # except:
        #   d['page url'] = 'No'

        #badge under price
        if product.find('img',{'src':'https://salt.tikicdn.com/ts/upload/51/ac/cc/528e80fe3f464f910174e2fdf8887b6f.png'}):
          d['badge under price'] = 'Yes'
        else: 
          d['badge under price'] = 'No'
        
        # Nhu: text discount percentage
        # try:
        #   d['discount percentage'] = product.find('div',{'class':'price-discount__discount'}).text[1:]
        # except:
        #   d['discount percentage'] = 0
        
        #installment
        if product.find('span', string = 'Trả góp'):
          d['installment'] = 'Yes'
        else:
          d['installment'] = 'No'

        #free gift
        if product.find('div',{'class':'gift-image-list'}):
          d['free gifts'] = 'Yes'
        else:
          d['free gifts'] = 'No'

        i+=1
        data.append(d)
        
      return data

#scrap many page
def web_scrap():
  data = ['Start']
  page = 1
  for page in range(1,15):
    tiki_urls = f'https://tiki.vn/dien-thoai-may-tinh-bang/c1789?page={page}&src=c.1789.hamburger_menu_fly_out_banner'
    if data[-1] == 'Stop':
      break
    else:
      data += page_scrap(tiki_urls)
    page += 1
  print(page)
  data.pop(-1)
  data.pop(0)
  return data


data = web_scrap()
products_dataframe = pd.DataFrame(data = data, columns = data[0].keys())

products_dataframe.to_pickle('./result.pkl')
products_dataframe.to_csv("./result.csv", index=False)

