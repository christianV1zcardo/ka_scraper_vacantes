from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


class BumeranScraper:
    def __init__(self):
        self.driver = webdriver.Firefox()

    def abrir_pagina_empleos(self, hoy: bool = False, dias: int = 0):
        
        # Mejorable y añadible mas condiciones
        if hoy:
            self.driver.get("https://www.bumeran.com.pe/empleos-publicacion-hoy.html")
        elif not hoy:
            if dias == 2:
                self.driver.get("https://www.bumeran.com.pe/empleos-publicacion-menor-a-2-dias.html")
            elif dias == 3:
                self.driver.get("https://www.bumeran.com.pe/empleos-publicacion-menor-a-3-dias.html")
            else:
                self.driver.get("https://www.bumeran.com.pe/empleos-busqueda.html")

    # Errores aqui
    def buscar_vacante(self, palabra_clave: str = ''):
        # El id del box de texto
        placeholder_name = "react-select-4-input"
        elem = self.driver.find_element(By.ID, placeholder_name)
        elem.send_keys(palabra_clave)
        elem.send_keys(Keys.RETURN)

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    scraper = BumeranScraper()
    scraper.abrir_pagina_empleos(dias=2)
    scraper.buscar_vacante('Data Scientist')  
    # Add more scraping logic here
    #scraper.close()