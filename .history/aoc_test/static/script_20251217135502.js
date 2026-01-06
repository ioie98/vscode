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
    
    // 强制重绘以触发 transition
    requestAnimationFrame(() => {
        toast.style.opacity = 1;
    });

    setTimeout(() => {
        toast.style.opacity = 0;
        setTimeout(() => document.body.removeChild(toast), 500);
    }, 2500);
}

// 统一 Fetch 封装
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
    loadSiteDatasets(); // 刷新表格
}

function onStationInputKeydown(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        addStationFromInput();
    }
}

function renderStationTags() {
    const box = document.getElementById('stationTags');
    if (!box) return;
    box.innerHTML = stations.map(s => 
        `<span class="station-tag">${s} <span class="remove-tag" onclick="removeStation('${s}')">×</span></span>`
    ).join('');
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
    renderPagination();
    renderDatasetTable(1);
}

// ---------------------- 数据表格与渲染 ----------------------

// 加载当前站点（第一个）的数据
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
        
        // 合并 train 和 pred，统一格式
        ['train', 'pred'].forEach(subDir => {
            (res[subDir] || []).forEach(d => {
                datasets.push({
                    file: d.name,
                    site: d.site,
                    site_name: d.site_name,
                    sub_dir: subDir,
                    start_time: d.start_time,
                    end_time: d.end_time,
                    created_at: d.created_at,
                    path: d.path
                });
            });
        });

        datasets.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        renderDatasetTable(1);
    } catch (err) {
        console.error("加载数据失败:", err);
    }
}

// 统一渲染表格
function renderDatasetTable(page) {
    currentPage = page;
    const tbody = document.getElementById('datasetTableBody');
    const datasetCount = document.getElementById('datasetCount');
    const pagination = document.getElementById('datasetPagination');
    
    if (!tbody) return;
    tbody.innerHTML = '';

    if (datasets.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;">${stations.length ? '暂无数据' : '未选择站点'}</td></tr>`;
        if (datasetCount) datasetCount.innerText = '';
        if (pagination) pagination.innerHTML = '';
        return;
    }

    const startIdx = (page - 1) * pageSize;
    const pageData = datasets.slice(startIdx, startIdx + pageSize);

    pageData.forEach(ds => {
        const filePath = `${ds.sub_dir}/${ds.site}/${ds.file}`;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${ds.file || ''}</td>
            <td>${ds.site || '未知'}</td>
            <td>${ds.site_name || ('站点' + ds.site)}</td>
            <td>${ds.start_time || ''} ~ ${ds.end_time || ''}</td>
            <td>${ds.created_at || ''}</td>
            <td>
                <button class="btn delete-btn" onclick="deleteDataset('${filePath}','${ds.site}')">删除</button>
                <button class="btn download-btn" onclick="downloadDataset('${ds.site}','${ds.sub_dir}','${ds.file}')">下载</button>
                <button class="btn upload-btn" onclick="uploadDatasetToOSS('${ds.site}','${ds.sub_dir}','${ds.file}')">上传</button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    renderPagination();
}

function renderPagination() {
    const pagination = document.getElementById('datasetPagination');
    if (!pagination || datasets.length === 0) return;
    
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

// ---------------------- 交互操作：上传/下载/删除 ----------------------

function openUploadModal(type) {
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
    dragArea.ondragleave = e => { e.preventDefault(); dragArea.classList.remove('dragover'); };
    dragArea.ondrop = e => {
        e.preventDefault();
        dragArea.classList.remove('dragover');
        handleFileSelect(e.dataTransfer.files[0]);
    };
    fileInput.onchange = e => handleFileSelect(e.target.files[0]);

    function handleFileSelect(file) {
        if (file) document.getElementById('fileInfo').innerText = `文件名: ${file.name}, 大小: ${file.size} bytes`;
    }
    
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
            closeModal();
            loadSiteDatasets();
        }).catch(err => {
            updateStatusUI(type, "上传失败", "0%");
            showToast("上传异常: " + err, 'error');
            closeModal();
        });
}

// 更新状态栏 UI
// 更新状态栏 UI (增强版)
function updateStatusUI(type, text, progressWidth, startTime, endTime) {
    // 1. 确保类型全小写，防止大小写不匹配
    type = (type || '').toLowerCase(); 
    
    // 2. 映射 ID
    const statusId = { pwv: "pwvStatus", weather: "weatherStatus", rain: "rainStatus" }[type];
    const rangeId = { pwv: "pwvTimeRange", weather: "weatherTimeRange", rain: "rainTimeRange" }[type];
    
    // 3. 更新状态文字
    const statusEl = document.getElementById(statusId);
    if (statusEl) {
        statusEl.textContent = text;
        
        // 4. 更新进度条 (通过父级 TR 查找，更稳健)
        // 逻辑：从 statusTD 找到父级 TR，再在 TR 里找 .progress
        const tr = statusEl.closest('tr'); 
        if (tr) {
            const bar = tr.querySelector(".progress");
            if (bar) {
                // 强制移除内联 width 0% 并重新设置
                bar.style.width = progressWidth;
                
                // 颜色处理：如果是 100% 或者是 "下载完成"，保持蓝色或变绿；如果是 "失败"，变红
                if(text.includes("失败") || text.includes("无数据")) {
                    bar.style.backgroundColor = "#f44336"; // 红
                } else {
                    bar.style.backgroundColor = "#2196f3"; // 蓝
                }
            }
        }
    } else {
        console.warn(`无法找到状态元素 ID: ${statusId} (type: ${type})`);
    }
    
    // 5. 更新时间范围
    if (startTime && endTime && rangeId) {
        const rangeEl = document.getElementById(rangeId);
        if (rangeEl) {
            rangeEl.innerText = `${fmt(startTime)} - ${fmt(endTime)}`;
        }
    }
}

// 统一合并下载
function openUnifiedDownloadModal() {
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
        div.innerHTML = `<span style="flex:1;">${p}</span>
            <button class="btn small" onclick="movePriority(this, -1)">↑</button>
            <button class="btn small" onclick="movePriority(this, 1)">↓</button>`;
        pList.appendChild(div);
    });
    modalBg.style.display = 'flex';
}

function movePriority(btn, dir) {
    const item = btn.closest('.priority-item');
    const list = btn.closest('.priority-list');
    if (!item || !list) return;
    if (dir === -1 && item.previousElementSibling) list.insertBefore(item, item.previousElementSibling);
    else if (dir === 1 && item.nextElementSibling) list.insertBefore(item.nextElementSibling, item);
}

function startUnifiedDownload() {
    let devices = Array.from(stations);
    const inputVal = (document.getElementById('stationSelect')?.value || '').trim();
    if (devices.length === 0 && inputVal) devices = [inputVal];

    if (devices.length === 0) return showToast('请至少选择一个站点', 'error');

    const start = document.getElementById('unifiedStart')?.value;
    const end = document.getElementById('unifiedEnd')?.value;
    if (!start || !end) return showToast('请选择时间范围', 'error');

    const types = [];
    if (document.getElementById('chk_pw').checked) types.push('pwv');
    if (document.getElementById('chk_hw').checked) types.push('weather');
    if (document.getElementById('chk_rn').checked) types.push('rain');
    if (types.length === 0) return showToast('请至少选择一种数据类型', 'error');

    const mode = document.querySelector('input[name="downloadMode"]:checked')?.value || 'train';
    const priority = Array.from(document.querySelectorAll('#unifiedPriorityList .priority-item')).map(e => e.dataset.source);

    closeModal();
    showToast('开始批量下载...');

    fetch('/batch_download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ types, start_time: start, end_time: end, devices, priority, mode })
    })
    .then(res => res.json())
    .then(res => {
        if (res.error) return showToast('下载失败: ' + res.error, 'error');

        (res.details || []).forEach(dev => {
            (dev.results || []).forEach(r => {
                const isCurrent = (document.getElementById('stationSelect')?.value || '').trim() === dev.device;
                if (isCurrent) {
                    if (r.error || r.count <= 0) updateStatusUI(r.type, "无数据/失败", "0%");
                    else updateStatusUI(r.type, "下载完成", "100%", start, end);
                }
            });
        });

        // 合并结果到列表
        if (res.merged) {
            const mergedList = Array.isArray(res.merged) ? res.merged : (res.merged.results || []);
            mergedList.forEach(m => {
                const rec = {
                    file: m.dataset,
                    site: m.site_id || m.device,
                    site_name: m.site_name || m.site_id,
                    sub_dir: m.sub_dir || '',
                    start_time: (m.time_range || '').split('~')[0],
                    end_time: (m.time_range || '').split('~')[1],
                    created_at: new Date().toLocaleString(),
                    path: m.dataset
                };
                // 避免重复
                if (!datasets.some(d => d.path === rec.path && d.site === rec.site)) {
                    datasets.push(rec);
                }
            });
            datasets.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            renderDatasetTable(1);
            showToast('整合完成');
        }
    })
    .catch(err => showToast('下载异常: ' + err, 'error'));
}

function deleteDataset(filename, site) {
    if(!confirm("确定要删除此文件吗？")) return;
    
    fetch(`/delete_dataset/${filename}/${site}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(res => {
            if (res.status === 'success' || (res.message && res.message.includes('不存在'))) {
                showToast('删除成功');
                datasets = datasets.filter(d => {
                    const fullPath = `${d.sub_dir}/${d.site}/${d.file}`.replace(/\\/g, "/");
                    return fullPath !== filename;
                });
                renderDatasetTable(currentPage);
            } else {
                showToast('删除失败: ' + res.message, 'error');
            }
        }).catch(err => showToast('异常: ' + err, 'error'));
}

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
        if (data.status === 'success') showToast(`上传成功`, 'success');
        else showToast(`上传失败: ${data.error}`, 'error');
    } catch (err) {
        showToast('上传出错', 'error');
    }
}

function closeModal() {
    document.getElementById('modalBg').style.display = 'none';
}

// ---------------------- 动态选项加载 ----------------------

async function loadOptions() {
    // 加载项目
    try {
        const projects = await request('/get_projects');
        const projSel = document.getElementById('projectSelect');
        projSel.innerHTML = projects.map(p => `<option value="${p.XMID}">${p.MC}</option>`).join('');
        
        // 绑定项目切换事件
        projSel.addEventListener("change", loadStationsByProject);
    } catch (err) { console.error("项目加载失败", err); }

    // 加载站点
    try {
        const stationsData = await request('/get_station_options');
        const datalist = document.getElementById('stationList');
        datalist.innerHTML = stationsData.map(st => `<option value="${st}">`).join('');
        
        // 初始逻辑：如果队列空，且有数据，默认加第一个
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
        const datalist = document.getElementById("stationList");
        datalist.innerHTML = sites.map(s => `<option value="${s.MC}  ${s.ID}" data-id="${s.ID}">`).join('');
    } catch (err) { console.error("站点加载失败", err); }
}

// ---------------------- 初始化 ----------------------

document.addEventListener("DOMContentLoaded", () => {
    loadOptions();
    renderStationTags();
});