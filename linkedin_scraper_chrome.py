import time
import json
import os
import sys
import re
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

os.environ['DISPLAY'] = ':99' # Asegurar display virtual configurado

# Comprobar argumentos
if len(sys.argv) != 2:
    print("Uso: python linkedin_scraper_chrome.py <URL_DEL_PERFIL>") # Nombre de archivo actualizado
    sys.exit(1)

PROFILE_URL = sys.argv[1]

def obtener_nombre_archivo(profile_url):
    match = re.search(r'linkedin\.com/in/([a-zA-Z0-9\-]+)', profile_url)
    if match:
        nombre = match.group(1)
        nombre = re.sub(r'-[a-zA-Z0-9]+$', '', nombre)
        return nombre.replace('-', '_') + ".json"
    else:
        return "perfil.json"

def hacer_scroll_completo(driver, espera=1.5, max_intentos=10):
    """Hace scroll hacia abajo hasta que no haya más contenido que cargar."""
    ultima_altura = driver.execute_script("return document.body.scrollHeight")
    intentos = 0

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(espera)
        nueva_altura = driver.execute_script("return document.body.scrollHeight")
        
        if nueva_altura == ultima_altura:
            intentos += 1
            if intentos >= max_intentos:
                break
        else:
            intentos = 0
            ultima_altura = nueva_altura

# Leer configuración (mantener en blanco para que el usuario las introduzca en VNC si es necesario)
EMAIL = ""
PASSWORD = ""

# Configuración del navegador con perfil persistente
profile_path = os.path.join(os.getcwd(), "chrome_profile") # Cambiado a 'chrome_profile' (sin 'debug')
chrome_options = uc.ChromeOptions()
chrome_options.add_argument(f"--user-data-dir={profile_path}")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--log-level=3") # Nivel de log más bajo para menos verbosidad

driver = uc.Chrome(options=chrome_options)

# Iniciar sesión solo si no está iniciada
driver.get("https://www.linkedin.com/login")
time.sleep(5) # Espera inicial para que la página cargue

if "login" in driver.current_url and EMAIL and PASSWORD:
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')

        for char in EMAIL:
            username_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
        time.sleep(random.uniform(1, 6))

        for char in PASSWORD:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
        time.sleep(random.uniform(1, 6))

        login_button.click()
        
        # --- LÓGICA PARA MANEJAR EL PUZZLE/VERIFICACIÓN ---
        try:
            WebDriverWait(driver, 60).until(
                EC.any_of(
                    EC.url_to_be("https://www.linkedin.com/feed/"),
                    EC.presence_of_element_located((By.ID, "global-nav-typeahead"))
                )
            )

        except TimeoutException:
            print("\n")
            print("====================================================================================")
            print("¡ATENCIÓN! Parece que LinkedIn requiere una verificación manual (puzzle/código).")
            print("Por favor, conéctate a tu servidor VNC (si no lo estás ya) y mira la ventana del navegador.")
            print("Resuelve el puzzle de seguridad o introduce el código en la ventana del navegador.")
            print("Una vez que estés logueado en https://www.linkedin.com/feed/ (la página principal de inicio),")
            print("VUELVE A ESTA TERMINAL Y presiona ENTER para que el script continúe.")
            print("====================================================================================")
            input("Presiona ENTER después de resolver el desafío en el navegador: ")

            WebDriverWait(driver, 60).until(
                EC.any_of(
                    EC.url_to_be("https://www.linkedin.com/feed/"),
                    EC.presence_of_element_located((By.ID, "global-nav-typeahead"))
                )
            )

    except Exception as e:
        print(f"ERROR: Fallo durante el inicio de sesión: {e}")
        driver.save_screenshot("login_error.png") # Nombre de archivo actualizado
        driver.quit()
        sys.exit(1)

# -------- DATOS GENERALES --------
driver.get(PROFILE_URL)
time.sleep(random.uniform(3, 7))
hacer_scroll_completo(driver)

datosgenerales = []
try:
    nombre_element = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".inline.t-24.v-align-middle.break-words"))
    )
    nombre = nombre_element.text.strip()
    ubicacion = driver.find_element(By.CSS_SELECTOR, ".text-body-small.inline.t-black--light.break-words").text.strip()
except Exception as e:
    nombre = ""
    ubicacion = ""
    print(f"ERROR: No se pudieron obtener nombre/ubicación: {e}")
    driver.save_screenshot("error_datos_generales.png") # Nombre de archivo actualizado

try:
    acerca_de_section = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.display-flex.ph5.pv3"))
    )
    acerca_de_element = acerca_de_section.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']")
    acerca_de = acerca_de_element.text.strip().replace("\n", " ")
except Exception as e:
    acerca_de = ""
    print(f"ERROR: No se pudo obtener la sección 'Acerca de': {e}")
    driver.save_screenshot("error_acerca_de.png") # Nombre de archivo actualizado

datosgenerales.append({
    "nombreContacto": nombre,
    "ubicacionContacto": ubicacion,
    "acerca_deContacto": acerca_de
})

# -------- CONTACTO --------
driver.get(PROFILE_URL + "/overlay/contact-info/")
time.sleep(random.uniform(3, 7))

contacto = {
    "linkedinContacto": "",
    "teléfonoContacto": "",
    "emailContacto": "",
    "cumpleañosContacto": ""
}

try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "pv-contact-info__contact-type"))
    )
    bloques = driver.find_elements(By.CLASS_NAME, "pv-contact-info__contact-type")
    for bloque in bloques:
        titulo = bloque.find_element(By.TAG_NAME, "h3").text.strip().lower()
        if "perfil" in titulo:
            contacto["linkedinContacto"] = bloque.find_element(By.TAG_NAME, "a").get_attribute("href")
        elif "teléfono" in titulo:
            contacto["teléfonoContacto"] = bloque.find_element(By.TAG_NAME, "span").text.strip()
        elif "email" in titulo:
            contacto["emailContacto"] = bloque.find_element(By.TAG_NAME, "a").text.strip()
        elif "cumpleaños" in titulo:
            contacto["cumpleañosContacto"] = bloque.find_element(By.TAG_NAME, "span").text.strip()
except Exception as e:
    print(f"ERROR: No se pudo obtener la información de contacto: {e}")
    driver.save_screenshot("error_contacto.png") # Nombre de archivo actualizado

# -------- EXPERIENCIA --------
driver.get(PROFILE_URL + "/details/experience/")
time.sleep(random.uniform(3, 7))
hacer_scroll_completo(driver)

experiencias = []
try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.pvs-list__paged-list-item"))
    )
    bloques = driver.find_elements(By.CSS_SELECTOR, "li.pvs-list__paged-list-item")

    for i, bloque in enumerate(bloques):
        try:
            cargo = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[1]").text.strip()
            empresaYtipo = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[2]").text.strip()
            duracion = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[3]").text.strip()
            
            ubicacion_element = ""
            try:
                ubicacion_elements = bloque.find_elements(By.XPATH, ".//div[contains(@class, 'entity-result__secondary-subtitle')]//span[@aria-hidden='true']")
                for u_elem in ubicacion_elements:
                    text = u_elem.text.strip()
                    if "España" in text or "Híbrido" in text or "Presencial" in text or "En remoto" in text:
                        ubicacion_element = text
                        break
            except:
                pass

            raw_desc = ""
            descripcion = ""
            try:
                raw_desc_element = bloque.find_element(By.XPATH, ".//div[contains(@class,'t-14 t-normal t-black')]//span[@aria-hidden='true']")
                raw_desc = raw_desc_element.text.strip()
                descripcion = "" if "Aptitudes:" in raw_desc else raw_desc
            except:
                pass

            experiencias.append({
                "cargoExperiencia": cargo,
                "empresaExperiencia": empresaYtipo,
                "duracionExperiencia": duracion,
                "ubicacionExperiencia": ubicacion_element,
                "descripcionExperiencia": descripcion,
            })
        except Exception as e:
            print(f"ERROR: Fallo al procesar experiencia {i+1}: {e}")
except Exception as e:
    print(f"ERROR: No se pudieron obtener las experiencias: {e}")
    driver.save_screenshot("error_experiencia.png") # Nombre de archivo actualizado

# -------- EDUCACIÓN --------
driver.get(PROFILE_URL + "/details/education/")
time.sleep(random.uniform(3, 7))
hacer_scroll_completo(driver)

educacion = []
try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.pvs-list__paged-list-item"))
    )
    bloques = driver.find_elements(By.CSS_SELECTOR, "li.pvs-list__paged-list-item")

    for i, bloque in enumerate(bloques):
        try:
            institucion = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[1]").text.strip()
            
            raw_titulo = ""
            titulo = ""
            try:
                raw_titulo_element = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[2]")
                raw_titulo = raw_titulo_element.text.strip()
                titulo = "" if " - " in raw_titulo or "Aptitudes: " in raw_titulo else raw_titulo
            except:
                pass
            
            duracion_pre = ""
            duracion = ""
            try:
                duracion_pre_element = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[3]")
                duracion_pre = duracion_pre_element.text.strip()
                duracion = "" if "Aptitudes: " in duracion_pre else duracion_pre
            except:
                pass

            educacion.append({
                "institucionEducacion": institucion,
                "tituloEducacion": titulo,
                "duracionEducacion": duracion,
            })
        except Exception as e:
            print(f"ERROR: Fallo al procesar educación {i+1}: {e}")
except Exception as e:
    print(f"ERROR: No se pudo obtener la sección de educación: {e}")
    driver.save_screenshot("error_educacion.png") # Nombre de archivo actualizado

# -------- CERTIFICADOS --------
driver.get(PROFILE_URL + "/details/certifications/")
time.sleep(random.uniform(3, 7))
hacer_scroll_completo(driver)

licYcert = []
try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.pvs-list__paged-list-item"))
    )
    bloques = driver.find_elements(By.CSS_SELECTOR, "li.pvs-list__paged-list-item")

    for i, bloque in enumerate(bloques):
        try:
            certificado = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[1]").text.strip()
            institucion = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[2]").text.strip()
            
            raw_time = ""
            tiempoEXP = ""
            tiempoCAD = ""
            try:
                raw_time_element = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[3]")
                raw_time = raw_time_element.text.strip()
                if "Expedición:" in raw_time:
                    tiempoEXP = raw_time.replace("Expedición: ", "").strip()
                    tiempoCAD = ""
                elif "Caducidad:" in raw_time:
                    tiempoCAD = raw_time.replace("Caducidad: ", "").strip()
                    tiempoEXP = ""
                else:
                    tiempoEXP = raw_time
                    tiempoCAD = ""
            except:
                pass

            enlace = ""
            try:
                enlace_element = bloque.find_element(By.XPATH, './/a[contains(@aria-label, "Mostrar credencial")]')
                enlace = enlace_element.get_attribute("href")
            except:
                pass

            licYcert.append({
                "tituloCert": certificado,
                "instituciónCert": institucion,
                "expediciónCert": tiempoEXP,
                "caducidadCert": tiempoCAD,
                "enlace_credencialCert": enlace
            })
        except Exception as e:
            print(f"ERROR: Fallo al procesar certificado {i+1}: {e}")
except Exception as e:
    print(f"ERROR: No se pudo obtener la sección de certificaciones: {e}")
    driver.save_screenshot("error_certificaciones.png") # Nombre de archivo actualizado

# -------- APTITUDES --------
driver.get(PROFILE_URL + "/details/skills/")
time.sleep(random.uniform(3, 7))
hacer_scroll_completo(driver)

aptitudes = []
try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.pvs-list__paged-list-item"))
    )
    bloques = driver.find_elements(By.CSS_SELECTOR, "li.pvs-list__paged-list-item")

    for i, bloque in enumerate(bloques):
        try:
            texto_element = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[1]")
            texto = texto_element.text.strip()
            if texto:
                aptitudes.append(texto.replace("\n", " "))
        except Exception as e:
            print(f"ERROR: Fallo al procesar aptitud {i+1}: {e}")
except Exception as e:
    print(f"ERROR: No se pudo obtener la sección de aptitudes: {e}")
    driver.save_screenshot("error_aptitudes.png") # Nombre de archivo actualizado
    
# -------- IDIOMAS --------
driver.get(PROFILE_URL + "/details/languages/")
time.sleep(random.uniform(3, 7))
hacer_scroll_completo(driver)

idiomas = []
try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.pvs-list__paged-list-item"))
    )
    bloques = driver.find_elements(By.CSS_SELECTOR, "li.pvs-list__paged-list-item")

    for i, bloque in enumerate(bloques):
        try:
            idioma = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[1]").text.strip()
            competencia = ""
            try:
                competencia_element = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[2]")
                competencia = competencia_element.text.strip()
            except:
                pass
            idiomas.append({
                "idioma": idioma,
                "competencia": competencia
            })
        except Exception as e:
            print(f"ERROR: Fallo al procesar idioma {i+1}: {e}")
except Exception as e:
    print(f"ERROR: No se pudo obtener la sección de idiomas: {e}")
    driver.save_screenshot("error_idiomas.png") # Nombre de archivo actualizado

# -------- GUARDAR JSON --------
resultado = {
    "datos generales": datosgenerales,
    "información de contacto": contacto,
    "experiencias": experiencias,
    "educacion": educacion,
    "licencias y certificaciones": licYcert,
    "aptitudes": aptitudes,
    "idiomas": idiomas
}

nombre_archivo = obtener_nombre_archivo(PROFILE_URL)
with open(nombre_archivo, "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)

print(json.dumps(resultado, indent=2, ensure_ascii=False)) # Salida JSON final por terminal

driver.quit()