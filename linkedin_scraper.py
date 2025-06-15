import time
import json
import configparser
import os
import sys
import re
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Leer configuración ---
config = configparser.ConfigParser()
script_dir = os.path.dirname(__file__)
config_path = os.path.join(script_dir, "config.ini")
config.read(config_path, encoding="utf-8")

EMAIL = config.get("credentials", "email")
PASSWORD = config.get("credentials", "password")

PAGE_LOAD_SLEEP = config.getfloat("timeouts", "page_load_sleep")
SCROLL_WAIT = config.getfloat("timeouts", "scroll_wait")
MAX_SCROLL_ATTEMPTS = config.getint("timeouts", "max_scroll_attempts")

EDGE_DRIVER_PATH = config.get("driver", "msedgedriver_path")

# Comprobar argumentos
if len(sys.argv) != 2:
    print("Uso: python linkedin_scraper.py <URL>")
    sys.exit(1)

PROFILE_URL = sys.argv[1]

def obtener_nombre_archivo(PROFILE_URLurl):
    match = re.search(r'linkedin\.com/in/([a-zA-Z0-9\-]+)', PROFILE_URL)
    if match:
        nombre = match.group(1)
        nombre = re.sub(r'-[a-zA-Z0-9]+$', '', nombre)  # Quitar parte final tipo -37bb44342
        return nombre.replace('-', '_') + ".json"
    else:
        return "perfil.json"

def hacer_scroll_completo(driver):
    """Hace scroll hacia abajo hasta que no haya más contenido que cargar."""
    ultima_altura = driver.execute_script("return document.body.scrollHeight")
    intentos = 0

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_WAIT)
        nueva_altura = driver.execute_script("return document.body.scrollHeight")
        
        if nueva_altura == ultima_altura:
            intentos += 1
            if intentos >= MAX_SCROLL_ATTEMPTS:
                break
        else:
            intentos = 0
            ultima_altura = nueva_altura

# Configuración del navegador con perfil persistente
profile_path = os.path.join(os.getcwd(), "edge_profile")
edge_options = Options()
# edge_options.add_argument("--headless")
edge_options.add_argument(f"--user-data-dir={profile_path}")
edge_options.add_argument("--start-maximized")
edge_options.add_argument("--disable-blink-features=AutomationControlled")
edge_options.add_argument("--log-level=3")  # Silencia mensajes innecesarios

service = Service(executable_path=EDGE_DRIVER_PATH)
driver = webdriver.Edge(service=service, options=edge_options)

# Iniciar sesión solo si no está iniciada
driver.get("https://www.linkedin.com/login")
time.sleep(PAGE_LOAD_SLEEP)

if "login" in driver.current_url and EMAIL and PASSWORD:
    try:
        driver.find_element(By.ID, "username").send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        time.sleep(PAGE_LOAD_SLEEP)
    except:
        pass

# -------- DATOS GENERALES --------
driver.get(PROFILE_URL)
time.sleep(PAGE_LOAD_SLEEP)
hacer_scroll_completo(driver)

datosgenerales = []
try:
    nombre = driver.find_element(By.CSS_SELECTOR, ".inline.t-24.v-align-middle.break-words").text.strip()
    ubicacion = driver.find_element(By.CSS_SELECTOR, ".text-body-small.inline.t-black--light.break-words").text.strip()
except:
    nombre = ""
    ubicacion = ""

try:
    acerca_de_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.display-flex.ph5.pv3"))
    )
    acerca_de = acerca_de_element.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']").text.strip().replace("\n", " ")
except:
    acerca_de = ""

datosgenerales.append({
    "nombreContacto": nombre,
    "ubicacionContacto": ubicacion,
    "acerca_deContacto": acerca_de
})

# -------- CONTACTO --------
driver.get(PROFILE_URL + "/overlay/contact-info/")
time.sleep(PAGE_LOAD_SLEEP)
hacer_scroll_completo(driver)

contacto = {
    "linkedinContacto": "",
    "teléfonoContacto": "",
    "emailContacto": "",
    "cumpleañosContacto": ""
}

try:
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
except:
    pass

# -------- EXPERIENCIA --------
driver.get(PROFILE_URL + "/details/experience/")
time.sleep(PAGE_LOAD_SLEEP)
hacer_scroll_completo(driver)

experiencias = []
bloques = driver.find_elements(By.CSS_SELECTOR, "li.pvs-list__paged-list-item")

for bloque in bloques:
    try:
        cargo = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[1]").text.strip()
        empresaYtipo = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[2]").text.strip()
        duracion = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[3]").text.strip()
        try:
            ubicacion = bloque.find_elements(By.XPATH, ".//span[contains(text(), 'España') or contains(text(), 'Híbrido') or contains(text(), 'Presencial') or contains(text(), 'En remoto')]")
        except:
            ubicacion = ""
        try:
            raw_desc = bloque.find_element(By.XPATH, ".//div[contains(@class,'t-14 t-normal t-black')]").text.strip()
            descripcion = "" if "Aptitudes:" in raw_desc else raw_desc
        except:
            descripcion = ""

        experiencias.append({
            "cargoExperiencia": cargo,
            "empresaExperiencia": empresaYtipo,
            "duracionExperiencia": duracion,
            "ubicacionExperiencia": ubicacion[0].text if ubicacion else "",
            "descripcionExperiencia": descripcion,
        })
    except:
        pass

# -------- EDUCACIÓN --------
driver.get(PROFILE_URL + "/details/education/")
time.sleep(PAGE_LOAD_SLEEP)
hacer_scroll_completo(driver)

educacion = []
bloques = driver.find_elements(By.CSS_SELECTOR, "li.pvs-list__paged-list-item")

for bloque in bloques:
    try:
        institucion = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[1]").text.strip()
        try:
            raw_titulo = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[2]").text.strip()
            titulo = "" if " - " or "Aptitudes: " in raw_titulo else raw_titulo
        except:
            titulo = ""
        try:
            duracion_pre = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[3]").text.strip()
            duracion = "" if "Aptitudes: " in duracion_pre else duracion_pre
        except:
            duracion = ""

        educacion.append({
            "institucionEducacion": institucion,
            "tituloEducacion": titulo,
            "duracionEducacion": duracion,
        })
    except:
        pass

# -------- CERTIFICADOS --------
driver.get(PROFILE_URL + "/details/certifications/")
time.sleep(PAGE_LOAD_SLEEP)
hacer_scroll_completo(driver)

licYcert = []
bloques = driver.find_elements(By.CSS_SELECTOR, "li.pvs-list__paged-list-item")

for bloque in bloques:
    try:
        certificado = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[1]").text.strip()
        institucion = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[2]").text.strip()
        try:
            raw_time = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[3]").text.strip()
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
            tiempoEXP = ""
            tiempoCAD = ""

        try:
            enlace = bloque.find_element(By.XPATH, './/a[contains(@aria-label, "Mostrar credencial")]').get_attribute("href")
        except:
            enlace = ""

        licYcert.append({
            "tituloCert": certificado,
            "instituciónCert": institucion,
            "expediciónCert": tiempoEXP,
            "caducidadCert": tiempoCAD,
            "enlace_credencialCert": enlace
        })
    except:
        pass

# -------- APTITUDES --------
driver.get(PROFILE_URL + "/details/skills/")
time.sleep(PAGE_LOAD_SLEEP)
hacer_scroll_completo(driver)

aptitudes = []
bloques = driver.find_elements(By.CSS_SELECTOR, "li.pvs-list__paged-list-item")

for bloque in bloques:
    try:
        texto = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[1]").text.strip()
        if texto: 
            aptitudes.append(texto.replace("\n", " "))
    except Exception:
        pass
    
# -------- IDIOMAS --------
driver.get(PROFILE_URL + "/details/languages/")
time.sleep(PAGE_LOAD_SLEEP)
hacer_scroll_completo(driver)

idiomas = []
bloques = driver.find_elements(By.CSS_SELECTOR, "li.pvs-list__paged-list-item")

for bloque in bloques:
    try:
        idioma = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[1]").text.strip()
        try:
            competencia = bloque.find_element(By.XPATH, "(.//span[@aria-hidden='true'])[2]").text.strip()
        except:
            competencia = ""
        idiomas.append({
            "idioma": idioma,
            "competencia": competencia
        })
    except:
        pass

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

print(json.dumps(resultado, indent=2, ensure_ascii=False)) # Mostrar por consola

driver.quit()

