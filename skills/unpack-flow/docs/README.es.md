<p align="center"><a href="https://once-email.com"><img src="../assets/unpack-flow-banner.png" alt="UnpackFlow by Once Email" width="100%"></a></p>

# UnpackFlow — descompresión anidada sin vigilancia

[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [हिन्दी](README.hi.md) · [العربية](README.ar.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [日本語](README.ja.md) · [Русский](README.ru.md)

Con `-r`, si el nombre de salida ya existe, UnpackFlow incorpora la carpeta de origen (`sample-backup-legacy-set-unpacked`) y añade `-2`, `-3`, etc. para evitar sobrescrituras y omisiones.

La suite mínima `unpack-flow-minimal-testcases-v1.zip` cubre ZIP, TAR.GZ, Unicode, archivos anidados, `part01.exe` multipartes y un fallo esperado por volumen ausente, sin incluir aplicaciones grandes ni ejecutar el SFX.

La aceptación nativa usa datos sintéticos en `/data/unpack-flow-testcases`; la ruta puede cambiarse mediante `UNPACK_FLOW_TEST_ROOT`. Las suites grandes son opcionales y se reservan para rendimiento o compatibilidad adicional.

UnpackFlow procesa distribuciones de software, conjuntos de datos, copias de seguridad, recursos multimedia y otras colecciones grandes. Detecta el primer volumen, extrae las capas en orden y muestra paquete, fase, nivel y tiempo.

## Uso e instalación

Use `unpack-flow list 'Archive*'`, `plan`, `unpack-flow 'Archive*'` y `status`. Linux usa Bash; Windows, PowerShell 5.1+ y 7-Zip; macOS, PowerShell 7+ y `7zz`. `scripts/build-release.sh` crea los tres paquetes y SHA-256.

Python no es necesario para ejecutar `unpack-flow` ni extraer archivos. Python 3 solo se necesita para instalar automáticamente el Skill en Linux/macOS con `install_local.py` o `install_local.sh` y para la auditoría Python. Windows usa `install_local.ps1` con PowerShell, y la copia manual del Skill tampoco necesita Python.

## Flujos de extracción compatibles

UnpackFlow extrae lotes de carpetas o patrones, abre archivos anidados por capas e identifica el primer volumen de conjuntos RAR multipartes. También inspecciona paquetes autoextraíbles RAR sin ejecutar EXE desconocidos. Es útil para distribuciones de software, datos, copias de seguridad, medios, registros e imágenes ISO o WIM.

De forma predeterminada recorre hasta 10 capas internas. Si un archivo interno está dañado o incompleto, lo conserva, registra el fallo y continúa con los demás; use `-StopOnError` para detenerse en el primer error.

## Ejemplos de aprendizaje

Use `list`, `plan`, `start`, `status`, `log` y `wait` para copias de seguridad, datos, registros, software o archivos multipartes. Los juegos son solo un ejemplo de archivo, no el límite del producto.

En los tres sistemas, `run` se ejecuta en primer plano con progreso y `start` inicia una tarea en segundo plano y devuelve su ID.

Durante operaciones largas de 7-Zip o UnRAR, el tiempo se actualiza cada segundo y se registra una señal de actividad cada 30 segundos.

En macOS y Windows, `start` desconecta todos los flujos interactivos; el progreso va solo al registro y no produce secuencias ANSI ni pitidos.

Use `-r` o `-Recursive` para descubrir todos los archivos en subcarpetas y extraer sus capas internas; una colisión de nombre se guarda como `nombre-unpacked`.

También se admite `unpack-flow run *`: aunque el shell expanda `*`, el escaneo conserva solo archivos únicos y primeros volúmenes como `part1.exe`, `part1.rar`, `.7z.001` o `.zip.001`, y descarta `.sha256`, archivos ajenos y volúmenes posteriores.

`unpack-flow help` muestra la referencia combinada en inglés y chino simplificado.

## Tareas en segundo plano y registros

`unpack-flow start "archivo" -Output "destino"` inicia la extracción en segundo plano y devuelve un identificador. Use `unpack-flow status [id]`, `unpack-flow log [id]` y `unpack-flow wait [id]`; sin identificador se consulta la tarea más reciente. Los registros se guardan en `%LOCALAPPDATA%\unpack-flow\state` en Windows y `~/.local/state/unpack-flow` en macOS/Linux.

Se admiten TAR, TAR.GZ/TGZ y GZ independiente. Tras 7-Zip, el programa prueba según el formato UnRAR, `tar`, GZip o ZIP nativo; limpia cada intento fallido y continúa con el siguiente archivo cuando se agotan las opciones, sin bucles infinitos.

Linux x64 incluye UnRAR 7.23 oficial. Windows x64/ARM64 incluye 7-Zip 26.02 completo y oficial; x64 también incluye UnRAR. Se conservan los paquetes y licencias originales.

## Inicio rápido completo

```bash
unpack-flow list '/data/archives/*'
unpack-flow plan '/data/archives/backup.part1.rar'
unpack-flow run '/data/archives/*' -Output '/data/extracted'
```

Para ejecutar en segundo plano:

```bash
unpack-flow start '/data/archives/*' -Output '/data/extracted'
unpack-flow status
unpack-flow log
unpack-flow wait
```

`run` permanece en primer plano; `start` devuelve inmediatamente un ID de tarea. En ambos casos se conservan los archivos originales.

## Instalar la herramienta de línea de comandos

### Linux

```bash
./install-linux.sh --check
./install-linux.sh
unpack-flow version
```

### macOS

```bash
./install-macos.sh --check
./install-macos.sh
unpack-flow version
```

### Windows

```bat
install.bat -Check
install.bat
unpack-flow version
```

Las comprobaciones informan de dependencias ausentes, pero no instalan software del sistema automáticamente.

## Recursión, registros y errores

Use `-r` o `-Recursive` para buscar archivos en subcarpetas y abrir capas internas. El límite predeterminado es de 10 capas.

| Plataforma | Directorio de estado predeterminado |
|---|---|
| Windows | `%LOCALAPPDATA%\unpack-flow\state` |
| Linux/macOS | `${XDG_STATE_HOME:-$HOME/.local/state}/unpack-flow` |

UnpackFlow prueba una cadena limitada: 7-Zip, UnRAR para RAR y las herramientas nativas apropiadas para TAR, GZ o ZIP. Limpia cada intento incompleto; si todos fallan, conserva el archivo, registra el error y continúa. Use `-StopOnError` solo cuando deba detenerse en el primer error.

## Pruebas e instalación como Agent Skill

```bash
bash tests/generate-minimal-public-suite.sh
bash tests/test-minimal-public-suite.sh
pwsh -NoProfile -File tests/test-minimal-public-suite.ps1
scripts/install_local.sh .
```

En Windows, instale el Skill con `scripts/install_local.ps1`. Python no es necesario para extraer archivos; solo se usa en el instalador automatizado del Skill para Linux/macOS y en la auditoría Python.

## Seguridad, proyecto y soporte

UnpackFlow conserva las fuentes, no sobrescribe destinos ni ejecuta archivos EXE desconocidos.

- Sitio web oficial: [once-email.com](https://once-email.com)
- Creadora y desarrolladora: helen.jar
- Proyecto GitHub: [pangxin12345/unpack-flow](https://github.com/pangxin12345/unpack-flow)
- Correo de soporte: [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)

Para cualquier pregunta, escriba a [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com) o [abra una incidencia en GitHub](https://github.com/pangxin12345/unpack-flow/issues).

Licencia MIT, versión 2.1.4.
