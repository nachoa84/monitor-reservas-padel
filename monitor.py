#!/usr/bin/env python3
"""
MONITOR AUTOMÁTICO DE RESERVAS DE PÁDEL
Para GitHub Actions - Versión 2.0
"""

import os
import sys
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# ============================================================================
# CONFIGURACIÓN - SE TOMAN DE VARIABLES SECRETAS EN GITHUB
# ============================================================================

# Obtener variables de GitHub Secrets
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
USUARIO_CLUB = os.environ.get('USUARIO_CLUB', '')
PASSWORD_CLUB = os.environ.get('PASSWORD_CLUB', '')

# URLs del club (cambiar según tu club)
URL_LOGIN = "https://tuclub.com/login"        # <-- CAMBIAR
URL_RESERVAS = "https://tuclub.com/reservas"  # <-- CAMBIAR

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
# FUNCIONES DE VERIFICACIÓN
# ============================================================================

def setup_driver():
    """Configura el navegador Chrome para GitHub Actions"""
    chrome_options = Options()
    
    # Configuración para entorno cloud
    chrome_options.add_argument("--headless")  # Sin interfaz
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
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        log(f"❌ Error creando driver: {e}")
        return None

def hacer_login(driver):
    """Realiza login en la página del club"""
    try:
        log("🔐 Intentando login...")
        driver.get(URL_LOGIN)
        time.sleep(5)  # Esperar carga
        
        # DETECTAR CAMPOS DE LOGIN - AJUSTAR SEGÚN TU PÁGINA
        # Opción 1: Por name (común)
        try:
            driver.find_element(By.NAME, "usuario").send_keys(USUARIO_CLUB)
            driver.find_element(By.NAME, "password").send_keys(PASSWORD_CLUB)
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            log("✅ Login con campos 'usuario'/'password'")
        except:
            # Opción 2: Por ID (común)
            try:
                driver.find_element(By.ID, "username").send_keys(USUARIO_CLUB)
                driver.find_element(By.ID, "password").send_keys(PASSWORD_CLUB)
                driver.find_element(By.ID, "btnLogin").click()
                log("✅ Login con campos por ID")
            except:
                # Opción 3: Por clase CSS
                try:
                    inputs = driver.find_elements(By.TAG_NAME, "input")
                    inputs[0].send_keys(USUARIO_CLUB)
                    inputs[1].send_keys(PASSWORD_CLUB)
                    driver.find_element(By.TAG_NAME, "button").click()
                    log("✅ Login con campos genéricos")
                except Exception as e:
                    log(f"❌ No se pudo hacer login: {e}")
                    return False
        
        time.sleep(3)
        return True
        
    except Exception as e:
        log(f"❌ Error en login: {e}")
        return False

def buscar_horarios(driver):
    """Busca horarios de 20-22 hs en la página"""
    try:
        log("🔍 Buscando horarios 20-22 hs...")
        
        # Ir a página de reservas
        driver.get(URL_RESERVAS)
        time.sleep(4)
        
        # Obtener HTML de la página
        html = driver.page_source.lower()
        
        # Palabras clave a buscar (en minúsculas)
        palabras_clave = [
            "20:00", "20 hs", "20hs", "20.00", 
            "20 a 22", "20-22", "20:00 a 22:00",
            "8 pm", "20h", "20:00hs"
        ]
        
        # Verificar cada palabra clave
        horarios_encontrados = []
        for palabra in palabras_clave:
            if palabra in html:
                horarios_encontrados.append(palabra)
                log(f"   ✅ Encontrado: {palabra}")
        
        if horarios_encontrados:
            return horarios_encontrados
        else:
            log("   📭 No se encontraron horarios 20-22")
            return []
            
    except Exception as e:
        log(f"❌ Error buscando horarios: {e}")
        return []

def intentar_reserva(driver, horario):
    """Intenta hacer la reserva automáticamente"""
    try:
        log(f"🎯 Intentando reservar: {horario}")
        
        # ESTA PARTE DEBES AJUSTARLA SEGÚN TU PÁGINA
        # Buscar botones que contengan el horario
        elementos = driver.find_elements(By.XPATH, f"//*[contains(text(), '{horario}')]")
        
        for elemento in elementos:
            try:
                # Buscar botón de reservar cercano
                btn_reservar = elemento.find_element(By.XPATH, "./following::button[contains(text(), 'Reservar') or contains(text(), 'reservar')]")
                btn_reservar.click()
                log(f"   ✅ Click en reservar para {horario}")
                
                # Esperar y confirmar si hay popup
                time.sleep(2)
                
                # Intentar encontrar botón de confirmar
                try:
                    confirmar = driver.find_element(By.XPATH, "//button[contains(text(), 'Confirmar') or contains(text(), 'confirmar')]")
                    confirmar.click()
                    log("   ✅ Reserva confirmada")
                    return True
                except:
                    log("   ⚠️ No hubo popup de confirmación")
                    return True
                    
            except:
                continue
        
        log("   ❌ No se encontró botón de reserva")
        return False
        
    except Exception as e:
        log(f"❌ Error en reserva automática: {e}")
        return False

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def ejecutar_monitor():
    """Función principal que ejecuta toda la verificación"""
    log("=" * 60)
    log("🤖 INICIANDO MONITOR DE RESERVAS")
    log("=" * 60)
    
    # Verificar que tenemos credenciales
    if not all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, USUARIO_CLUB, PASSWORD_CLUB]):
        log("❌ Faltan variables de configuración en GitHub Secrets")
        log("   Verifica: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, USUARIO_CLUB, PASSWORD_CLUB")
        return False
    
    # Enviar notificación de inicio
    mensaje_inicio = f"""
🤖 <b>Monitor de Reservas - EJECUCIÓN INICIADA</b>
📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
🔔 Verificando disponibilidad...
"""
    enviar_telegram(mensaje_inicio)
    
    driver = None
    reserva_exitosa = False
    
    try:
        # 1. Configurar navegador
        driver = setup_driver()
        if not driver:
            enviar_telegram("❌ Error configurando navegador")
            return False
        
        # 2. Hacer login
        if not hacer_login(driver):
            enviar_telegram("❌ Error en login - Revisar credenciales")
            return False
        
        # 3. Buscar horarios
        horarios = buscar_horarios(driver)
        
        if horarios:
            log(f"🎉 ¡HORARIOS ENCONTRADOS! {len(horarios)} disponibles")
            
            # Enviar alerta por cada horario encontrado
            for horario in horarios:
                mensaje_alerta = f"""
🚨 <b>¡HORARIO DISPONIBLE!</b> 🚨

🎾 <b>Club:</b> Tiro Federal
⏰ <b>Horario:</b> {horario}
📅 <b>Fecha detección:</b> {datetime.now().strftime('%d/%m %H:%M:%S')}
🔗 <b>Enlace:</b> {URL_RESERVAS}

⚡ <i>¡Corré a reservar!</i>
"""
                enviar_telegram(mensaje_alerta)
                
                # Intentar reservar automáticamente (opcional)
                if not reserva_exitosa:  # Solo intentar una vez
                    reserva_exitosa = intentar_reserva(driver, horario)
                    
                    if reserva_exitosa:
                        mensaje_exito = f"""
✅ <b>¡RESERVA AUTOMÁTICA EXITOSA!</b>

🎾 Horario reservado: {horario}
📅 Fecha: {datetime.now().strftime('%d/%m/%Y')}
🕒 Hora reserva: {datetime.now().strftime('%H:%M:%S')}

🏆 <i>¡Listo! Tenés la cancha</i>
"""
                        enviar_telegram(mensaje_exito)
                        break  # Salir del loop si ya reservó
            
            return True
            
        else:
            log("📭 No se encontraron horarios disponibles")
            mensaje_sin_disponibilidad = f"""
📭 <b>Sin disponibilidad</b>
🕒 {datetime.now().strftime('%H:%M:%S')}
⚠️ No hay horarios 20-22 disponibles
"""
            enviar_telegram(mensaje_sin_disponibilidad)
            return False
            
    except Exception as e:
        log(f"❌ ERROR CRÍTICO: {e}")
        enviar_telegram(f"❌ <b>Error en monitor:</b>\n{str(e)[:200]}")
        return False
        
    finally:
        if driver:
            try:
                driver.quit()
                log("✅ Navegador cerrado")
            except:
                pass
        
        # Mensaje final
        log("=" * 60)
        log("✅ EJECUCIÓN COMPLETADA")
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
