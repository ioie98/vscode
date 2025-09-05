// package main
// import "fmt"
// func main() {
//     result := 0
//     for i := 1; i <= 10; i++ {
//         result = fibonacci(i)
//         fmt.Printf("fibonacci(%d) is: %d\n", i, result)
//     }
// }
// func fibonacci(n int) (res int) {
//     if n <= 2 {
//         res = 1
//     } else {
//         res = fibonacci(n-1) + fibonacci(n-2)
//     }
//     return
// }


package main

import "fmt"

func Factorial(n uint64) (result uint64) {
    if n > 0 {
        result = n * Factorial(n-1)
        return result
    }
    return 1
}

func main() {
    var i int = 10
    fmt.Printf("%d 的阶乘是 %d\n", i, Factorial(uint64(i)))
}