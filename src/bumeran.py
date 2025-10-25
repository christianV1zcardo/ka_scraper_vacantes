from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


class BumeranScraper:
    def __init__(self):
        self.driver = webdriver.Firefox()

    def abrir_pagina_empleos(self):
        self.driver.get("https://www.bumeran.com.pe/empleos-busqueda.html")

    # Errores aqui
    def escribir_vacante(self):
        placeholder_name = "react-select-4-input"
        elem = self.driver.find_element(By.ID, placeholder_name)
        elem.send_keys("TESTING")
        elem.send_keys(Keys.RETURN)

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = BumeranScraper()
    scraper.abrir_pagina_empleos()
    scraper.escribir_vacante()  
    # Add more scraping logic here
    #scraper.close()