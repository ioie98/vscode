package worker

import (
    "strconv"
    "taskserver/store"
    "time"
    "math/rand"
)

func StartWorker() {
    go func() {
        for {
            // 从 store 获取任务
            job := store.GetJob()
            if job != nil {
                // 模拟处理耗时
                time.Sleep(time.Second * time.Duration(rand.Intn(3)+1))

                // 随机失败
                if rand.Intn(10) < 2 {
                    job.Error = "随机错误"
                } else {
                    // 正确计算平方并转换为字符串
                    job.Result = "平方结果 = " + strconv.Itoa(job.Input*job.Input)
                }

                // 标记任务完成
                store.MarkJobDone(job.ID)
            } else {
                // 没有任务，休眠等待
                time.Sleep(500 * time.Millisecond)
            }
        }
    }()
}
