Infrastructure Evidence Kit — paquete de capturas

Versión: v0.1.0
Commit de código: bf2287757bd86cf590c89d91f39a5b52abcded43
Fecha: 2026-10-29, America/Tegucigalpa (UTC-06:00).

Cinco capturas JPEG reales del navegador, tomadas de reportes HTML estáticos
que representan stdout/JSON/CSV de una ejecución local nueva. Cada imagen
incluye el aviso: Reporte local de resultados; no es una UI del producto.
No se usó ImageGen. No se simulan interfaces de equipos.

Selección para portafolio: images/01-gaps.jpg e images/03-tampered.jpg.
Las leyendas completas están en captions.txt; las fuentes de cada imagen,
dimensiones y SHA-256 están en manifest.json. Todos los archivos del paquete,
excepto SHA256SUMS, tienen una entrada en SHA256SUMS.

Comprobaciones finales: 133 tests, lint y formato correctos, 8/8 escenarios.
Los intentos anteriores y temporales no forman parte de publish.
Los cambios de documentación hechos en paralelo por otro chat se registran en
logs/run-metadata.json; src, tests, scripts y ejemplos corresponden al commit
de código indicado. No se modificó el repo desde este chat.

Fuentes: sources/inputs contiene los ejemplos originales; sources/scenarios
contiene los bundles y stdout/stderr del script real. El bundle tampered está
alterado deliberadamente y debe producir verify exit 1: no es un paquete sano.
El caso invalid-path debe dar build exit 2 y no crear un bundle. El campo
verified de summary.json significa que se comprobó la expectativa del escenario.
Los detalles de esas expectativas están en sources/check_examples.py.

commands.json registra los comandos ejecutados, códigos de salida, tiempos y
variables que mantienen los temporales/cachés fuera del repo. REPO y CAPTURE_ROOT
sustituyen rutas locales personales solo en el registro de comandos. Las salidas,
inputs y bytes de evidencia se conservaron sin cambios. La comparación entre
código instalado y código fuente está en logs/installed-code-check.json.

Los tres archivos históricos proceden de Network Lab Factory v0.1.1, commit
137a2cb89460b080253fdce07f7e6ba397962347. Sus URLs y hashes están en
sources/inputs/historical-lab/provenance.json. Se verificó igualdad de bytes
entre la copia incluida en los ejemplos y el bundle nuevo; no se volvió a
consultar la red ni se hizo una nueva ejecución de laboratorio.

El kit solo organiza archivos y comprueba integridad interna. No mide salud o
compliance, no autentica el manifiesto, no ejecuta recolección y no redacta
secretos. La cobertura 3/3 incluye un reporte histórico con checks fallidos.

Privacidad: se revisaron las cinco imágenes y todos los archivos de texto
publicables con búsqueda de rutas personales, IP RFC1918, credenciales y claves.
Solo aparecen direcciones sintéticas reservadas para documentación o benchmarking.
No se detectaron rutas personales, IP privadas RFC1918 ni credenciales.
Los reportes históricos se conservan íntegros: no se aplicó redacción al contenido.

Para revisar las fuentes visuales, abrir reports/*.html en un navegador local.
Para comprobar el paquete, ejecutar desde esta carpeta: shasum -a 256 -c SHA256SUMS
