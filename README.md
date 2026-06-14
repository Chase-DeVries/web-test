# htmx-demo

A small personal photo site. A Go server renders HTML pages and HTMX fragments;
the photo gallery loads images straight from a public Google Cloud Storage bucket
in the browser. Deployed to Google Cloud Run.

- **Backend:** Go, standard-library `net/http` ([tutorial](https://freshman.tech/web-development-with-go/))
- **Frontend:** [HTMX](https://htmx.org/examples) + `html/template`
- **Photos:** public GCS bucket `chasedv-photos`, fetched client-side
- **Hosting:** Google Cloud Run

## Running locally

The app listens on the port in `.env` (`PORT=6969`).

```sh
# Go directly
go run .

# or with live reload
air

# or in Docker (Compose builds the image automatically)
docker compose up --build
docker compose down
```

Then open http://localhost:6969.

## Deploying

From the project root:

```sh
gcloud run deploy --source .
# choose region: us-central1
```

## Project layout

```
main.go                     entrypoint: loads .env, starts the ServeMux
router/
  router.go                 routes and page/fragment handlers
  middleware.go             request logging + panic recovery
requests/
  request_handler.go        navbar helper (active-link state)
views/                      full-page templates (index, photos)
components/                 HTMX fragments (navbar)
assets/  styles/            static files served at /assets and /styles
architecture.drawio         architecture diagram (regenerate via build_diagram.py)
```

### Routes

| Path        | Purpose                                   |
|-------------|-------------------------------------------|
| `/`         | Home page                                 |
| `/photos`   | Photo gallery (fetches GCS in the browser)|
| `/navbar`   | Navbar fragment (loaded via HTMX)         |
| `/assets/`  | Static assets                             |
| `/styles/`  | Stylesheets                               |

## Roadmap

- **Photo uploads.** When this lands, reintroduce Supabase (auth + storage) and
  move config (URLs, keys) into `.env`; add `HttpOnly`/`Secure`/`SameSite` flags
  to the session cookie.
- Consider restructuring the Go packages once the app grows
  ([Ben Johnson style](https://medium.com/sellerapp/golang-project-structuring-ben-johnson-way-2a11035f94bc)).
