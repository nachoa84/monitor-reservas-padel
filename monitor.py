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
from webdriver_manager.chrome import ChromeDriverManager

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Obtener variables de GitHub Secrets
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
USUARIO_CLUB = os.environ.get('USUARIO_CLUB', '')
PASSWORD_CLUB = os.environ.get('PASSWORD_CLUB', '')

# URLs del club - ¡IMPORTANTE! REEMPLAZAR CON LAS REALES
URL_LOGIN = "https://tirofederalgualeguaychu.com/mi-cuenta"  # <-- VERIFICAR URL
URL_RESERVAS = "https://tirofederalgualeguaychu.com/reservas"  # <-- VERIFICAR URL

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
    chrome_options.add_argument("--headless")  # Sin ventana
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # User Agent real
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Evitar detección como bot
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        # Usar webdriver-manager para manejar ChromeDriver automáticamente
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        log("✅ Driver configurado con webdriver-manager")
        return driver
    except Exception as e:
        log(f"❌ Error con webdriver-manager: {e}")
        
        # Fallback: intentar sin service
        try:
            driver = webdriver.Chrome(options=chrome_options)
            log("✅ Driver configurado sin service")
            return driver
        except Exception as e2:
            log(f"❌ Error sin service: {e2}")
            return None

def hacer_login(driver):
    """Login específico para Tiro Federal Gualeguaychú"""
    try:
        log("🔐 Intentando login en Tiro Federal...")
        driver.get(URL_LOGIN)
        time.sleep(5)
        
        log("📝 Buscando campos de login (username/password)...")
        
        # CAMPO USUARIO
        try:
            campo_usuario = driver.find_element(By.ID, "username")
            log("✅ Campo usuario por ID")
        except:
            campo_usuario = driver.find_element(By.NAME, "username")
            log("✅ Campo usuario por NAME")
        
        campo_usuario.clear()
        campo_usuario.send_keys(USUARIO_CLUB)
        log("📝 Usuario ingresado")
        
        # CAMPO CONTRASEÑA
        try:
            campo_password = driver.find_element(By.ID, "password")
            log("✅ Campo contraseña por ID")
        except:
            campo_password = driver.find_element(By.NAME, "password")
            log("✅ Campo contraseña por NAME")
        
        campo_password.clear()
        campo_password.send_keys(PASSWORD_CLUB)
        log("🔑 Contraseña ingresada")
        
        # BUSCAR BOTÓN DE LOGIN
        log("🔍 Buscando botón de login...")
        
        # Selectores específicos para Woocommerce (que usa tu club)
        selectores_boton = [
            "//button[@name='login']",
            "//button[@type='submit']",
            "//button[contains(@class, 'woocommerce-button')]",
            "//button[contains(@class, 'woocommerce-form-login__submit')]",
            "//input[@name='login']",
            "//input[@type='submit']",
        ]
        
        boton_encontrado = False
        for selector in selectores_boton:
            try:
                boton_login = driver.find_element(By.XPATH, selector)
                boton_login.click()
                log(f"✅ Botón encontrado: {selector}")
                boton_encontrado = True
                break
            except:
                continue
        
        if not boton_encontrado:
            # Si no encuentra botón, presionar ENTER
            campo_password.send_keys(Keys.RETURN)
            log("✅ Login con ENTER")
            boton_encontrado = True
        
        # Esperar login
        log("⏳ Esperando login...")
        time.sleep(5)
        
        # Verificar login exitoso
        pagina_html = driver.page_source.lower()
        
        # Buscar indicadores de error
        if "error" in pagina_html or "incorrecto" in pagina_html or "invalid" in pagina_html:
            log("❌ Error en login - Credenciales incorrectas")
            return False
        
        # Buscar indicadores de éxito
        if "mi cuenta" in pagina_html or "logout" in pagina_html or "cerrar sesión" in pagina_html:
            log("✅ Login exitoso - Página 'Mi cuenta' detectada")
            return True
        
        # Si no encuentra indicadores claros, continuar de todos modos
        log("⚠️ No se detectaron indicadores claros de login, pero continuando...")
        return True
        
    except Exception as e:
        log(f"❌ Error en login: {e}")
        return False

def buscar_horarios_especificos(driver):
    """Busca horarios específicos de 20-22 hs"""
    try:
        log("🔍 Buscando horarios 20-22 hs...")
        
        # Ir a reservas (o refrescar si ya estamos allí)
        driver.get(URL_RESERVAS)
        time.sleep(4)
        
        # Obtener HTML completo
        html_completo = driver.page_source
        
        # Lista de patrones a buscar
        patrones = [
            "20:00", "20:00", "20hs", "20 hs",
            "20 a 22", "20-22", "20:00 a 22:00",
            "20.00", "20:00hs", "20 h", "8 pm", "8pm"
        ]
        
        horarios_encontrados = []
        
        # Buscar cada patrón
        for patron in patrones:
            if patron.lower() in html_completo.lower():
                # Encontrar contexto
                inicio = html_completo.lower().find(patron.lower())
                contexto = html_completo[max(0, inicio-50):min(len(html_completo), inicio+50)]
                horarios_encontrados.append({
                    "horario": patron,
                    "contexto": contexto.replace('\n', ' ').strip()
                })
                log(f"✅ Encontrado: {patron}")
        
        # También buscar en elementos visibles
        try:
            elementos = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '20')]")
            for elemento in elementos:
                texto = elemento.text
                if any(hora in texto.lower() for hora in ["20", "8 pm", "8pm"]):
                    if "22" in texto or "reservar" in texto.lower():
                        horarios_encontrados.append({
                            "horario": texto[:30],
                            "tipo": "elemento_web"
                        })
                        log(f"✅ En elemento web: {texto[:30]}...")
        except Exception as e:
            log(f"⚠️ Error buscando elementos: {e}")
        
        return horarios_encontrados
        
    except Exception as e:
        log(f"❌ Error buscando horarios: {e}")
        return []

def intentar_reserva_automatica(driver, horario_info):
    """Intenta reservar automáticamente"""
    try:
        horario = horario_info.get("horario", "")
        log(f"🎯 Intentando reservar: {horario}")
        
        # Estrategia 1: Buscar elementos que contengan el horario
        elementos_con_horario = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{str(horario).lower()[:5]}')]")
        
        for elemento in elementos_con_horario[:5]:  # Limitar a primeros 5
            try:
                # Buscar botón de reserva en el mismo contenedor
                parent = elemento.find_element(By.XPATH, "..")
                botones = parent.find_elements(By.TAG_NAME, "button")
                
                for btn in botones:
                    btn_text = btn.text.lower()
                    if "reservar" in btn_text or "reserva" in btn_text or "seleccionar" in btn_text:
                        btn.click()
                        log("✅ Click en botón Reservar/Seleccionar")
                        time.sleep(2)
                        
                        # Confirmar si hay popup
                        try:
                            confirmar = driver.find_element(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirmar')]")
                            confirmar.click()
                            log("✅ Reserva confirmada")
                            return True
                        except:
                            log("⚠️ No hubo confirmación, pero se hizo click en reservar")
                            return True
            except:
                continue
        
        # Estrategia 2: Buscar enlaces de reserva
        try:
            enlaces = driver.find_elements(By.PARTIAL_LINK_TEXT, "Reservar")
            for enlace in enlaces[:3]:  # Limitar a primeros 3
                enlace.click()
                log("✅ Click en enlace Reservar")
                time.sleep(2)
                return True
        except:
            pass
        
        log("⚠️ No se pudo reservar automáticamente")
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
            mensaje_horarios += "<b>Horarios encontrados:</b>\n"
            
            for i, horario in enumerate(horarios[:5], 1):  # Máximo 5
                mensaje_horarios += f"{i}. {horario['horario']}\n"
            
            mensaje_horarios += f"\n🔗 <b>URL:</b> {URL_RESERVAS}\n"
            mensaje_horarios += "⚡ <i>¡No esperes, corré a reservar!</i>"
            
            # Enviar alerta
            enviar_telegram(mensaje_horarios)
            
            # Intentar reservar el primer horario
            if horarios and len(horarios) > 0:
                log("🔄 Intentando reserva automática...")
                reservado = intentar_reserva_automatica(driver, horarios[0])
                if reservado:
                    enviar_telegram(f"✅ <b>¡RESERVA AUTOMÁTICA EXITOSA!</b>\nHorario: {horarios[0]['horario']}")
            
            return True
        else:
            log("📭 No hay horarios 20-22 disponibles")
            mensaje_vacio = f"""
📭 <b>Sin disponibilidad</b>
🕒 {datetime.now().strftime('%H:%M:%S')}
📅 {datetime.now().strftime('%d/%m/%Y')}
⚠️ No hay horarios 20-22 hs disponibles
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
