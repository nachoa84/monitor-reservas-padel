# 🤖 Monitor Automático de Reservas de Pádel

Sistema automático que monitorea y reserva horarios de pádel en el club.

## 🚀 Cómo funciona

1. Se ejecuta automáticamente en GitHub según horarios programados
2. Verifica si hay horarios disponibles de 20-22 hs
3. Envía alerta por Telegram
4. Intenta reservar automáticamente

## ⚙️ Configuración

### 1. Configurar Secrets en GitHub

Ve a: Settings → Secrets and variables → Actions → New repository secret

Agrega estos 4 secrets:

| Secret Name | Valor |
|-------------|-------|
| `TELEGRAM_TOKEN` | Token de tu bot de Telegram |
| `TELEGRAM_CHAT_ID` | Tu Chat ID de Telegram |
| `USUARIO_CLUB` | Tu usuario del club |
| `PASSWORD_CLUB` | Tu contraseña del club |

### 2. Configurar URLs en monitor.py

Edita `monitor.py` y cambia:
- `URL_LOGIN` = URL donde haces login en el club
- `URL_RESERVAS` = URL donde ves/reservas canchas

### 3. Ajustar selectores

En `monitor.py`, función `hacer_login()`, ajusta los selectores según tu página web.

## 📅 Horarios de ejecución

Se ejecuta automáticamente:
- **Miércoles:** 21:50 a 23:50 (cada 10 minutos)
- **Jueves:** 06:00 a 08:00 (cada 15 minutos)

## 🔧 Ejecución manual

Puedes ejecutar manualmente desde GitHub:
1. Ve a "Actions"
2. Click en "🤖 Monitor Reservas Pádel"
3. Click "Run workflow"

## 📱 Notificaciones

Recibirás alertas por Telegram cuando:
- Se inicie una verificación
- Se encuentren horarios disponibles
- Se realice una reserva exitosa
- Ocurra un error
