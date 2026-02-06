#!/usr/bin/env python3
"""
MONITOR AUTOMÁTICO DE RESERVAS DE PÁDEL - VERSIÓN COMPLETA
Específico para Tiro Federal Gualeguaychú
"""

import os
import sys
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Obtener variables de GitHub Secrets
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
USUARIO_CLUB = os.environ.get('USUARIO_CLUB', '')
PASSWORD_CLUB = os.environ.get('PASSWORD_CLUB', '')

# URLs CORREGIDAS según lo que me enviaste
URL_LOGIN = "https://www.tirofederalgchu.com/web/mi-cuenta/"
URL_RESERVAS = "https://www.tirofederalgchu.com/web/producto/canchas-padel/"

# ============================================================================
# FUNCIONES DE NOTIFICACIÓN
# ============================================================================

def enviar_telegram(mensaje):
    """Envía mensaje por Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Faltan credenciales de Telegram en los Secrets")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    try:
        response = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": "HTML"
        }, timeout=10)
        
        if response.status_code == 200:
            print("✅ Mensaje enviado a Telegram")
            return True
        else:
            print(f"❌ Error Telegram: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error enviando Telegram: {e}")
        return False

def log(mensaje):
    """Muestra mensaje con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {mensaje}")
    sys.stdout.flush()

# ============================================================================
# FUNCIONES DE VERIFICACIÓN - ESPECÍFICAS PARA TU CLUB
# ============================================================================

def setup_driver():
    """Configura el navegador Chrome usando webdriver-manager"""
    chrome_options = Options()
    
    # Configuración para entorno cloud
    chrome_options.add_argument("--headless=new")  # Headless moderno
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # User Agent real
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Evitar detección como bot
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Preferencias para evitar detección
    chrome_options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })
    
    try:
        # Usar webdriver-manager para manejar ChromeDriver automáticamente
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Script para evitar detección
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        
        log("✅ Driver configurado correctamente")
        return driver
    except Exception as e:
        log(f"❌ Error configurando driver: {e}")
        return None

def hacer_login(driver):
    """Login específico para Tiro Federal Gualeguaychú"""
    try:
        log(f"🔐 Intentando login en: {URL_LOGIN}")
        driver.get(URL_LOGIN)
        
        # Esperar con timeout
        wait = WebDriverWait(driver, 15)
        time.sleep(3)
        
        log("📝 Buscando campos de login...")
        
        # CAMPO USUARIO - Buscar con múltiples selectores
        campo_usuario = None
        selectores_usuario = [
            (By.ID, "username"),
            (By.NAME, "username"),
            (By.XPATH, "//input[@type='text' or @type='email']"),
            (By.CSS_SELECTOR, "input[name='username'], input[name='email'], input[type='text']")
        ]
        
        for selector_type, selector_value in selectores_usuario:
            try:
                campo_usuario = wait.until(EC.presence_of_element_located((selector_type, selector_value)))
                log(f"✅ Campo usuario encontrado: {selector_type}={selector_value}")
                break
            except:
                continue
        
        if not campo_usuario:
            log("❌ No se encontró campo de usuario")
            return False
        
        campo_usuario.clear()
        campo_usuario.send_keys(USUARIO_CLUB)
        log("📝 Usuario ingresado")
        
        # CAMPO CONTRASEÑA
        campo_password = None
        selectores_password = [
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.XPATH, "//input[@type='password']"),
            (By.CSS_SELECTOR, "input[type='password']")
        ]
        
        for selector_type, selector_value in selectores_password:
            try:
                campo_password = driver.find_element(selector_type, selector_value)
                log(f"✅ Campo contraseña encontrado: {selector_type}={selector_value}")
                break
            except:
                continue
        
        if not campo_password:
            log("❌ No se encontró campo de contraseña")
            return False
        
        campo_password.clear()
        campo_password.send_keys(PASSWORD_CLUB)
        log("🔑 Contraseña ingresada")
        
        # BUSCAR BOTÓN DE LOGIN
        log("🔍 Buscando botón de login...")
        
        selectores_boton = [
            (By.XPATH, "//button[@type='submit' or @name='login']"),
            (By.XPATH, "//input[@type='submit']"),
            (By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"),
            (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'iniciar')]"),
            (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ingresar')]"),
        ]
        
        boton_login = None
        for selector_type, selector_value in selectores_boton:
            try:
                boton_login = driver.find_element(selector_type, selector_value)
                log(f"✅ Botón login encontrado: {selector_type}={selector_value}")
                break
            except:
                continue
        
        if boton_login:
            boton_login.click()
            log("✅ Botón clickeado")
        else:
            # Si no encuentra botón, presionar ENTER
            campo_password.send_keys(Keys.RETURN)
            log("✅ Login con ENTER")
        
        # Esperar login (con timeout)
        log("⏳ Esperando login...")
        time.sleep(5)
        
        # Verificar login exitoso
        current_url = driver.current_url
        pagina_html = driver.page_source.lower()
        
        log(f"📄 URL actual: {current_url}")
        
        # Si sigue en la misma página, login probablemente falló
        if URL_LOGIN in current_url:
            log("⚠️ Sigue en página de login - posible falla")
            return False
        
        # Buscar indicadores de éxito
        if "mi cuenta" in pagina_html or "logout" in pagina_html or "cerrar sesión" in pagina_html:
            log("✅ Login exitoso detectado")
            return True
        
        # Si no encuentra indicadores claros, verificar por URL de reservas
        driver.get(URL_RESERVAS)
        time.sleep(3)
        
        if URL_RESERVAS in driver.current_url:
            log("✅ Acceso a reservas exitoso")
            return True
        
        log("⚠️ Login resultó ambiguo, pero continuando...")
        return True
        
    except Exception as e:
        log(f"❌ Error en login: {e}")
        # Tomar screenshot para debugging
        try:
            driver.save_screenshot("error_login.png")
            log("📸 Screenshot guardado como error_login.png")
        except:
            pass
        return False

def buscar_horarios_especificos(driver):
    """Busca horarios específicos de 20-22 hs"""
    try:
        log(f"🔍 Buscando horarios en: {URL_RESERVAS}")
        
        # Ir a reservas
        driver.get(URL_RESERVAS)
        time.sleep(4)
        
        # Tomar screenshot para debugging
        try:
            driver.save_screenshot("pagina_reservas.png")
            log("📸 Screenshot de reservas guardado")
        except:
            pass
        
        # Obtener HTML completo
        html_completo = driver.page_source
        log(f"📄 Tamaño HTML: {len(html_completo)} caracteres")
        
        # Guardar HTML para debugging
        with open("debug_reservas.html", "w", encoding="utf-8") as f:
            f.write(html_completo)
        
        # Lista de patrones a buscar
        patrones = [
            "20:00", "20:00", "20hs", "20 hs",
            "20 a 22", "20-22", "20:00 a 22:00",
            "20.00", "20:00hs", "20 h", "8 pm", "8pm",
            "20hs", "21:00", "21hs", "22:00", "22hs"
        ]
        
        horarios_encontrados = []
        
        # Buscar cada patrón
        for patron in patrones:
            conteo = html_completo.lower().count(patron.lower())
            if conteo > 0:
                # Encontrar contexto del primer match
                inicio = html_completo.lower().find(patron.lower())
                contexto = html_completo[max(0, inicio-100):min(len(html_completo), inicio+100)]
                contexto_limpio = ' '.join(contexto.replace('\n', ' ').split())
                
                horarios_encontrados.append({
                    "horario": patron,
                    "conteo": conteo,
                    "contexto": contexto_limpio[:150] + "..."
                })
                log(f"✅ Encontrado '{patron}' {conteo} veces")
        
        # También buscar en elementos visibles
        try:
            elementos = driver.find_elements(By.XPATH, "//*[contains(text(), '20') or contains(text(), '21') or contains(text(), '22')]")
            for elemento in elementos:
                texto = elemento.text.strip()
                if texto and any(hora in texto.lower() for hora in ["20", "21", "22", "8 pm", "8pm", "9 pm", "9pm"]):
                    # Verificar que sea un horario (no solo un número aleatorio)
                    if ":" in texto or "hs" in texto.lower() or "h" in texto.lower():
                        horarios_encontrados.append({
                            "horario": texto[:50],
                            "tipo": "elemento_visible",
                            "tag": elemento.tag_name
                        })
                        log(f"✅ En elemento {elemento.tag_name}: '{texto[:50]}...'")
        except Exception as e:
            log(f"⚠️ Error buscando elementos: {e}")
        
        if horarios_encontrados:
            log(f"🎉 ¡ENCONTRADOS {len(horarios_encontrados)} HORARIOS!")
        else:
            log("📭 No se encontraron horarios 20-22 hs")
            
        return horarios_encontrados
        
    except Exception as e:
        log(f"❌ Error buscando horarios: {e}")
        return []

def intentar_reserva_automatica(driver, horario_info):
    """Intenta reservar automáticamente"""
    try:
        horario = horario_info.get("horario", "")
        log(f"🎯 Intentando reservar: {horario}")
        
        # Estrategia 1: Buscar elementos que contengan el horario y estén clickeables
        elementos_con_horario = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{str(horario).lower()[:5]}')]")
        
        for elemento in elementos_con_horario[:10]:  # Limitar a primeros 10
            try:
                # Verificar si es clickeable
                if elemento.is_displayed() and elemento.is_enabled():
                    # Buscar botón de reserva cercano
                    try:
                        # Primero buscar en el mismo elemento
                        if elemento.tag_name.lower() in ['button', 'a', 'input']:
                            log(f"🖱️ Intentando click en elemento: {elemento.tag_name}")
                            elemento.click()
                            time.sleep(2)
                            log("✅ Click realizado")
                            return True
                        
                        # Buscar en elementos padres
                        for _ in range(3):  # Buscar hasta 3 niveles arriba
                            elemento = elemento.find_element(By.XPATH, "..")
                            botones = elemento.find_elements(By.TAG_NAME, "button")
                            
                            for btn in botones:
                                btn_text = btn.text.lower()
                                if "reservar" in btn_text or "seleccionar" in btn_text or "reserva" in btn_text:
                                    btn.click()
                                    log("✅ Click en botón de reserva")
                                    time.sleep(2)
                                    return True
                    except:
                        continue
            except:
                continue
        
        # Estrategia 2: Buscar botones de reserva generales
        try:
            botones_reserva = driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'reservar') or contains(text(), 'Reservar')]")
            for btn in botones_reserva[:3]:
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    log("✅ Click en botón 'Reservar'")
                    time.sleep(2)
                    return True
        except:
            pass
        
        log("⚠️ No se pudo reservar automáticamente - reserva manual requerida")
        return False
        
    except Exception as e:
        log(f"❌ Error en reserva automática: {e}")
        return False

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def ejecutar_monitor():
    """Función principal"""
    log("=" * 60)
    log("🤖 MONITOR TIRO FEDERAL GUALEGUAYCHÚ")
    log("=" * 60)
    
    # Verificar credenciales
    if not all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, USUARIO_CLUB, PASSWORD_CLUB]):
        log("❌ Faltan variables en GitHub Secrets")
        log("   Verifica: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, USUARIO_CLUB, PASSWORD_CLUB")
        return False
    
    # Notificación de inicio
    mensaje_inicio = f"""
🔔 <b>Monitor iniciado</b>
🏢 Tiro Federal Gualeguaychú
🕒 {datetime.now().strftime('%H:%M:%S')}
📅 {datetime.now().strftime('%d/%m/%Y')}
🔗 {URL_RESERVAS}
"""
    enviar_telegram(mensaje_inicio)
    
    driver = None
    try:
        # 1. Configurar navegador
        driver = setup_driver()
        if not driver:
            enviar_telegram("❌ Error configurando navegador")
            return False
        
        # 2. Login
        if not hacer_login(driver):
            enviar_telegram("❌ Error en login - Verificar credenciales o URLs")
            return False
        
        # 3. Buscar horarios
        horarios = buscar_horarios_especificos(driver)
        
        if horarios:
            log(f"🎉 ¡ENCONTRADOS {len(horarios)} HORARIOS!")
            
            # Preparar mensaje con todos los horarios
            mensaje_horarios = "🚨 <b>¡HORARIOS DISPONIBLES!</b> 🚨\n\n"
            mensaje_horarios += f"🏢 <b>Club:</b> Tiro Federal\n"
            mensaje_horarios += f"📅 <b>Fecha:</b> {datetime.now().strftime('%d/%m')}\n"
            mensaje_horarios += f"🕒 <b>Hora detección:</b> {datetime.now().strftime('%H:%M:%S')}\n\n"
            mensaje_horarios += f"<b>Total encontrados:</b> {len(horarios)}\n\n"
            mensaje_horarios += "<b>Detalles:</b>\n"
            
            for i, horario in enumerate(horarios[:8], 1):  # Máximo 8
                if 'conteo' in horario:
                    mensaje_horarios += f"{i}. {horario['horario']} (aparece {horario['conteo']} veces)\n"
                else:
                    mensaje_horarios += f"{i}. {horario['horario'][:50]}...\n"
            
            mensaje_horarios += f"\n🔗 <b>URL directa:</b> {URL_RESERVAS}\n"
            mensaje_horarios += "⚡ <i>¡Reserva rápido antes que se acaben!</i>"
            
            # Enviar alerta
            enviar_telegram(mensaje_horarios)
            
            # Intentar reservar el primer horario
            if horarios and len(horarios) > 0:
                log("🔄 Intentando reserva automática...")
                reservado = intentar_reserva_automatica(driver, horarios[0])
                if reservado:
                    enviar_telegram(f"✅ <b>¡INTENTO DE RESERVA AUTOMÁTICA!</b>\nHorario: {horarios[0]['horario']}\nVerifica en el sitio si se completó.")
            
            return True
        else:
            log("📭 No hay horarios 20-22 disponibles")
            mensaje_vacio = f"""
📭 <b>Sin disponibilidad</b>
🕒 {datetime.now().strftime('%H:%M:%S')}
📅 {datetime.now().strftime('%d/%m/%Y')}
⚠️ No hay horarios 20-22 hs disponibles
🔗 {URL_RESERVAS}
"""
            enviar_telegram(mensaje_vacio)
            return False
            
    except Exception as e:
        log(f"❌ ERROR CRÍTICO: {e}")
        enviar_telegram(f"❌ <b>Error en monitor:</b>\n{str(e)[:150]}")
        return False
        
    finally:
        if driver:
            try:
                driver.quit()
                log("✅ Navegador cerrado")
            except:
                pass
        
        log("=" * 60)
        log("✅ EJECUCIÓN FINALIZADA")
        log("=" * 60)

# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    # Verificar que estamos en GitHub Actions
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        log("🚀 Ejecutando en GitHub Actions")
    else:
        log("💻 Ejecutando localmente")
    
    # Ejecutar monitor
    exit_code = 0 if ejecutar_monitor() else 1
    sys.exit(exit_code)
