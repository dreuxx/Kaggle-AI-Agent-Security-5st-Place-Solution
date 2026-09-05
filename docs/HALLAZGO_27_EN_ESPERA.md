# Hallazgo 27 — EN ESPERA

Estado: **EN ESPERA / NO ACTIVO EN `attack.py`**.

El experimento verifico localmente que una razon de denegacion se almacena en
el historial del runtime y puede influir en un segundo mensaje del mismo
`AttackCandidate`. No se considera terminado ni promovido para Kaggle porque el
segundo mensaje aumenta la latencia y el private oculto puede utilizar razones o
politicas diferentes al surrogate local.

## Resultado verificado de 200 candidatos

Version experimental de `attack.py`:
`7e8d9249ea7239957eeee22d1d7e7f79f70a62288339dddf14f7e1888c3defe2`.

- GPT/Optimal: score 18.0, 200/200, 310.549 s.
- GPT/Strict: score 5.76, fallback exitoso en 192/200, 962.988 s.
- Gemma/Optimal: score 18.0, 200/200, 558.567 s.
- Gemma/Strict: score 6.0, fallback exitoso en 200/200, 814.599 s.

## Motivo de la espera

- El runtime termina el `env.interact()` inmediatamente después de `DENY`; por
  eso la razon solo puede consumirse mediante un segundo mensaje.
- Ese segundo mensaje se ejecuta tambien cuando el POST publico tuvo exito.
- La extrapolacion GPT/Strict a 2,000 supera el margen conservador de replay.
- El comportamiento del private real no esta verificado.

## Estado activo actual

El hallazgo 27 continúa desactivado. `attack.py` contiene actualmente un
experimento independiente de un solo mensaje con la secuencia
`http.post -> email.send`, configurado con 2,000 candidatos para subida. Su
SHA-256 activo es
`ae03c4ec9c330e429c9692202dc2ebf746dc9694e751c25d81c677e0141f52e5`.

No reactivar el hallazgo 27 durante otros experimentos salvo petición
explícita. Sus artefactos y detalles permanecen en `RESULTADOS_EXPERIMENTOS.md`.
