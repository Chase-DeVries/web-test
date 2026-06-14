package main

import (
	requestHandler "htmx-demo/router"
	"log"
	"net/http"
	"os"

	"github.com/joho/godotenv" // read from a .env file for this application
)

func main() {
	log.Println("Starting Golang server...")
	err := godotenv.Load()
	if err != nil {
		log.Println("Error loading .env file")
	}
	port := os.Getenv("PORT")
	if port == "" {
		port = "3000"
	}
	router := http.NewServeMux()
	requestHandler.HandleRequests(router, port)
}
