# agent/tools.py — Herramientas del agente MONTELOMA
# Generado por AgentKit

import os
import yaml
import logging
from datetime import datetime

logger = logging.getLogger("agentkit")


def cargar_info_negocio() -> dict:
    """Carga la información del negocio desde business.yaml."""
    try:
        with open("config/business.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("config/business.yaml no encontrado")
        return {}


def obtener_catalogo() -> list[dict]:
    """Retorna el catálogo completo de cafés MONTELOMA."""
    return [
        {"variedad": "Pink Bourbon",      "origen": "Quindío",   "precio": 80000, "notas": "Lychee, floral, fresa, caramelo"},
        {"variedad": "Sudán Rumé Lavado", "origen": "Quindío",   "precio": 80000, "notas": "Floral, especias dulces, herbal, cardamomo, jengibre, romero"},
        {"variedad": "Gesha",             "origen": "Risaralda", "precio": 65000, "notas": "Limoncillo, jazmín, lima"},
        {"variedad": "Bourbon Rojo",      "origen": "Huila",     "precio": 70000, "notas": "Floral, bergamota, menta"},
        {"variedad": "Chiroso Natural",   "origen": "Quindío",   "precio": 70000, "notas": "Lima, ciruela, pasas, cacao, caramelo"},
        {"variedad": "Wush Wush",         "origen": "Quindío",   "precio": 80000, "notas": "Azúcar morena, hibiscus, chocolate, fruta de la pasión"},
        {"variedad": "Castillo Mora",     "origen": "Quindío",   "precio": 70000, "notas": "Mora, caramelo, chocolate negro"},
    ]


def recomendar_cafe(gusto: str) -> list[dict]:
    """
    Recomienda cafés según el gusto del cliente.

    Args:
        gusto: "dulce", "frutal", "floral", "exotico", "regalo", "leche", "negro", "espresso"

    Returns:
        Lista de cafés recomendados
    """
    catalogo = obtener_catalogo()
    gusto = gusto.lower()

    recomendaciones = {
        "dulce":    ["Castillo Mora", "Pink Bourbon"],
        "frutal":   ["Chiroso Natural", "Wush Wush"],
        "floral":   ["Gesha", "Bourbon Rojo"],
        "exotico":  ["Sudán Rumé Lavado", "Wush Wush"],
        "regalo":   ["Gesha", "Pink Bourbon", "Wush Wush"],
        "leche":    ["Castillo Mora", "Chiroso Natural", "Wush Wush"],
        "negro":    ["Gesha", "Pink Bourbon", "Bourbon Rojo", "Chiroso Natural"],
        "espresso": ["Castillo Mora", "Chiroso Natural", "Wush Wush"],
        "principiante": ["Castillo Mora", "Gesha"],
        "exclusivo": ["Sudán Rumé Lavado", "Wush Wush", "Pink Bourbon"],
    }

    nombres = recomendaciones.get(gusto, [])
    return [c for c in catalogo if c["variedad"] in nombres]


def obtener_molienda(metodo: str) -> str:
    """Retorna el tipo de molienda recomendado para el método de preparación."""
    metodo = metodo.lower()
    moliendas = {
        "espresso": "fina",
        "moka": "media-fina",
        "italiana": "media-fina",
        "v60": "media",
        "chemex": "media",
        "origami": "media",
        "prensa francesa": "gruesa",
        "french press": "gruesa",
        "cafetera electrica": "media",
        "cafetera eléctrica": "media",
        "colador": "media",
        "tradicional": "media",
    }
    for clave, molienda in moliendas.items():
        if clave in metodo:
            return molienda
    return "media (para método no especificado)"


def calcular_pedido(variedades: list[dict]) -> dict:
    """
    Calcula el total de un pedido.

    Args:
        variedades: [{"variedad": "Gesha", "cantidad": 2}, ...]

    Returns:
        Resumen del pedido con total
    """
    catalogo = {c["variedad"]: c["precio"] for c in obtener_catalogo()}
    items = []
    total = 0

    for item in variedades:
        nombre = item.get("variedad", "")
        cantidad = item.get("cantidad", 1)
        precio_unitario = catalogo.get(nombre, 0)
        subtotal = precio_unitario * cantidad
        total += subtotal
        items.append({
            "variedad": nombre,
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "subtotal": subtotal,
        })

    return {
        "items": items,
        "total_productos": total,
        "nota": "El costo de envío se calcula según ciudad de destino",
    }


def obtener_horario() -> dict:
    """Retorna el horario de atención del negocio."""
    info = cargar_info_negocio()
    return {
        "horario": info.get("negocio", {}).get("horario", "Lunes a Domingo, 1am a 12pm"),
        "esta_abierto": True,
    }


def buscar_en_knowledge(consulta: str) -> str:
    """Busca información en los archivos de /knowledge."""
    resultados = []
    knowledge_dir = "knowledge"

    if not os.path.exists(knowledge_dir):
        return "No hay archivos de conocimiento disponibles."

    for archivo in os.listdir(knowledge_dir):
        ruta = os.path.join(knowledge_dir, archivo)
        if archivo.startswith(".") or not os.path.isfile(ruta):
            continue
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
                if consulta.lower() in contenido.lower():
                    resultados.append(f"[{archivo}]: {contenido[:500]}")
        except (UnicodeDecodeError, IOError):
            continue

    if resultados:
        return "\n---\n".join(resultados)
    return "No encontré información específica sobre eso en mis archivos."
