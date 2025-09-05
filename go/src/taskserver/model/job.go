package model

type Job struct {
	ID     int    `json:"id"`
	Input  int    `json:"input"`
	Result string `json:"result,omitempty"`
	Error  string `json:"error,omitempty"`
}
