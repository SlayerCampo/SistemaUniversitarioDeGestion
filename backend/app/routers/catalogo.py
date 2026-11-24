from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.horarios import codigo_base_asignatura, validar_bloque_institucional
from app.core.security import hash_password, require_roles
from app.db.models import (
    Asignatura,
    Estudiante,
    Facultad,
    Grupo,
    HorarioGrupo,
    Matricula,
    Nota,
    Periodo,
    Programa,
    Usuario,
)
from app.db.session import get_db
from app.schemas import EstudianteCreate, FacultadCreate, GrupoOfertaCreate, ProgramaCreate
from app.services.matricula_service import serializar_grupo

router = APIRouter(prefix="/catalogo", tags=["Catálogo y Administración"])


@router.get("/kpis")
def obtener_kpis(db: Session = Depends(get_db)):
    facs = db.scalar(select(func.count(Facultad.id_facultad))) or 0
    progs = db.scalar(select(func.count(Programa.id_programa))) or 0
    asigs = db.scalar(select(func.count(Asignatura.id_asignatura))) or 0
    grupos = db.scalar(select(func.count(Grupo.id_grupo))) or 0
    ests = db.scalar(select(func.count(Estudiante.id_estudiante))) or 0
    mats = db.scalar(select(func.count(Matricula.id_matricula)).where(Matricula.estado == "Activa")) or 0
    prom = db.scalar(select(func.avg(Nota.definitiva)).where(Nota.estado != "Sin calificar"))
    periodo_activo = db.scalar(select(Periodo.id_periodo).where(Periodo.activo.is_(True))) or settings.PERIODO_ACTIVO_DEFECTO

    return {
        "facultades": int(facs),
        "programas": int(progs),
        "asignaturas": int(asigs),
        "grupos": int(grupos),
        "estudiantes": int(ests),
        "matriculas_activas": int(mats),
        "promedio_global": round(float(prom), 2) if prom is not None else 0.0,
        "periodo_activo": periodo_activo,
        "demo_mode": settings.DEMO_MODE,
    }


@router.get("/facultades")
def listar_facultades(db: Session = Depends(get_db)):
    rows = db.execute(select(Facultad).order_by(Facultad.id_facultad)).scalars().all()
    return [
        {"id_facultad": f.id_facultad, "nombre_facultad": f.nombre_facultad, "decano": f.decano}
        for f in rows
    ]


@router.post("/facultades", status_code=201)
def crear_facultad(
    body: FacultadCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    fid = body.id_facultad.strip().upper()
    if db.get(Facultad, fid):
        raise HTTPException(status_code=409, detail=f"La facultad '{fid}' ya existe.")
    obj = Facultad(id_facultad=fid, nombre_facultad=body.nombre_facultad.strip(), decano=body.decano.strip() or "Por asignar")
    db.add(obj)
    db.commit()
    return {"id_facultad": obj.id_facultad, "nombre_facultad": obj.nombre_facultad, "decano": obj.decano}


@router.delete("/facultades/{id_facultad}")
def eliminar_facultad(
    id_facultad: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    obj = db.get(Facultad, id_facultad)
    if not obj:
        raise HTTPException(status_code=404, detail="Facultad no encontrada.")
    try:
        db.delete(obj)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se puede eliminar: existen programas asociados a esta facultad.")
    return {"mensaje": "Facultad eliminada."}


@router.get("/programas")
def listar_programas(db: Session = Depends(get_db)):
    rows = db.execute(select(Programa).options(selectinload(Programa.facultad)).order_by(Programa.id_programa)).scalars().all()
    return [
        {
            "id_programa": p.id_programa,
            "nombre_programa": p.nombre_programa,
            "id_facultad": p.id_facultad,
            "nombre_facultad": p.facultad.nombre_facultad if p.facultad else p.id_facultad,
            "semestres_duracion": p.semestres_duracion,
        }
        for p in rows
    ]


@router.post("/programas", status_code=201)
def crear_programa(
    body: ProgramaCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    pid = body.id_programa.strip().upper()
    fid = body.id_facultad.strip().upper()
    if db.get(Programa, pid):
        raise HTTPException(status_code=409, detail=f"El programa '{pid}' ya existe.")
    if not db.get(Facultad, fid):
        raise HTTPException(status_code=404, detail=f"La facultad '{fid}' no existe.")
    obj = Programa(
        id_programa=pid,
        nombre_programa=body.nombre_programa.strip(),
        id_facultad=fid,
        semestres_duracion=body.semestres_duracion,
    )
    db.add(obj)
    db.commit()
    return {"id_programa": obj.id_programa, "nombre_programa": obj.nombre_programa, "id_facultad": obj.id_facultad}


@router.delete("/programas/{id_programa}")
def eliminar_programa(
    id_programa: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    obj = db.get(Programa, id_programa)
    if not obj:
        raise HTTPException(status_code=404, detail="Programa no encontrado.")
    try:
        db.delete(obj)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se puede eliminar: existen asignaturas o estudiantes asociados.")
    return {"mensaje": "Programa eliminado."}


@router.get("/grupos")
def listar_grupos(
    id_programa: str | None = Query(default=None),
    search: str | None = Query(default=None),
    id_periodo: str = Query(default=settings.PERIODO_ACTIVO_DEFECTO),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Grupo)
        .join(Asignatura, Grupo.id_asignatura == Asignatura.id_asignatura)
        .options(
            selectinload(Grupo.asignatura).selectinload(Asignatura.programa),
            selectinload(Grupo.horarios),
        )
        .where(Grupo.id_periodo == id_periodo)
        .order_by(Grupo.id_grupo)
    )
    if id_programa:
        stmt = stmt.where(Asignatura.id_programa == id_programa)

    grupos = db.execute(stmt).scalars().all()
    resultado = [serializar_grupo(g) for g in grupos]
    if search and search.strip():
        q = search.strip().lower()
        resultado = [
            g for g in resultado
            if q in g["id_grupo"].lower()
            or q in g["nombre_curso"].lower()
            or q in g["docente"].lower()
            or q in g["horario_texto"].lower()
            or q in g["nombre_programa"].lower()
        ]
    return resultado


@router.post("/grupos", status_code=201)
def crear_grupo_oferta(
    body: GrupoOfertaCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    gid = body.id_grupo.strip().upper()
    pid = body.id_programa.strip().upper()
    cod_asig = (body.id_asignatura or codigo_base_asignatura(gid)).strip().upper()

    if not db.get(Programa, pid):
        raise HTTPException(status_code=404, detail=f"El programa '{pid}' no existe.")
    if db.get(Grupo, gid):
        raise HTTPException(status_code=409, detail=f"El grupo '{gid}' ya existe.")

    for h in body.horarios:
        ok, msg = validar_bloque_institucional(h.dia_semana, h.hora_inicio, h.hora_fin, body.creditos)
        if not ok:
            raise HTTPException(status_code=400, detail=msg)

    if not db.get(Periodo, settings.PERIODO_ACTIVO_DEFECTO):
        db.add(Periodo(id_periodo=settings.PERIODO_ACTIVO_DEFECTO, activo=True))
        db.flush()

    if not db.get(Asignatura, cod_asig):
        db.add(Asignatura(id_asignatura=cod_asig, nombre_curso=body.nombre_curso.strip(), creditos=body.creditos, id_programa=pid))
        db.flush()

    grupo = Grupo(
        id_grupo=gid,
        id_asignatura=cod_asig,
        id_periodo=settings.PERIODO_ACTIVO_DEFECTO,
        docente=body.docente.strip(),
        cupos_totales=body.cupos_totales,
        cupos_disponibles=body.cupos_totales,
    )
    db.add(grupo)
    for h in body.horarios:
        db.add(HorarioGrupo(id_grupo=gid, dia_semana=h.dia_semana, hora_inicio=h.hora_inicio, hora_fin=h.hora_fin))

    db.commit()
    grupo_full = db.execute(
        select(Grupo)
        .options(selectinload(Grupo.asignatura).selectinload(Asignatura.programa), selectinload(Grupo.horarios))
        .where(Grupo.id_grupo == gid)
    ).scalar_one()
    return serializar_grupo(grupo_full)


@router.delete("/grupos/{id_grupo}")
def eliminar_grupo(
    id_grupo: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    obj = db.get(Grupo, id_grupo)
    if not obj:
        raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    try:
        db.delete(obj)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se puede eliminar: existen matrículas asociadas a este grupo.")
    return {"mensaje": "Grupo eliminado."}


@router.get("/estudiantes")
def listar_estudiantes(
    id_programa: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador", "Profesor")),
):
    stmt = select(Estudiante).options(selectinload(Estudiante.programa)).order_by(Estudiante.id_estudiante)
    if id_programa:
        stmt = stmt.where(Estudiante.id_programa == id_programa)
    rows = db.execute(stmt).scalars().all()
    data = [
        {
            "id_estudiante": e.id_estudiante,
            "nombre": e.nombre,
            "apellidos": e.apellidos,
            "nombre_completo": f"{e.nombre} {e.apellidos}",
            "correo": e.correo,
            "telefono": e.telefono,
            "semestre": e.semestre,
            "id_programa": e.id_programa,
            "nombre_programa": e.programa.nombre_programa if e.programa else e.id_programa,
        }
        for e in rows
    ]
    if search and search.strip():
        q = search.strip().lower()
        data = [
            e for e in data
            if q in e["id_estudiante"].lower()
            or q in e["nombre_completo"].lower()
            or q in e["correo"].lower()
            or q in e["nombre_programa"].lower()
        ]
    return data


@router.post("/estudiantes", status_code=201)
def crear_estudiante(
    body: EstudianteCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    eid = body.id_estudiante.strip()
    pid = body.id_programa.strip().upper()
    if db.get(Estudiante, eid):
        raise HTTPException(status_code=409, detail=f"El estudiante con ID '{eid}' ya existe.")
    if not db.get(Programa, pid):
        raise HTTPException(status_code=404, detail=f"El programa '{pid}' no existe.")

    est = Estudiante(
        id_estudiante=eid,
        nombre=body.nombre.strip(),
        apellidos=body.apellidos.strip(),
        correo=body.correo.strip(),
        telefono=body.telefono.strip(),
        semestre=body.semestre,
        id_programa=pid,
    )
    db.add(est)
    if not db.get(Usuario, eid):
        db.add(
            Usuario(
                usuario=eid,
                password_hash=hash_password(body.password),
                rol="Estudiante",
                nombre_completo=f"{est.nombre} {est.apellidos}",
                documento_asociado=eid,
            )
        )
    db.commit()
    return {"id_estudiante": est.id_estudiante, "nombre_completo": f"{est.nombre} {est.apellidos}", "id_programa": pid}


@router.delete("/estudiantes/{id_estudiante}")
def eliminar_estudiante(
    id_estudiante: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    obj = db.get(Estudiante, id_estudiante)
    if not obj:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado.")
    try:
        usr = db.get(Usuario, id_estudiante)
        if usr:
            db.delete(usr)
        db.delete(obj)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se puede eliminar: el estudiante tiene matrículas registradas.")
    return {"mensaje": "Estudiante eliminado."}


@router.get("/analitica")
def obtener_analitica(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador", "Profesor")),
):
    est_por_prog = db.execute(
        select(Programa.id_programa, Programa.nombre_programa, func.count(Estudiante.id_estudiante))
        .outerjoin(Estudiante, Programa.id_programa == Estudiante.id_programa)
        .group_by(Programa.id_programa, Programa.nombre_programa)
        .order_by(Programa.id_programa)
    ).all()

    ocup_por_prog = db.execute(
        select(
            Programa.id_programa,
            Programa.nombre_programa,
            func.coalesce(func.sum(Grupo.cupos_totales), 0),
            func.coalesce(func.sum(Grupo.cupos_disponibles), 0),
        )
        .outerjoin(Asignatura, Programa.id_programa == Asignatura.id_programa)
        .outerjoin(Grupo, Asignatura.id_asignatura == Grupo.id_asignatura)
        .group_by(Programa.id_programa, Programa.nombre_programa)
        .order_by(Programa.id_programa)
    ).all()

    notas_estado = db.execute(
        select(Nota.estado, func.count(Nota.id_nota)).group_by(Nota.estado)
    ).all()

    return {
        "estudiantes_por_programa": [
            {"id_programa": r[0], "programa": r[1], "estudiantes": int(r[2])}
            for r in est_por_prog
        ],
        "ocupacion_por_programa": [
            {
                "id_programa": r[0],
                "programa": r[1],
                "cupos_totales": int(r[2]),
                "cupos_ocupados": int(r[2]) - int(r[3]),
                "cupos_disponibles": int(r[3]),
            }
            for r in ocup_por_prog
        ],
        "distribucion_notas": [
            {"estado": r[0], "cantidad": int(r[1])}
            for r in notas_estado
        ],
    }
