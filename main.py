from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
import argparse
import requests
import time


parser = argparse.ArgumentParser()
parser.add_argument('-n', '--nro', help="Ingrese numero a consultar"
)
args = parser.parse_args()

driver = webdriver.Chrome()

url = 'https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp'

# Cargar 
driver.get(url)



element  = driver.find_element(By.ID, "txtRuc")
element.send_keys(args.nro)
button =driver.find_element(By.ID, "btnAceptar")
button.send_keys(Keys.RETURN)




time.sleep(5)

driver.quit()