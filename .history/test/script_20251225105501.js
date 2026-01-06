document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', function() {
        // 1. 切换 active 样式
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        this.classList.add('active');

        // 2. 更改 iframe 地址
        const url = this.getAttribute('data-url');
        if (url !== "#") {
            document.getElementById('contentFrame').src = url;
        }
    });
});

// 顶栏添加站点标签的逻辑
function addTag() {
    const val = document.getElementById('siteInput').value;
    if(!val) return;
    const container = document.getElementById('tagContainer');
    const span = document.createElement('div');
    span.className = 'tag';
    span.innerHTML = val + ' <small style="cursor:pointer" onclick="this.parentElement.remove()">×</small>';
    container.appendChild(span);
    document.getElementById('siteInput').value = '';
}