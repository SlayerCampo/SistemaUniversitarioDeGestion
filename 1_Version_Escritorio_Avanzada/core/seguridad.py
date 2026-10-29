from __future__ import annotations
# ==============================================================================
# ARCHIVO: core/seguridad.py
# PROPÓSITO: Gestionar la autenticación de usuarios, encriptación de contraseñas
#            mediante SHA-256 (hashlib) y control de acceso basado en roles (RBAC).
# ==============================================================================

import hashlib
import data.db_excel as db

# Cuentas maestras de respaldo por si la hoja Usuarios aún no ha sido poblada.
# La cuenta "estudiante" es el acceso de demostración: permite elegir con qué
# estudiante registrado actuar. Los estudiantes reales ingresan con su propia
# cédula y solo pueden operar sobre su propia información.
USUARIOS_POR_DEFECTO = {
    "admin": ("1234", "Administrador", "Administrador General UCC", "0000"),
    "profe": ("1234", "Profesor", "Docente UCC", "9001"),
    "estudiante": ("1234", "Estudiante", "Modo Demostración", ""),
}


def encriptar_password(password_plano: str) -> str:
    """Genera el hash SHA-256 hexadecimal de una contraseña."""
    return hashlib.sha256(password_plano.strip().encode("utf-8")).hexdigest()


def autenticar_usuario(usuario_input: str, password_input: str) -> tuple[bool, dict]:
    """
    Verifica las credenciales del usuario contra:
    1. La hoja 'Usuarios' de la base de datos Excel (con contraseña encriptada o texto plano).
    2. Las cuentas maestras por defecto ('admin', 'profe' y 'estudiante' en modo demostración).
    3. La cédula de cualquier estudiante registrado en la hoja 'Estudiantes'
       (usando como contraseña su propia cédula o '1234' para pruebas).

    Retorna:
        (True, {"usuario": ..., "rol": ..., "nombre": ..., "documento": ...})
        o (False, {"mensaje": ...})
    """
    user = usuario_input.strip()
    pwd = password_input.strip()

    if not user or not pwd:
        return False, {"mensaje": "Ingrese usuario y contraseña."}

    pwd_hash = encriptar_password(pwd)

    # 1. Buscar en la hoja Usuarios de la base de datos
    filas_usuarios = db.obtener_datos("Usuarios")
    for fila in filas_usuarios:
        if len(fila) >= 4 and str(fila[0]).strip() == user:
            almacenado = str(fila[1]).strip()
            if almacenado == pwd_hash or almacenado == pwd:
                return True, {
                    "usuario": user,
                    "rol": str(fila[2]).strip(),
                    "nombre": str(fila[3]).strip(),
                    "documento": str(fila[4]).strip() if len(fila) > 4 and fila[4] else ""
                }

    # 2. Verificar cuentas por defecto
    if user in USUARIOS_POR_DEFECTO:
        pwd_def, rol_def, nom_def, doc_def = USUARIOS_POR_DEFECTO[user]
        if pwd == pwd_def or (doc_def and pwd == doc_def):
            return True, {
                "usuario": user,
                "rol": rol_def,
                "nombre": nom_def,
                "documento": doc_def,
                # Solo el acceso de demostración puede cambiar de estudiante
                "modo_demo": user == "estudiante"
            }

    # 3. Permitir a cualquier estudiante registrado ingresar con su cédula
    filas_estudiantes = db.obtener_datos("Estudiantes")
    for est in filas_estudiantes:
        cedula_est = str(est[0]).strip()
        if cedula_est == user and (pwd == cedula_est or pwd == "1234"):
            nombre_completo = f"{est[1]} {est[2]}"
            return True, {
                "usuario": cedula_est,
                "rol": "Estudiante",
                "nombre": nombre_completo,
                "documento": cedula_est
            }

    return False, {"mensaje": "Usuario o contraseña incorrectos."}
