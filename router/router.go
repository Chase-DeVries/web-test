package requestHandler

import (
	"html/template" // injection safe html generation
	requestHandler "htmx-demo/requests"
	"log"
	"net/http"
)

func index(w http.ResponseWriter, r *http.Request) {
	var tpl = template.Must(template.ParseFiles("views/index.html"))
	tpl.Execute(w, nil)
}

func photos(w http.ResponseWriter, r *http.Request) {
	var tpl = template.Must(template.ParseFiles("views/photos.html"))
	tpl.Execute(w, nil)
}

func navBar(w http.ResponseWriter, r *http.Request) {
	n := requestHandler.GetNavbarForRequest(r)
	var tpl = template.Must(template.ParseFiles("components/navbar.html"))
	tpl.Execute(w, n)
}

func faviconHandler(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, "assets/favicon-32x32.png")
}

/**
 * as it turns out, only capitalized identifiers are exported from a module.
**/
func HandleRequests(router *http.ServeMux, port string) {
	router.HandleFunc("/favicon.ico", faviconHandler)
	router.HandleFunc("/{$}", index) // exact "/" only, so unknown paths 404 instead of silently serving home
	router.HandleFunc("/photos", photos)
	router.HandleFunc("/navbar", navBar)

	router.Handle("/assets/", http.StripPrefix("/assets/", http.FileServer(http.Dir("assets"))))
	router.Handle("/styles/", http.StripPrefix("/styles/", http.FileServer(http.Dir("styles"))))

	log.Println("Server is running on http://localhost:" + port)
	log.Fatal(http.ListenAndServe(":"+port, recoverPanics(logRequests(router))))
}
