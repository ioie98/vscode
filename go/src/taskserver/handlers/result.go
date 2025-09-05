package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"
	"taskserver/store"
)

// 查询任务结果
func ResultHandler(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("id")
	if query == "" {
		http.Error(w, "缺少任务 ID", http.StatusBadRequest)
		return
	}

	jobID, err := strconv.Atoi(query)
	if err != nil {
		http.Error(w, "无效的任务 ID", http.StatusBadRequest)
		return
	}

	job, ok := store.Results[jobID]
	if !ok {
		http.Error(w, "任务尚未完成或不存在", http.StatusNotFound)
		return
	}

	_ = json.NewEncoder(w).Encode(job)
}
