import React, { useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { AlertTriangle, CheckCircle2, Download, ExternalLink, Monitor, ShieldCheck, Smartphone } from "lucide-react";
import { GITHUB_RELEASES_URL } from "@/lib/api";
import { detectPlatform } from "@/lib/platform";
import { Badge, Button, Card, StepHeader } from "@/components/ui/Primitives";

export function DescargasPage() {
  const platform = detectPlatform();
  const isAndroid = platform === "web-android" || platform === "capacitor-android";
  const isIOS = platform === "web-ios";
  const isMobile = isAndroid || isIOS;
  const [confirmDesktopOnMobile, setConfirmDesktopOnMobile] = useState(false);

  const apkUrl = `${GITHUB_RELEASES_URL}/latest/download/UCC_Academico_v2.apk`;
  const exeUrl = `${GITHUB_RELEASES_URL}/latest/download/Instalador_UCC_Academico_v2_Setup.exe`;

  return (
    <div className="space-y-6">
      <Card className="p-5 sm:p-6 space-y-3">
        <StepHeader
          step="MULTIPLATAFORMA"
          title="Descarga la App Oficial para tu Dispositivo"
          subtitle="Mismo diseño, misma base de datos PostgreSQL en tiempo real en Web, Windows (.exe) y Android (.apk)."
          action={
            <Badge variant="blue">
              Detectado:{" "}
              {isAndroid
                ? "Teléfono Android"
                : isIOS
                  ? "iPhone / iPad"
                  : "Computador de Escritorio"}
            </Badge>
          }
        />

        {isIOS && (
          <div className="p-4 rounded-xl bg-sky-50 border border-sky-200 text-sm text-[#154B75]">
            <b>Estás en iPhone / iPad:</b> puedes usar la versión web directamente o tocar el botón <b>Compartir</b> de
            Safari → <b>“Agregar a pantalla de inicio”</b> para instalarla como aplicación.
          </div>
        )}
      </Card>

      {/* ORDEN INTELIGENTE: EN ANDROID SUBE EL APK PRIMERO; EN PC SUBE EL EXE PRIMERO */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* TARJETA WINDOWS DESKTOP (.exe) */}
        <Card
          className={`p-6 flex flex-col justify-between gap-5 ${
            !isMobile ? "ring-2 ring-[#1F6AA5] order-1" : "order-2 opacity-95"
          }`}
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-2">
              <div className="p-3 rounded-2xl bg-sky-50 text-[#1F6AA5]">
                <Monitor className="w-7 h-7" />
              </div>
              {!isMobile ? <Badge variant="green">Recomendado para tu dispositivo</Badge> : <Badge variant="amber">Solo Windows PC</Badge>}
            </div>

            <div>
              <h3 className="font-display font-extrabold text-xl text-slate-900">App de Escritorio Windows (.exe)</h3>
              <p className="text-sm text-slate-600 mt-1 leading-relaxed">
                Instalador profesional ligero (<b>Tauri + Inno Setup</b>) con logotipo oficial UCC, asistente
                “Siguiente → Instalar” y creación automática de acceso directo en el Escritorio.
              </p>
            </div>

            <ul className="space-y-1.5 text-xs text-slate-600">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                No requiere Python ni descomprimir archivos ZIP
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                Selector de servidor integrado (Nube o Docker local para sustentación)
              </li>
            </ul>
          </div>

          <div className="space-y-3">
            {isMobile ? (
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-2.5">
                <div className="flex items-start gap-2 text-xs text-amber-900">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-700" />
                  <span>
                    <b>Aviso móvil:</b> Los archivos <code>.exe</code> no se ejecutan en celulares. Si deseas
                    descargarlo para transferirlo a un PC con Windows, confirma abajo:
                  </span>
                </div>
                <label className="flex items-center gap-2 text-xs font-semibold text-amber-950 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={confirmDesktopOnMobile}
                    onChange={(e) => setConfirmDesktopOnMobile(e.target.checked)}
                    className="rounded border-amber-400"
                  />
                  Entiendo que es solo para PC y deseo descargarlo para transferirlo.
                </label>
                {confirmDesktopOnMobile && (
                  <a href={exeUrl} target="_blank" rel="noreferrer" className="block">
                    <Button variant="outline" className="w-full">
                      <Download className="w-4 h-4" /> Descargar Instalador Windows (.exe)
                    </Button>
                  </a>
                )}
              </div>
            ) : (
              <div className="space-y-2">
                <a href={exeUrl} target="_blank" rel="noreferrer" className="block">
                  <Button size="lg" className="w-full">
                    <Download className="w-4 h-4" />
                    Descargar Instalador Windows (.exe)
                  </Button>
                </a>
                <a href={GITHUB_RELEASES_URL} target="_blank" rel="noreferrer" className="block">
                  <Button variant="outline" size="sm" className="w-full">
                    <ExternalLink className="w-3.5 h-3.5" />
                    Ver todas las versiones en GitHub Releases
                  </Button>
                </a>
              </div>
            )}
          </div>
        </Card>

        {/* TARJETA ANDROID (.apk) */}
        <Card
          className={`p-6 flex flex-col justify-between gap-5 ${
            isAndroid ? "ring-2 ring-emerald-600 order-1" : "order-2"
          }`}
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-2">
              <div className="p-3 rounded-2xl bg-emerald-50 text-emerald-700">
                <Smartphone className="w-7 h-7" />
              </div>
              {isAndroid ? <Badge variant="green">Recomendado para tu celular</Badge> : <Badge variant="cyan">Android 8.0+</Badge>}
            </div>

            <div>
              <h3 className="font-display font-extrabold text-xl text-slate-900">App Móvil Android (.apk)</h3>
              <p className="text-sm text-slate-600 mt-1 leading-relaxed">
                Aplicación Android instalable (<b>Capacitor</b>) con el logotipo oficial de la UCC, pantalla de carga
                institucional, navegación inferior adaptada al pulgar y descarga nativa de boletines PDF.
              </p>
            </div>

            {!isMobile && (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-4">
                <div className="bg-white p-2 rounded-xl border border-slate-200 shrink-0">
                  <QRCodeSVG value={GITHUB_RELEASES_URL} size={84} fgColor="#154B75" />
                </div>
                <div className="text-xs text-slate-600 space-y-1">
                  <p className="font-bold text-slate-900">Escanea desde tu celular</p>
                  <p>Apunta la cámara de tu Android para abrir los Releases y descargar el archivo <b>.apk</b> al instante.</p>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <a href={apkUrl} target="_blank" rel="noreferrer" className="block">
              <Button variant="success" size="lg" className="w-full">
                <Download className="w-4 h-4" />
                Descargar App Android (.apk)
              </Button>
            </a>
            <a href={GITHUB_RELEASES_URL} target="_blank" rel="noreferrer" className="block">
              <Button variant="outline" size="sm" className="w-full">
                <ExternalLink className="w-3.5 h-3.5" />
                Abrir GitHub Releases
              </Button>
            </a>
          </div>
        </Card>
      </div>

      {/* NOTA DE TRANSPARENCIA */}
      <Card className="p-4 sm:p-5 bg-slate-50 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-[#1F6AA5] shrink-0 mt-0.5" />
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          <b>Transparencia académica:</b> Tanto el instalador de Windows (<code>.exe</code>) como la app Android (
          <code>.apk</code>) se compilan directamente desde el código fuente abierto de este repositorio. Si Windows
          SmartScreen o Android muestran el aviso estándar de aplicación de origen académico, selecciona{" "}
          <b>“Más información → Ejecutar de todas formas”</b> (Windows) o <b>“Instalar de todas formas”</b> (Android).
        </p>
      </Card>
    </div>
  );
}
