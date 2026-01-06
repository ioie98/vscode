let datasets = [];
let currentPage = 1;
const pageSize = 5;
let stations = []; // 站点队列
let currentDownloadMode = "train";

// ---------------------- 工具函数 ----------------------

function fmt(dt) {
    if (!dt) return '';
    const d = new Date(dt);
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function showToast(message, type = 'success') {
    let toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.style.background = type === 'error' ? '#f44336' : '#4caf50';
    toast.innerText = message;
    document.body.appendChild(toast);
    
    requestAnimationFrame(() => {
        toast.style.opacity = 1;
    });

    setTimeout(() => {
        toast.style.opacity = 0;
        setTimeout(() => document.body.removeChild(toast), 500);
    }, 2500);
}

async function request(url, options = {}) {
    try {
        const res = await fetch(url, options);
        return await res.json();
    } catch (err) {
        console.error(`Request failed: ${url}`, err);
        throw err;
    }
}

// ---------------------- 站点管理 ----------------------

function addStationFromInput() {
    const inp = document.getElementById('stationSelect');
    const v = (inp.value || '').trim();
    if (!v) return showToast('请输入站点再添加', 'error');
    const parts = v.split(/\s+/);
    const stationId = parts[parts.length - 1];
    if (stations.includes(stationId)) {
        showToast(`${stationId} 已在列表中`);
        inp.value = '';
        return;
    }
    stations.push(stationId);
    renderStationTags();
    inp.value = v;
    loadSiteDatasets();
}

function onStationInputKeydown(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        addStationFromInput();
    }
}

function renderStationTags() {
    const box = document.getElementById('stationTags');
    if (box) box.innerHTML = stations.map(s => `<span class="station-tag">${s} <span class="remove-tag" onclick="removeStation('${s}')">×</span></span>`).join('');
}

function removeStation(s) {
    stations = stations.filter(x => x !== s);
    renderStationTags();
    const input = document.getElementById('stationSelect');
    if (input) input.value = stations.length > 0 ? stations[0] : '';
    loadSiteDatasets();
}

function clearStationList() {
    stations = [];
    renderStationTags();
    const input = document.getElementById('stationSelect');
    if (input) input.value = '';
    showToast('站点列表已清空');
    datasets = [];
    renderDatasetTable(1);
    ['pwv', 'weather', 'rain'].forEach(t => updateStatusUI(t, "未操作", "0%"));
}

// ---------------------- 数据表格与渲染 ----------------------

async function loadSiteDatasets() {
    if (!stations || stations.length === 0) {
        datasets = [];
        renderDatasetTable(1);
        return;
    }
    const site = stations[0];
    try {
        const res = await request(`/get_datasets?site=${encodeURIComponent(site)}`);
        datasets = [];
        ['train', 'pred'].forEach(subDir => {
            (res[subDir] || []).forEach(d => datasets.push({ ...d, sub_dir: subDir }));
        });
        datasets.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        renderDatasetTable(1);
    } catch (err) {
        console.error("加载数据失败:", err);
    }
}

function renderDatasetTable(page) {
    currentPage = page;
    const tbody = document.getElementById('datasetTableBody');
    if (!tbody) return;
    
    if (datasets.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;">${stations.length ? '暂无数据' : '未选择站点'}</td></tr>`;
        renderPagination();
        return;
    }

    const startIdx = (page - 1) * pageSize;
    const pageData = datasets.slice(startIdx, startIdx + pageSize);
    tbody.innerHTML = pageData.map(ds => `
        <tr>
            <td>${ds.file || ''}</td>
            <td>${ds.site || '未知'}</td>
            <td>${ds.site_name || ('站点' + ds.site)}</td>
            <td>${ds.start_time || ''} ~ ${ds.end_time || ''}</td>
            <td>${ds.created_at || ''}</td>
            <td>
                <button class="btn delete-btn" onclick="deleteDataset('${ds.sub_dir}/${ds.site}/${ds.file}','${ds.site}')">删除</button>
                <button class="btn download-btn" onclick="downloadDataset('${ds.site}','${ds.sub_dir}','${ds.file}')">下载</button>
                <button class="btn upload-btn" onclick="uploadDatasetToOSS('${ds.site}','${ds.sub_dir}','${ds.file}')">上传</button>
            </td>
        </tr>
    `).join('');
    renderPagination();
}

function renderPagination() {
    const pagination = document.getElementById('datasetPagination');
    if (!pagination) return;
    
    if (datasets.length === 0) {
        pagination.innerHTML = '';
        return;
    }

    pagination.innerHTML = `<span style="margin-right:10px">共 ${datasets.length} 条</span>`;
    const totalPages = Math.ceil(datasets.length / pageSize);
    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        if (i === currentPage) btn.classList.add('active');
        btn.onclick = () => renderDatasetTable(i);
        pagination.appendChild(btn);
    }
}

// ---------------------- 弹窗控制逻辑 (已修正) ----------------------

// 【修正1】closeModal 只负责关闭，不处理内部状态
function closeModal() {
    const modalBg = document.getElementById('modalBg');
    if (modalBg) modalBg.style.display = 'none';
}

// 更新状态栏 UI
function updateStatusUI(type, text, progressWidth, startTime, endTime) {
    type = (type || '').toLowerCase();
    const statusId = { pwv: "pwvStatus", weather: "weatherStatus", rain: "rainStatus" }[type];
    const rangeId = { pwv: "pwvTimeRange", weather: "weatherTimeRange", rain: "rainTimeRange" }[type];
    const statusEl = document.getElementById(statusId);
    if (statusEl) {
        statusEl.textContent = text;
        const tr = statusEl.closest('tr');
        if (tr) {
            const bar = tr.querySelector(".progress");
            if (bar) {
                bar.style.width = progressWidth;
                bar.style.backgroundColor = (text.includes("失败") || text.includes("无数据")) ? "#f44336" : "#2196f3";
            }
        }
    }
    if (startTime && endTime && rangeId) {
        const rangeEl = document.getElementById(rangeId);
        if (rangeEl) rangeEl.innerText = `${fmt(startTime)} - ${fmt(endTime)}`;
    }
}

// ---------------------- 业务：上传 ----------------------

function openUploadModal(type) {
    // 【修正2】打开弹窗的函数，自己负责设置 UI 状态
    document.getElementById('modalFooter').style.display = 'block';

    const modalBg = document.getElementById('modalBg');
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <h3>上传 ${type.toUpperCase()} 数据</h3>
        <div class="drag-area" id="dragArea">点击选择文件</div>
        <input type="file" id="fileInput" style="display:none;">
        <div id="fileInfo"></div>
        <button class="btn" onclick="startUpload('${type}')">开始上传</button>`;

    const dragArea = document.getElementById('dragArea');
    const fileInput = document.getElementById('fileInput');
    dragArea.onclick = () => fileInput.click();
    dragArea.ondragover = e => { e.preventDefault(); dragArea.classList.add('dragover'); };
    dragArea.ondragleave = e => dragArea.classList.remove('dragover');
    dragArea.ondrop = e => {
        e.preventDefault();
        dragArea.classList.remove('dragover');
        if (e.dataTransfer.files[0]) document.getElementById('fileInfo').innerText = `文件名: ${e.dataTransfer.files[0].name}`;
    };
    fileInput.onchange = e => {
        if (e.target.files[0]) document.getElementById('fileInfo').innerText = `文件名: ${e.target.files[0].name}`;
    };
    
    modalBg.style.display = 'flex';
}

function startUpload(type) {
    const file = document.getElementById('fileInput').files[0];
    if (!file) return showToast('请选择文件', 'error');
    const stationId = document.getElementById('stationSelect').value;
    if (!stationId) return showToast('请先选择站点', 'error');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);
    formData.append('device', stationId);

    updateStatusUI(type, "上传中...", "30%");
    closeModal();

    fetch('/upload_data', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(res => {
            if (res.error) {
                updateStatusUI(type, "上传失败", "0%");
                showToast("上传失败：" + res.error, 'error');
            } else {
                updateStatusUI(type, "上传完成", "100%", res.start_time, res.end_time);
                showToast("上传完成: " + file.name);
            }
            loadSiteDatasets();
        }).catch(err => {
            updateStatusUI(type, "上传失败", "0%");
            showToast("上传异常: " + err, 'error');
        });
}

// ---------------------- 业务：合并下载 ----------------------

function openUnifiedDownloadModal() {
    // 【修正2】打开弹窗的函数，自己负责设置 UI 状态
    document.getElementById('modalFooter').style.display = 'block';

    const modalBg = document.getElementById('modalBg');
    const modalBody = document.getElementById('modalBody');
    const defaultPriority = ['Device', 'cros', 'ec', 'era5'];
    modalBody.innerHTML = `
        <h3>下载数据</h3>
        <label>起始时间: </label><input type="datetime-local" id="unifiedStart"><br><br>
        <label>结束时间: </label><input type="datetime-local" id="unifiedEnd"><br><br>
        <div class="download-mode">
            <label>数据类别:</label>
            <label><input type="radio" name="downloadMode" value="train" checked> train</label>
            <label><input type="radio" name="downloadMode" value="pred"> pred</label>
        </div>
        <div>
            ${['pwv', 'weather', 'rain'].map(t => `<label style="margin-right:10px;"><input type="checkbox" id="chk_${t === 'weather' ? 'hw' : (t === 'rain' ? 'rn' : 'pw')}" checked> ${t.toUpperCase()}</label>`).join('')}
        </div>
        <div style="margin-top:12px;">
            <div style="font-weight:600;margin-bottom:6px;">数据源优先级</div>
            <div id="unifiedPriorityList" class="priority-list"></div>
        </div>
        <div style="margin-top:12px; text-align:right;">
            <button class="btn" onclick="startUnifiedDownload()">确认合并</button>
        </div>`;

    const pList = document.getElementById('unifiedPriorityList');
    defaultPriority.forEach(p => {
        const div = document.createElement('div');
        div.className = 'priority-item';
        div.dataset.source = p;
        div.innerHTML = `<span style="flex:1;">${p}</span><button class="btn small" onclick="movePriority(this, -1)">↑</button><button class="btn small" onclick="movePriority(this, 1)">↓</button>`;
        pList.appendChild(div);
    });
    modalBg.style.display = 'flex';
}

function movePriority(btn, dir) {
    const item = btn.closest('.priority-item');
    if (!item) return;
    if (dir === -1 && item.previousElementSibling) item.parentElement.insertBefore(item, item.previousElementSibling);
    else if (dir === 1 && item.nextElementSibling) item.parentElement.insertBefore(item.nextElementSibling, item);
}

function startUnifiedDownload() {
    let devices = Array.from(stations);
    let inputVal = (document.getElementById('stationSelect')?.value || '').trim();
    if (inputVal) inputVal = inputVal.split(/\s+/).pop();
    if (devices.length === 0 && inputVal) devices = [inputVal];
    if (devices.length === 0) return showToast('请至少选择一个站点', 'error');

    const start = document.getElementById('unifiedStart')?.value;
    const end = document.getElementById('unifiedEnd')?.value;
    if (!start || !end) return showToast('请选择时间范围', 'error');

    const types = ['pw', 'hw', 'rn'].filter(id => document.getElementById(`chk_${id}`).checked)
        .map(id => ({ pw: 'pwv', hw: 'weather', rn: 'rain' }[id]));
    if (types.length === 0) return showToast('请至少选择一种数据类型', 'error');

    const mode = document.querySelector('input[name="downloadMode"]:checked')?.value || 'train';
    const priority = Array.from(document.querySelectorAll('#unifiedPriorityList .priority-item')).map(e => e.dataset.source);
    
    const currentUiSite = inputVal || (stations.length > 0 ? stations[0] : null);

    closeModal();
    showToast('开始批量下载...');
    types.forEach(t => updateStatusUI(t, "请求中...", "30%", start, end));

    fetch('/batch_download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ types, start_time: start, end_time: end, devices, priority, mode })
    })
    .then(res => res.json())
    .then(res => {
        if (res.error) {
             types.forEach(t => updateStatusUI(t, "请求失败", "0%"));
             return showToast('下载失败: ' + res.error, 'error');
        }
        (res.details || []).forEach(dev => {
            if (currentUiSite && dev.device === currentUiSite) {
                (dev.results || []).forEach(r => {
                    updateStatusUI(r.type, r.error || r.count <= 0 ? "无数据/失败" : "下载完成", r.error || r.count <= 0 ? "0%" : "100%", start, end);
                });
            }
        });
        if (res.merged) {
            const mergedList = Array.isArray(res.merged) ? res.merged : (res.merged.results || []);
            mergedList.forEach(m => {
                const rec = {
                    file: m.dataset,
                    site: m.site_id || m.device,
                    site_name: m.site_name || m.site_id,
                    sub_dir: m.sub_dir || '',
                    start_time: (m.time_range || '~').split('~')[0].trim(),
                    end_time: (m.time_range || '~').split('~')[1].trim(),
                    created_at: new Date().toLocaleString(),
                    path: m.dataset
                };
                if (!datasets.some(d => d.path === rec.path && d.site === rec.site)) {
                    datasets.push(rec);
                }
            });
            datasets.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            renderDatasetTable(1);
            showToast('整合完成');
        }
    })
    .catch(err => {
        types.forEach(t => updateStatusUI(t, "异常", "0%"));
        showToast('下载异常: ' + err, 'error');
    });
}

// ---------------------- 业务：删除（自定义弹框）----------------------

// 【修正3】showConfirmModal 只负责隐藏 footer
function showConfirmModal(message, onConfirm) {
    document.getElementById('modalFooter').style.display = 'none';

    const modalBg = document.getElementById('modalBg');
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div style="text-align: center; padding: 20px 10px;">
            <div style="font-size: 16px; margin-bottom: 30px; color: #333; font-weight:500;">
                ${message}
            </div>
            <div style="display: flex; justify-content: center; gap: 15px;">
                <button class="btn" id="confirmBtnCancel" style="background-color: #f0f2f5; color: #555; border: 1px solid #dcdfe6; min-width:80px;">取消</button>
                <button class="btn delete-btn" id="confirmBtnOk" style="min-width:80px;">确定</button>
            </div>
        </div>`;

    modalBg.style.display = 'flex';

    document.getElementById('confirmBtnCancel').onclick = closeModal;
    document.getElementById('confirmBtnOk').onclick = () => {
        closeModal();
        if (onConfirm) onConfirm();
    };
}

function deleteDataset(filename, site) {
    showConfirmModal("确定要删除此文件吗？", () => {
        fetch(`/delete_dataset/${filename}/${site}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(res => {
                if (res.status === 'success' || (res.message && res.message.includes('不存在'))) {
                    showToast('删除成功');
                    datasets = datasets.filter(d => `${d.sub_dir}/${d.site}/${d.file}`.replace(/\\/g, "/") !== filename);
                    renderDatasetTable(currentPage);
                } else {
                    showToast('删除失败: ' + (res.message || '未知错误'), 'error');
                }
            })
            .catch(err => showToast('删除异常: ' + err, 'error'));
    });
}

// ---------------------- 业务：下载与上传TOS ----------------------

function downloadDataset(siteId, subDir, file) {
    window.location.href = `/download_dataset/${subDir}/${siteId}/${file}`;
}

async function uploadDatasetToOSS(siteId, mode, filename) {
    showToast(`上传 ${filename} 中...`, 'info');
    try {
        const data = await request('/upload_to_tos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ site: siteId, mode, filename })
        });
        showToast(data.status === 'success' ? `上传成功` : `上传失败: ${data.error}`, data.status);
    } catch (err) {
        showToast('上传出错', 'error');
    }
}

// ---------------------- 初始化与选项加载 ----------------------

async function loadOptions() {
    try {
        const projects = await request('/get_projects');
        const projSel = document.getElementById('projectSelect');
        projSel.innerHTML = '<option value="">请选择项目</option>' + projects.map(p => `<option value="${p.XMID}">${p.MC}</option>`).join('');
        projSel.onchange = loadStationsByProject;
    } catch (err) { console.error("项目加载失败", err); }

    try {
        const stationsData = await request('/get_station_options');
        document.getElementById('stationList').innerHTML = stationsData.map(st => `<option value="${st}"></option>`).join('');
        
        if (stations.length === 0) {
            const data = await request('/get_datasets');
            if (data.length > 0) {
                stations.push(data[0].site_id);
                renderStationTags();
                const inp = document.getElementById('stationSelect');
                if (inp) inp.value = stations[0];
                loadSiteDatasets();
            }
        }
    } catch (err) { console.error("站点加载失败", err); }
}

async function loadStationsByProject() {
    const xmid = document.getElementById("projectSelect").value;
    if (!xmid) return;
    try {
        const sites = await request(`/get_sites_by_project?xmid=${encodeURIComponent(xmid)}`);
        document.getElementById("stationList").innerHTML = sites.map(s => `<option value="${s.MC}  ${s.ID}" data-id="${s.ID}"></option>`).join('');
    } catch (err) { console.error("站点加载失败", err); }
}

document.addEventListener("DOMContentLoaded", () => {
    loadOptions();
    renderStationTags();
});