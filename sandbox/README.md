# Entorno aislado local

Este directorio ejecuta los experimentos locales con `bubblewrap` sin cambiar
`attack.py`, el SDK ni los GGUF.

## Garantias verificables

- El proyecto completo se monta en solo lectura.
- Solo `sandbox/output/` es persistente y escribible.
- `/tmp` y `HOME` son efimeros dentro de cada ejecucion.
- No se heredan credenciales ni variables del shell anfitrion.
- Hugging Face, Transformers y Datasets se fuerzan a modo offline.
- Python rechaza conexiones IPv4/IPv6 mediante `offline/sitecustomize.py`.
- Los modelos y dependencias existentes se leen directamente, sin copiarlos ni
  descargarlos.

El kernel de esta maquina no permite crear un namespace de red anidado con
`bubblewrap` (`Operation not permitted`). Por eso la red tiene dos capas: la
restriccion de red del sandbox anfitrion y el bloqueo explicito de sockets
Python. Un binario nativo ajeno a Python depende de la primera capa; no se afirma
un aislamiento de red kernel-level dentro de `bubblewrap`.

## Verificar el sandbox

```bash
bash sandbox/run.sh .venv/bin/python sandbox/self_test.py
```

El comando debe terminar con `"ok": true` y escribe el reporte en
`sandbox/output/self_test_report.json`.

## Ejecutar un experimento

Prueba minima de Gemma:

```bash
bash sandbox/run_experiment.sh gemma gemma_smoke.json \
  --samples 1 --variants baseline_k1
```

Prueba minima de GPT-OSS:

```bash
bash sandbox/run_experiment.sh gpt_oss gpt_oss_smoke.json \
  --samples 1 --variants frame_current_k1
```

Los JSON siempre quedan bajo `sandbox/output/`. El wrapper rechaza una ruta de
salida que intente escapar de ese directorio.

Por defecto `/dev` es minimo y no expone una GPU. En una maquina T4 donde el
entorno anfitrion ya autorice el dispositivo, se puede habilitarlo expresamente:

```bash
SANDBOX_ALLOW_GPU=1 bash sandbox/run_experiment.sh gemma gemma_t4.json \
  --samples 1 --variants baseline_k1
```

Este entorno reduce efectos laterales del runtime. No elimina las politicas de
OpenAI ni modifica los limites del benchmark.
