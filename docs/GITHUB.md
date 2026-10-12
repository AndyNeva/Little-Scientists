# GitHub — cómo subir este proyecto

El proyecto ya está preparado como repositorio Git, con **todo confirmado en un
primer commit**. Solo falta publicarlo en GitHub. Son tres pasos y una decisión.

> **Nada de esto incluye credenciales.** `.env` está en `.gitignore` y queda fuera
> del repositorio. Antes del primer `push` se comprobó que ni la clave de Gemini ni
> el token de Cloudflare aparecen en ningún archivo confirmado.

---

## 1. Crear el repositorio vacío en GitHub

1. Entrar en <https://github.com/new>.
2. **Repository name:** `aventura-ia` (o el que prefieras).
3. **Visibility:** elegir una de estas dos opciones.

   | Opción | Cuándo usarla |
   |---|---|
   | **Private** (recomendado) | Solo tú y las personas que invites pueden verlo. El encargado de la feria necesitará una invitación o un token para descargarlo. |
   | **Public** | Cualquiera puede verlo y descargarlo. **Nunca subas el `.env`**, y ten en cuenta que el código quedará visible para todo el mundo. |

4. **No** marques «Add a README», «Add .gitignore» ni «Choose a license»: el
   repositorio debe quedar vacío, porque el contenido ya está aquí.
5. Pulsar **Create repository**.

---

## 2. Enlazar y subir

GitHub mostrará la URL del repositorio. Sustituye `<USUARIO>` por tu usuario:

```bash
git remote add origin https://github.com/<USUARIO>/aventura-ia.git
git push -u origin main
```

La primera vez pedirá autenticación. **GitHub no acepta la contraseña de la
cuenta**; hay que usar una de estas dos formas:

- **Token de acceso personal:** se crea en
  <https://github.com/settings/tokens> (permiso `repo`) y se usa como contraseña
  cuando Git la pida.
- **GitHub CLI:** si instalas `gh`, basta con `gh auth login` una vez.

---

## 3. Dar acceso al encargado de la feria

Si el repositorio es **privado**:

- **Invitarlo como colaborador:** *Settings → Collaborators → Add people*. Podrá
  clonar con su propia cuenta.
- **O darle un token de solo lectura:** *Settings → Developer settings → Personal
  access tokens → Fine-grained tokens*, limitado a ese repositorio y con permiso
  solo de lectura de contenido.

Para que **descargue y ejecute** la aplicación, lo que necesita es:

```bash
git clone https://github.com/<USUARIO>/aventura-ia.git
cd aventura-ia
cp .env.example .env
nano .env                 # poner las credenciales del proveedor
docker compose up -d --build
```

La guía completa, con la configuración, la comprobación de salud, el requisito de
HTTPS para la cámara y los problemas frecuentes, está en
[`docs/DEPLOY.md`](DEPLOY.md). **Ese es el documento que hay que enviarle.**

---

## 4. A partir de aquí: cambios

```bash
git status                 # ver qué cambió
git add -A
git commit -m "Descripcion corta del cambio"
git push
```

Reglas que conviene no romper:

- **Nunca** `git add .env` ni forzarlo con `-f`. Si alguna vez se subiera una clave
  por error, hay que **revocarla y generar otra** en el proveedor: borrarla del
  repositorio no basta, porque queda en el historial.
- Antes de confirmar, comprobar que las pruebas pasan:

  ```bash
  python -m pytest
  ```

- Los mensajes de commit, descriptivos y en una línea si es posible.

---

## 5. Si algo va mal

| Síntoma | Causa y solución |
|---|---|
| `remote origin already exists` | Ya hay un remoto: `git remote set-url origin <URL>` |
| `Authentication failed` | GitHub no acepta la contraseña. Usar un token personal o `gh auth login`. |
| `src refspec main does not match any` | La rama no se llama `main`: comprobar con `git branch`. |
| `rejected — fetch first` | El repositorio remoto tiene commits que no tienes (por ejemplo, si marcaste «Add a README»). Resolver con `git pull --rebase origin main` antes de subir. |
| Quiero comprobar qué se va a subir | `git diff --cached --stat` antes de confirmar. |
