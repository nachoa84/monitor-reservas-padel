def setup_driver():
    """Configura el navegador Chrome usando webdriver-manager"""
    # Configuración específica para GitHub Actions
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        os.environ['WDM_LOCAL'] = '0'
        os.environ['WDM_SSL_VERIFY'] = '0'
        os.environ['WDM_LOG_LEVEL'] = '0'
    
    # ¡IMPORTANTE: Crear el objeto chrome_options!
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
