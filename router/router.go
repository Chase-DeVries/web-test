package requestHandler

import (
	"html/template" // injection safe html generation
	jokeFactory "htmx-demo/jokes"
	"log"
	"net/http"

	"github.com/gorilla/mux" // router for the site
)

func index(w http.ResponseWriter, r *http.Request) {
	var tpl = template.Must(template.ParseFiles("components/index.html"))
	tpl.Execute(w, nil)
}

func jokes(w http.ResponseWriter, r *http.Request) {
	var tpl = template.Must(template.ParseFiles("components/jokes.html"))
	tpl.Execute(w, nil)
}

func contact(w http.ResponseWriter, r *http.Request) {
	var tpl = template.Must(template.ParseFiles("components/contact.html"))
	tpl.Execute(w, nil)
}

func about(w http.ResponseWriter, r *http.Request) {
	var tpl = template.Must(template.ParseFiles("components/about.html"))
	tpl.Execute(w, nil)
}

func generate(w http.ResponseWriter, r *http.Request) {
	p := jokeFactory.GetRandomJoke()
	tpl, _ := template.ParseFiles("components/joke.html")
	tpl.Execute(w, p)
}

func faviconHandler(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, "assets/favicon-32x32.png")
}

/**
 * as it turns out, only capitalized identifiers are exported from a module.
**/
func HandleRequests(router *mux.Router, port string) {
	router.HandleFunc("/", index)
	router.HandleFunc("/jokes", jokes)
	router.HandleFunc("/contact", contact)
	router.HandleFunc("/about", about)
	router.HandleFunc("/generate", generate)
	router.HandleFunc("/favicon.ico", faviconHandler)
	log.Fatal(http.ListenAndServe(":"+port, router))
}
