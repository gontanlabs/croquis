# Especificación: <tarea>

Una página. Se escribe antes de programar y Jose la aprueba (su frase va a `docs/DECISIONES.md`). Se construye en una sesión nueva a partir de este fichero.

- **Fecha y commit de inicio:** AAAA-MM-DD · `<hash>` (la revisión compara desde aquí: `git diff <hash>..HEAD`).
- **Problema:** qué pasa hoy y a quién le duele, con un ejemplo real.
- **Apetito:** tiempo máximo (no estimación). Si se pasa, se para y se vuelve a dar forma.
- **Solución, a grandes rasgos:** lo justo para que se entienda.
- **Límites y lo que queda fuera.**
- **Riesgos:** lo que puede salir mal y cómo se sabrá pronto.

## Terminado cuando

- [ ] `python scripts/comprobar.py` en verde y la CI en verde.
- [ ] Criterio comprobable 1 (con número o con prueba real).
- [ ] Criterio comprobable 2.
- [ ] Revisión sin hallazgos de corrección abiertos.
- [ ] Jose lo ha probado y dado por bueno.
