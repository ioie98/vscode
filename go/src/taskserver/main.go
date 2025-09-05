package main

import (
	"log"
	"net/http"
	"taskserver/handlers"
	"taskserver/worker"
)

func main() {
	// 启动 3 个 worker
	for i := 1; i <= 3; i++ {
		worker.StartWorker(i)
	}

	http.HandleFunc("/submit", handlers.SubmitTaskHandler)
	http.HandleFunc("/result", handlers.ResultHandler)

	log.Println("服务器启动，监听 http://localhost:8080 ...")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal("服务器启动失败:", err)
	}
}
