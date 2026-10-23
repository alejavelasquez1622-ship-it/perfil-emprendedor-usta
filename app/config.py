import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"
BACKUPS_DIR = DATA_DIR / "backups"
REPORTS_DIR = DATA_DIR / "reports"

# Ensure directories exist
for folder in [DATA_DIR, BACKUPS_DIR, REPORTS_DIR, STATIC_DIR / "img", STATIC_DIR / "css", STATIC_DIR / "js"]:
    folder.mkdir(parents=True, exist_ok=True)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'usta_perfil.db'}")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "usta-proyeccion-social-villavicencio-perfil-emprendedor-2026-key-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Institutional Identity
INSTITUTION_NAME = "Universidad Santo Tomás – Seccional Villavicencio"
INSTITUTION_SHORT = "USTA Villavicencio"
DEPENDENCY_NAME = "Dirección de Proyección Social"
SYSTEM_NAME = "Sistema de Análisis y Seguimiento del Perfil Emprendedor"
SYSTEM_VERSION = "1.0.0"

# Institutional Colors (Hex and RGB)
COLOR_NAVY_HEX = "#0B2545"
COLOR_NAVY_RGB = (11/255.0, 37/255.0, 69/255.0)

COLOR_GOLD_HEX = "#FDB813"
COLOR_GOLD_RGB = (253/255.0, 184/255.0, 19/255.0)

COLOR_RED_HEX = "#8B0000"
COLOR_RED_RGB = (139/255.0, 0/255.0, 0/255.0)

COLOR_LIGHT_BLUE_HEX = "#EBF3FA"
COLOR_LIGHT_BLUE_RGB = (235/255.0, 243/255.0, 250/255.0)

COLOR_TEXT_DARK_HEX = "#1F2937"
COLOR_BORDER_HEX = "#D1D5DB"

# Logo path
LOGO_PATH = STATIC_DIR / "img" / "logo_usta.png"

# Profile questions mapping (Exact mapping based on Microsoft Forms questionnaire)
PROFILE_QUESTIONS = {
    "P01_MOTIVACION": {
        "code": "P01",
        "title": "Motivación personal para emprender",
        "prompt": "Desde el punto de vista de la motivación, señale la respuesta que se identifique mejor con su posición personal."
    },
    "P02_GESTION_PROBLEMAS": {
        "code": "P02",
        "title": "Afrontamiento de problemas y errores",
        "prompt": "Ante los problemas que plantea la gestión de una empresa propia: ¿Cuál de estas respuestas le parece más adecuada?"
    },
    "P03_MOTIVACION_ECONOMICA": {
        "code": "P03",
        "title": "Importancia de la motivación económica",
        "prompt": "¿En qué medida la motivación económica es importante para usted?"
    },
    "P04_DINERO_PROPIO": {
        "code": "P04",
        "title": "Disponibilidad de capital propio",
        "prompt": "¿Cree usted que disponer de dinero propio para su empresa es importante?"
    },
    "P05_INICIATIVA": {
        "code": "P13",
        "title": "Iniciativa emprendedora",
        "prompt": "¿Con cuál de las siguientes definiciones se siente mas identificado?"
    },
    "P06_NUEVO_PROYECTO": {
        "code": "P14",
        "title": "Capacidad de reacción e incertidumbre",
        "prompt": "De cara al nuevo proyecto: ¿Cuál de esta afirmaciones podría hacer suya?"
    },
    "P07_TIEMPO_DEDICACION": {
        "code": "P15",
        "title": "Dedicación y equilibrio personal",
        "prompt": "¿Cuál es su postura ante el tiempo que debe dedicar a su empresa?"
    },
    "P08_INFLUENCIA_SOCIAL": {
        "code": "P16",
        "title": "Comunicación e influencia social",
        "prompt": "Ante su capacidad de relación e influencia social: ¿Cuál de estas afirmaciones está más de acuerdo?"
    },
    "P09_FUNCION_COMERCIAL": {
        "code": "P17",
        "title": "Orientación comercial y ventas",
        "prompt": "En cuanto a la función comercial: ¿con qué respuesta se siente más identificado?"
    },
    "P10_LIDERAZGO": {
        "code": "P18",
        "title": "Dotes de liderazgo para dirigir",
        "prompt": "¿Considera que es necesario tener dotes de liderazgo para dirigir una empresa?"
    },
    "P11_SATISFACCION_LOGROS": {
        "code": "P19",
        "title": "Satisfacción de logros y validación",
        "prompt": "Ante la satisfacción de haber acertado con una solución, ¿Qué considero adecuada?"
    },
    "P12_ACTITUD_RIESGO": {
        "code": "P20",
        "title": "Actitud frente al riesgo",
        "prompt": "¿EN QUÉ MEDIDA CONSIDERA QUE HAY QUE ARRIESGARSE AL TOMAR DECISIONES?"
    },
    "P13_VALIDACION_VIABILIDAD": {
        "code": "P21",
        "title": "Validación y viabilidad de ideas",
        "prompt": "¿Considera que tiene una idea que le va a permitir montar una empresa?"
    }
}

# Standard INNPulsa Stages order
INNPULSA_STAGES = [
    "Pre-semilla",
    "Semilla",
    "Temprana",
    "Consolidación",
    "Escalamiento"
]
