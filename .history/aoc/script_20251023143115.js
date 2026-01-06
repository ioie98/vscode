// ---------- 全局变量 ----------
let datasets = [];
let currentPage = 1;
const pageSize = 5;

// ---------- 初始化 ----------
document.addEventListener('DOMContentLoaded', () => {
    loadSiteDatasets();
});

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
                <button class="btn" onclick="viewDataset('${ds.filename}','${ds.siteId}')">详情</button>
                <button class="btn red" onclick="deleteDataset('${ds.filename}','${ds.siteId}')">删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById('datasetCount').innerText = `共 ${datasets.length} 条`;
    renderPagination();
}

// ---------- 渲染分页 ----------
function renderPagination() {
    const totalPages = Math.ceil(datasets.length / pageSize);
    const pagination = document.getElementById('datasetPagination');
    pagination.innerHTML = '';
    if (totalPages <= 1) return;

    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.innerText = i;
        if (i === currentPage) btn.classList.add('active');
        btn.addEventListener('click', () => {
            currentPage = i;
            renderDatasetTable();
        });
        pagination.appendChild(btn);
    }
}

// ---------- 删除数据集 ----------
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

function closeModal() {
    document.getElementById('modalBg').style.display = 'none';
}

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

// ---------- 统一下载弹框 ----------
function openDownloadModalUnified() {
    const defaultOrder = ['deviced','ec','era5','cros'];
    const modalContent = `
        <h3>下载数据</h3>
        <label>开始时间:</label>
        <input type="text" id="downloadStartTime" placeholder="开始时间"><br><br>
        <label>结束时间:</label>
        <input type="text" id="downloadEndTime" placeholder="结束时间"><br><br>
        <label>排序方式:</label>
        <select id="downloadSortMode" onchange="toggleManualOrder(this.value)">
            <option value="default">默认排序</option>
            <option value="manual">手动排序</option>
        </select><br><br>
        <div id="manualOrderDiv" style="display:none;">
            <label>手动顺序:</label><br>
            <input type="text" id="manualOrderInput" value="${defaultOrder.join(',')}" placeholder="用逗号分隔 deviced,ec,era5,cros"><br><br>
        </div>
        <h4>优先级选择</h4>
        <label>PWV:</label>
        <select id="priorityPWV">
            <option value="deviced">deviced</option>
            <option value="ec">ec</option>
            <option value="era5">era5</option>
            <option value="cros">cros</option>
        </select><br><br>
        <label>HWS:</label>
        <select id="priorityHWS">
            <option value="deviced">deviced</option>
            <option value="ec">ec</option>
            <option value="era5">era5</option>
            <option value="cros">cros</option>
        </select><br><br>
        <label>RAIN:</label>
        <select id="priorityRAIN">
            <option value="deviced">deviced</option>
            <option value="ec">ec</option>
            <option value="era5">era5</option>
            <option value="cros">cros</option>
        </select><br><br>
        <button class="btn" onclick="downloadUnifiedData()">下载</button>
    `;
    openModal(modalContent);

    flatpickr("#downloadStartTime", { enableTime: true, dateFormat: "Y/m/d H:i" });
    flatpickr("#downloadEndTime", { enableTime: true, dateFormat: "Y/m/d H:i" });
}

function toggleManualOrder(value) {
    document.getElementById('manualOrderDiv').style.display = value === 'manual' ? 'block' : 'none';
}

// ---------- 下载逻辑 ----------
function downloadUnifiedData() {
    const startTime = document.getElementById('downloadStartTime').value;
    const endTime = document.getElementById('downloadEndTime').value;
    const sortMode = document.getElementById('downloadSortMode').value;
    const manualOrder = document.getElementById('manualOrderInput')?.value.split(',') || [];
    const priority = {
        pwv: document.getElementById('priorityPWV').value,
        hws: document.getElementById('priorityHWS').value,
        rain: document.getElementById('priorityRAIN').value
    };
    const site = document.getElementById('stationSelect').value.trim();
    if (!site) { showToast('请选择站点', 'error'); return; }
    if (!startTime || !endTime) { showToast('请选择时间范围', 'error'); return; }

    const payload = {
        site, startTime, endTime, sortMode, manualOrder, priority
    };

    fetch('/download_merge_data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).then(res => res.json())
      .then(res => {
          if(res.status === 'success') {
              showToast('下载合并完成');
              closeModal();
              loadSiteDatasets();
          } else {
              showToast('下载失败: ' + (res.message || ''), 'error');
          }
      }).catch(err => showToast('下载异常: ' + err, 'error'));
}
