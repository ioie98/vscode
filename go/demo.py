import os
import subprocess
import time
import platform

def run_cmd(cmd):
    try:
        start = time.time()
        output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
        duration = time.time() - start
        return output.strip(), duration
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output}", -1

print("=== Go 环境排查脚本 ===")

# 1. 系统信息
print(f"系统: {platform.system()} {platform.release()} ({platform.architecture()[0]})")
print(f"Python 版本: {platform.python_version()}")
print()

# 2. Go 版本
out, t = run_cmd("go version")
print(f"[Go 版本] {out} (耗时 {t:.2f}s)")

# 3. Go 环境变量
out, _ = run_cmd("go env")
print("\n[Go 环境变量部分]")
for line in out.splitlines():
    if any(k in line for k in ["GOCACHE", "GOPATH", "GOMODCACHE", "GOPROXY"]):
        print("  ", line)

# 4. 缓存目录检查
cache_dir = None
for line in out.splitlines():
    if line.startswith("GOCACHE="):
        cache_dir = line.split("=", 1)[1].strip('"')
if cache_dir:
    print(f"\n[GOCACHE] {cache_dir}")
    print("  是否存在:", os.path.exists(cache_dir))
    if os.path.exists(cache_dir):
        print("  文件数:", sum(len(files) for _, _, files in os.walk(cache_dir)))

# 5. go run 耗时测试
test_file = "test_demo.go"
with open(test_file, "w", encoding="utf-8") as f:
    f.write('package main\nimport "fmt"\nfunc main(){fmt.Println("Hello Go!")}\n')

print("\n[go run 耗时测试]")
out, t = run_cmd(f"go run {test_file}")
print(f"输出: {out} (耗时 {t:.2f}s)")

# 6. go build + 运行耗时
print("\n[go build + 运行 耗时测试]")
out, t1 = run_cmd(f"go build -o test_demo.exe {test_file}")
if "Error" not in out:
    print(f"go build 耗时 {t1:.2f}s")
    out, t2 = run_cmd("test_demo.exe")
    print(f"运行耗时 {t2:.2f}s, 输出: {out}")
else:
    print(out)

# 清理
try:
    os.remove(test_file)
    os.remove("test_demo.exe")
except:
    pass

print("\n=== 检查完成 ===")
