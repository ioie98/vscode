package handlers

import (
	"encoding/json"
	"net/http"
	"taskserver/model"
	"taskserver/store"
)

var jobIDCounter = 1

// 提交任务
func SubmitTaskHandler(w http.ResponseWriter, r *http.Request) {
	var payload struct {
		Input int `json:"input"`
	}
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, "无效输入", http.StatusBadRequest)
		return
	}

	job := model.Job{
		ID:    jobIDCounter,
		Input: payload.Input,
	}
	jobIDCounter++

	// 发送到任务队列
	store.JobQueue <- job

	resp := map[string]interface{}{
		"message": "任务已提交",
		"job_id":  job.ID,
	}
	_ = json.NewEncoder(w).Encode(resp)
}
