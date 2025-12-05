# Cómo subir cambios a GitHub

1. Guarda todos tus archivos y asegúrate de estar en la carpeta raíz del proyecto.
2. Abre la terminal y ejecuta:

```sh
git add .
```
Esto agrega todos los archivos nuevos y modificados al área de preparación (staging).

3. Haz un commit con un mensaje descriptivo:

```sh
git commit -m "Tu mensaje de commit aquí"
```

4. Sube los cambios al repositorio remoto (por ejemplo, a la rama main):

```sh
git push origin main
```

Si es la primera vez que subes una rama nueva, usa:

```sh
git push -u origin nombre-de-la-rama
```

---

## Resumen rápido
- `git add .` — agrega todos los cambios
- `git commit -m "mensaje"` — guarda un snapshot
- `git push origin main` — sube a GitHub

