# agent/main.py — Servidor FastAPI + Webhook de WhatsApp
# Generado por AgentKit

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from agent.brain import generar_respuesta
from agent.memory import inicializar_db, guardar_mensaje, obtener_historial
from agent.providers import obtener_proveedor

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
log_level = logging.DEBUG if ENVIRONMENT == "development" else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger("agentkit")

PORT = int(os.getenv("PORT", 8000))

# El proveedor se inicializa en el lifespan para asegurar que las variables
# de entorno ya estén disponibles (especialmente en Railway/producción)
proveedor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa el proveedor y la base de datos al arrancar el servidor."""
    global proveedor
    proveedor = obtener_proveedor()
    await inicializar_db()
    logger.info("Base de datos inicializada")
    logger.info(f"Servidor AgentKit corriendo en puerto {PORT}")
    logger.info(f"Proveedor de WhatsApp: {proveedor.__class__.__name__}")
    yield


app = FastAPI(
    title="AgentKit — MONTELOMA WhatsApp Agent",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def health_check():
    """Endpoint de salud para Railway/monitoreo."""
    return {"status": "ok", "service": "agentkit-monteloma"}


@app.get("/debug")
async def debug_env():
    """Diagnóstico de variables de entorno — eliminar en producción."""
    return {
        "ANTHROPIC_API_KEY": "SET" if os.getenv("ANTHROPIC_API_KEY") else "NOT SET",
        "WHATSAPP_PROVIDER": os.getenv("WHATSAPP_PROVIDER", "NOT SET"),
        "TWILIO_ACCOUNT_SID": "SET" if os.getenv("TWILIO_ACCOUNT_SID") else "NOT SET",
        "TWILIO_AUTH_TOKEN": "SET" if os.getenv("TWILIO_AUTH_TOKEN") else "NOT SET",
        "TWILIO_PHONE_NUMBER": os.getenv("TWILIO_PHONE_NUMBER", "NOT SET"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "NOT SET"),
        "PORT": os.getenv("PORT", "NOT SET"),
    }


@app.get("/webhook")
async def webhook_verificacion(request: Request):
    """Verificación GET del webhook (requerido por Meta Cloud API, no-op para Twilio)."""
    resultado = await proveedor.validar_webhook(request)
    if resultado is not None:
        return PlainTextResponse(str(resultado))
    return {"status": "ok"}


@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Recibe mensajes de WhatsApp via Twilio.
    Procesa el mensaje, genera respuesta con Claude y la envía de vuelta.
    """
    try:
        mensajes = await proveedor.parsear_webhook(request)

        for msg in mensajes:
            if msg.es_propio or not msg.texto:
                continue

            logger.info(f"Mensaje de {msg.telefono}: {msg.texto}")

            # Obtener historial ANTES de guardar el mensaje actual
            historial = await obtener_historial(msg.telefono)

            respuesta = await generar_respuesta(msg.texto, historial)

            await guardar_mensaje(msg.telefono, "user", msg.texto)
            await guardar_mensaje(msg.telefono, "assistant", respuesta)

            await proveedor.enviar_mensaje(msg.telefono, respuesta)

            logger.info(f"Respuesta a {msg.telefono}: {respuesta}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
