import { Capacitor } from "@capacitor/core";
import { Directory, Filesystem } from "@capacitor/filesystem";
import { Share } from "@capacitor/share";

export type PlatformKind = "tauri" | "capacitor-android" | "web-windows" | "web-android" | "web-ios" | "web-other";

export function isTauriApp(): boolean {
  return typeof window !== "undefined" && ("__TAURI_INTERNALS__" in window || "__TAURI__" in window);
}

export function isCapacitorApp(): boolean {
  return Capacitor.isNativePlatform();
}

export function detectPlatform(): PlatformKind {
  if (isTauriApp()) return "tauri";
  if (isCapacitorApp()) return "capacitor-android";
  const ua = typeof navigator !== "undefined" ? navigator.userAgent.toLowerCase() : "";
  if (/android/.test(ua)) return "web-android";
  if (/iphone|ipad|ipod/.test(ua)) return "web-ios";
  if (/win/.test(ua)) return "web-windows";
  return "web-other";
}

export function isMobileDevice(): boolean {
  const p = detectPlatform();
  return p === "capacitor-android" || p === "web-android" || p === "web-ios";
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = reject;
    reader.onload = () => {
      const result = String(reader.result || "");
      resolve(result.includes(",") ? result.split(",")[1] : result);
    };
    reader.readAsDataURL(blob);
  });
}

/**
 * Descarga archivos PDF o Excel de forma compatible con:
 * - Navegador Web (PC y Móvil)
 * - Aplicación Escritorio Windows (Tauri WebView2)
 * - Aplicación Nativa Android (Capacitor Filesystem + Share)
 */
export async function downloadBinaryFile(blob: Blob, filename: string): Promise<void> {
  if (isCapacitorApp()) {
    const base64 = await blobToBase64(blob);
    const saved = await Filesystem.writeFile({
      path: filename,
      data: base64,
      directory: Directory.Cache,
    });
    await Share.share({
      title: filename,
      url: saved.uri,
      dialogTitle: `Abrir o guardar ${filename}`,
    });
    return;
  }

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}
