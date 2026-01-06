// 1. 模块切换逻辑
function switchModule(moduleId, el) {
    // 切换导航高亮
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    el.classList.add('active');

    // 切换模块内容显示
    document.querySelectorAll('.module-section').forEach(sec => sec.classList.remove('active'));
    document.getElementById(moduleId).classList.add('active');
}

// 2. 站点标签逻辑
function addStationTag() {
    const input = document.getElementById('stationSelect');
    const container = document.getElementById('stationTags');
    
    if (input.value.trim() === "") return;

    // 创建标签
    const tag = document.createElement('div');
    tag.className = 'tag';
    tag.innerHTML = `${input.value} <span style="cursor:pointer;margin-left:5px" onclick="this.parentElement.remove()">×</span>`;
    
    container.appendChild(tag);
    input.value = "";
}

// 3. 模型训练 Tab 切换
function switchTab(type) {
    console.log("切换到: " + type);
    // 这里可以根据类型（定性/定量）动态改变参数输入框的值
}

// 4. 模态框控制
function openModal(content) {
    const bg = document.getElementById('modalBg');
    const body = document.getElementById('modalBody');
    
    if(content === 'logs') {
        body.innerHTML = `<h4>操作日志</h4><ul style="font-size:13px">
            <li>[2024-11-28 10:20] Admin 启动了 B1 站点的定性训练</li>
            <li>[2024-11-28 09:15] Admin 替换了 B98 站点的现网模型</li>
        </ul>`;
    }
    
    bg.style.display = 'flex';
}

function closeModal() {
    document.getElementById('modalBg').style.display = 'none';
}

// 5. 文件上传模拟
function openUpload(type) {
    const body = document.getElementById('modalBody');
    body.innerHTML = `<h4>上传 ${type.toUpperCase()} 数据</h4>
        <div style="border:2px dashed #ccc; padding:40px; text-align:center; margin:10px 0">
            点击或拖拽文件到此处上传
        </div>`;
    document.getElementById('modalBg').style.display = 'flex';
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化日期选择器等插件（如果需要）
});