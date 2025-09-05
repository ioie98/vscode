package store

import "sync"

type Job struct {
    ID     int
    Input  int
    Result string
    Error  string
}

var (
    jobs   = make(map[int]*Job)
    jobMux sync.Mutex
    nextID = 1
)

// 添加任务
func AddJob(input int) int {
    jobMux.Lock()
    defer jobMux.Unlock()
    id := nextID
    nextID++
    jobs[id] = &Job{
        ID:    id,
        Input: input,
    }
    return id
}

// 获取下一个任务
func GetJob() *Job {
    jobMux.Lock()
    defer jobMux.Unlock()
    for _, job := range jobs {
        if job.Result == "" && job.Error == "" {
            return job
        }
    }
    return nil
}

// ✅ 标记任务完成
func MarkJobDone(id int) {
    jobMux.Lock()
    defer jobMux.Unlock()
    // 任务已经在 worker 中被更新 Result 或 Error
    // 这里可以加日志或其他处理
}
