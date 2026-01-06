let datasets = [];
let currentPage = 1;
const pageSize = 5;

// ---------- 加载站点数据集 ----------
function loadSiteDatasets() {
    const site = document.getElementById('stationSelect').value.trim();
    if (!site) {
        document.getElementById('datasetTableBody').innerHTML = '';
        document.getElementById('datasetCount').innerText = '';
        document.getElementById('datasetPagination').innerHTML = '';
        return;
    }

    fetch(`/get_datasets/${site}`)
        .then(res => res.json())
        .then(res => {
            datasets = res.data || [];
            currentPage = 1;
            renderDatasetTable();
        })
        .catch(err => showToast('加载数据集失败: ' + err, 'error'));
}

// ---------- 渲染表格 ----------
function renderDatasetTable() {
    const tbody = document.getElementById('datasetTableBody');
    tbody.innerHTML = '';

    if (!datasets.length) {
        document.getElementById('datasetCount').innerText = '共 0 条';
        document.getElementById('datasetPagination').innerHTML = '';
        return;
    }

    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    const pageDatasets = datasets.slice(start, end);

    pageDatasets.forEach(ds => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${ds.filename}</td>
            <td>${ds.siteId}</td>
            <td>${ds.siteName || ''}</td>
            <td>${ds.timeRange || '未知'}</td>
            <td>${ds.createTime || ''}</td>
            <td>
                <button class="btn" onclick="viewDataset('${ds.filename}', '${ds.siteId}')">详情</button>
                <button class="btn red" onclick="deleteDataset('${ds.filename}', '${ds.siteId}')">删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById('datasetCount').innerText = `共 ${datasets.length} 条`;
    renderPagination();
}

// ---------- 分页 ----------
function renderPagination() {
    const totalPages = Math.ceil(datasets.length / pageSize);
    const pagination = document.getElementById('datasetPagination');
    pagination.innerHTML = '';
    if (totalPages <= 1) return;

    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.innerText = i;
        if (i === currentPage) btn.classList.add('active');
        btn.addEventListener('click', () => { currentPage = i; renderDatasetTable(); });
        pagination.appendChild(btn);
    }
}

// ---------- 删除 ----------
function deleteDataset(filename, site) {
    if (!confirm(`确认删除 ${filename} 吗？`)) return;

    fetch(`/delete_dataset/${filename}/${site}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(res => {
            if (res.status === 'success') {
                showToast('删除成功');
                datasets = datasets.filter(d => d.filename !== filename);
                renderDatasetTable();
            } else {
                showToast('删除失败: ' + (res.message || ''), 'error');
            }
        })
        .catch(err => showToast('删除异常: ' + err, 'error'));
}

// ---------- 查看详情 ----------
function viewDataset(filename, site) {
    fetch(`/tmp_data/${site}/${filename}`)
        .then(res => res.text())
        .then(text => openModal(`<pre style="white-space: pre-wrap;">${text}</pre>`))
        .catch(err => showToast('加载详情失败: ' + err, 'error'));
}

// ---------- 弹窗 ----------
function openModal(content) {
    document.getElementById('modalBody').innerHTML = content;
    document.getElementById('modalBg').style.display = 'flex';
}
function closeModal() { document.getElementById('modalBg').style.display = 'none'; }

// ---------- Toast ----------
function showToast(msg, type='success') {
    const div = document.createElement('div');
    div.className = 'toast-message';
    div.style.background = type === 'error' ? '#dc3545' : '#4caf50';
    div.innerText = msg;
    document.body.appendChild(div);
    setTimeout(() => div.style.opacity = 1, 10);
    setTimeout(() => {
        div.style.opacity = 0;
        setTimeout(() => document.body.removeChild(div), 500);
    }, 2000);
}

// ---------- 下载弹框 ----------
function openDownloadModal() {
    const modalContent = `
    <div class="modal-body-section">
        <label>时间范围：</label>
        <input id="downloadStart" placeholder="开始时间" class="flatpickr" type="text">
        <input id="downloadEnd" placeholder="结束时间" class="flatpickr" type="text">
    </div>
    <div class="modal-body-section">
        <label>排序方式：</label>
        <select id="downloadMode">
            <option value="default">默认排序 (deviced>ec>era5>cros)</option>
            <option value="manual">手动排序</option>
        </select>
    </div>
    <div class="modal-body-section" id="manualSortSection" style="display:none;">
        <label>PWV 优先级：</label>
        <select id="pwvPriority" multiple>
            <option>deviced</option>
            <option>ec</option>
            <option>era5</option>
            <option>cros</option>
        </select>
        <label>HWS 优先级：</label>
        <select id="hwsPriority" multiple>
            <option>deviced</option>
            <option>ec</option>
            <option>era5</option>
            <option>cros</option>
        </select>
        <label>RAIN 优先级：</label>
        <select id="rainPriority" multiple>
            <option>deviced</option>
            <option>ec</option>
            <option>era5</option>
            <option>cros</option>
        </select>
    </div>
    <div style="text-align:right; margin-top:10px;">
        <button class="btn" onclick="startDownload()">下载并合并</button>
    </div>
    `;
    openModal(modalContent);

    flatpickr("#downloadStart", { enableTime: true, dateFormat: "Y/m/d H:i" });
    flatpickr("#downloadEnd", { enableTime: true, dateFormat: "Y/m/d H:i" });

    document.getElementById('downloadMode').addEventListener('change', function() {
        document.getElementById('manualSortSection').style.display = this.value === 'manual' ? 'block' : 'none';
    });
}

// ---------- 执行下载 ----------
function startDownload() {
    const site = document.getElementById('stationSelect').value.trim();
    if (!site) { showToast('请选择站点', 'error'); return; }

    const start = document.getElementById('downloadStart').value;
    const end = document.getElementById('downloadEnd').value;
    const mode = document.getElementById('downloadMode').value;

    let pwvPriority = ["deviced","ec","era5","cros"];
    let hwsPriority = ["deviced","ec","era5","cros"];
    let rainPriority = ["deviced","ec","era5","cros"];

    if (mode === 'manual') {
        pwvPriority = Array.from(document.getElementById('pwvPriority').selectedOptions).map(o=>o.value);
        hwsPriority = Array.from(document.getElementById('hwsPriority').selectedOptions).map(o=>o.value);
        rainPriority = Array.from(document.getElementById('rainPriority').selectedOptions).map(o=>o.value);
    }

    closeModal();
    showToast('下载并合并任务开始');

    // 调用后台接口下载合并（接口保持原逻辑）
    fetch(`/download_merge/${site}`, {
        method:'POST',
        headers:{ 'Content-Type':'application/json' },
        body: JSON.stringify({ start, end, pwvPriority, hwsPriority, rainPriority })
    })
    .then(res=>res.json())
    .then(res=>{
        if(res.status==='success'){
            showToast('下载合并完成');
            loadSiteDatasets();
        } else {
            showToast('下载失败: ' + (res.message||''), 'error');
        }
    })
    .catch(err => showToast('下载异常: '+err, 'error'));
}

// ---------- 初始化 ----------
document.addEventListener('DOMContentLoaded', () => {
    loadSiteDatasets();
});
