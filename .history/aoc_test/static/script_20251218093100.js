let datasets = [];
let currentPage = 1;
const pageSize = 5;
let stations = []; // 站点队列
let currentDownloadMode = "train";

// 工具函数

function fmt(dt) {
    if (!dt) return '';
    const d = new Date(dt);
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}
// Toast 提示
function showToast(message, type = 'success') {
    let toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.style.background = type === 'error' ? '#ef4444' : '#10b981'; 
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

// 站点管理 

function addStationFromInput() {
    const inp = document.getElementById('stationSelect');
    const v = (inp.value || '').trim();

    if (!v) return showToast('请输入站点再添加', 'error');

    // 支持 "名称 ID" 格式，取最后一部分作为 ID
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

// 监听输入框
function onStationInputKeydown(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        addStationFromInput();
    }
}

// 渲染站点标签
function renderStationTags() {
    const box = document.getElementById('stationTags');
    if (!box) return;
    box.innerHTML = stations.map(s => 
        `<span class="station-tag">${s} <span class="remove-tag" onclick="removeStation('${s}')">×</span></span>`
    ).join('');
}

// 移除站点
function removeStation(s) {
    stations = stations.filter(x => x !== s);
    renderStationTags();
    
    const input = document.getElementById('stationSelect');
    // 如果列表空了，清空输入框
    if (input) input.value = stations.length > 0 ? stations[0] : '';
    
    loadSiteDatasets();
}

// 清空站点列表
function clearStationList() {
    stations = [];
    renderStationTags();
    const input = document.getElementById('stationSelect');
    if (input) input.value = '';
    showToast('站点列表已清空');
    
    datasets = [];
    renderPagination();
    renderDatasetTable(1);
    
    // 清空状态栏
    ['pwv', 'weather', 'rain'].forEach(t => updateStatusUI(t, "未操作", "0%"));
}

// 数据表格与渲染
async function loadSiteDatasets() {
    // 如果没有站点，直接清空表格并返回
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
                    count: d.count,  
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
        // 根据是否有选站点显示不同提示
        const msg = stations.length > 0 ? '暂无数据' : '未选择站点';
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 30px; color: #9ca3af;">${msg}</td></tr>`;
        if (datasetCount) datasetCount.innerText = '';
        if (pagination) pagination.innerHTML = '';
        return;
    }

    const startIdx = (page - 1) * pageSize;
    const pageData = datasets.slice(startIdx, startIdx + pageSize);

    pageData.forEach(ds => {
        const filePath = `${ds.sub_dir}/${ds.site}/${ds.file}`;
        const tr = document.createElement('tr');
        
        // 获取 count
        const countDisplay = (ds.count !== undefined && ds.count !== null) ? ds.count : 0;

        tr.innerHTML = `
            <td class="td-dataset-name">${ds.file || ''}</td>
            <td class="td-site-id">${ds.site || '未知'}</td>
            <td>${ds.site_name || ('站点' + ds.site)}</td>
            
            <!-- 【关键】：显示样本数量 -->
            <td>${countDisplay} 条</td>
            
            <td>${ds.created_at || ''}</td>
            <td>
                <div style="display: flex; gap: 8px; justify-content: flex-start;">
                    <button class="btn delete-btn small" onclick="deleteDataset('${filePath}','${ds.site}')">删除</button>
                    <button class="btn download-btn small" onclick="downloadDataset('${ds.site}','${ds.sub_dir}','${ds.file}')">下载</button>
                    <button class="btn upload-btn small" onclick="uploadDatasetToOSS('${ds.site}','${ds.sub_dir}','${ds.file}')">上传</button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });

    renderPagination();
}

// 渲染分页
function renderPagination() {
    const pagination = document.getElementById('datasetPagination');
    const datasetCount = document.getElementById('datasetCount');
    
    if (!pagination || datasets.length === 0) return;
    
    // 更新左侧计数信息
    if (datasetCount) {
        datasetCount.innerText = `共 ${datasets.length} 个数据集`;
    }
    
    pagination.innerHTML = '';
    const totalPages = Math.ceil(datasets.length / pageSize);
    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        if (i === currentPage) btn.classList.add('active');
        btn.onclick = () => renderDatasetTable(i);
        pagination.appendChild(btn);
    }
}

// 弹窗控制
function closeModal() {
    document.getElementById('modalBg').style.display = 'none';
    
    // 恢复底部通用关闭按钮的显示，防止影响下一次打开其他弹窗
    const footer = document.getElementById('modalFooter');
    if (footer) footer.style.display = 'block';
}

// 确保弹窗底部通用关闭按钮可见
function ensureModalFooterVisible() {
    const footer = document.getElementById('modalFooter');
    if (footer) footer.style.display = 'block';
}

// 更新状态栏
function updateStatusUI(type, text, progressWidth, startTime, endTime) {
    type = (type || '').toLowerCase();
    
    const statusId = { pwv: "pwvStatus", weather: "weatherStatus", rain: "rainStatus" }[type];
    const rangeId = { pwv: "pwvTimeRange", weather: "weatherTimeRange", rain: "rainTimeRange" }[type];
    
    const statusEl = document.getElementById(statusId);
    if (statusEl) {
        statusEl.innerHTML = `<span style="font-weight:500">${text}</span>`;
        const tr = statusEl.closest('tr');
        if (tr) {
            const bar = tr.querySelector(".progress");
            if (bar) {
                bar.style.width = progressWidth;
                // 根据状态改变颜色
                if(text.includes("失败") || text.includes("无数据")) {
                    bar.style.backgroundColor = "#ef4444"; 
                } else {
                    bar.style.backgroundColor = "#3b82f6"; 
                }
            }
        }
    }
    
    if (startTime && endTime && rangeId) {
        const rangeEl = document.getElementById(rangeId);
        if (rangeEl) rangeEl.innerText = `${fmt(startTime)} - ${fmt(endTime)}`;
    }
}

// 上传 

function openUploadModal(type) {
    ensureModalFooterVisible(); // 确保显示通用关闭按钮
    const modalBg = document.getElementById('modalBg');
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <h3 style="margin-top:0;">上传 ${type.toUpperCase()} 数据</h3>
        <div class="drag-area" id="dragArea">点击或拖拽文件到此处</div>
        <input type="file" id="fileInput" style="display:none;">
        <div id="fileInfo" style="margin-bottom:15px; font-size:13px; color:#666; height:20px;"></div>
        <button class="btn" style="width:100%" onclick="startUpload('${type}')">开始上传</button>`;

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
        if (file) document.getElementById('fileInfo').innerText = `文件名: ${file.name} (${(file.size/1024).toFixed(1)} KB)`;
    }
    
    modalBg.style.display = 'flex';
}

// 开始上传
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
    closeModal(); // 上传开始后即可关闭弹窗

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

// ---------------------- 合并下载 ----------------------

function openUnifiedDownloadModal() {
    ensureModalFooterVisible(); 
    const modalBg = document.getElementById('modalBg');
    const modalBody = document.getElementById('modalBody');
    const defaultPriority = ['Device', 'cros', 'ec', 'era5'];

    modalBody.innerHTML = `
        <h3 style="margin-top:0;">下载数据</h3>
        <label>起始时间: </label><input type="datetime-local" id="unifiedStart" style="margin-bottom:10px;"><br>
        <label>结束时间: </label><input type="datetime-local" id="unifiedEnd"><br>
        <div class="download-mode">
            <span style="font-weight:600; font-size:14px;">数据类别:</span>
            <label><input type="radio" name="downloadMode" value="train" checked> train</label>
            <label><input type="radio" name="downloadMode" value="pred"> pred</label>
        </div>
        <div style="margin-bottom:15px;">
            ${['pwv', 'weather', 'rain'].map(t => `<label style="margin-right:15px; cursor:pointer;"><input type="checkbox" id="chk_${t === 'weather' ? 'hw' : (t === 'rain' ? 'rn' : 'pw')}" checked> ${t.toUpperCase()}</label>`).join('')}
        </div>
        <div>
            <div style="font-weight:600;margin-bottom:6px; font-size:14px;">数据源优先级</div>
            <div id="unifiedPriorityList" class="priority-list"></div>
        </div>
        <div style="margin-top:20px;">
            <button class="btn" style="width:100%" onclick="startUnifiedDownload()">确认合并并下载</button>
        </div>`;

    const pList = document.getElementById('unifiedPriorityList');
    defaultPriority.forEach(p => {
        const div = document.createElement('div');
        div.className = 'priority-item';
        div.dataset.source = p;
        div.innerHTML = `<span style="flex:1; font-size:13px;">${p}</span>
            <div style="display:flex; gap:4px;">
                <button class="btn small" onclick="movePriority(this, -1)">↑</button>
                <button class="btn small" onclick="movePriority(this, 1)">↓</button>
            </div>`;
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
    // 获取站点列表
    let devices = Array.from(stations);
    let inputVal = (document.getElementById('stationSelect')?.value || '').trim();

    // 解析输入框的值 (支持 "Name ID" 格式取 ID)
    if (inputVal) {
        const parts = inputVal.split(/\s+/);
        inputVal = parts[parts.length - 1];
    }

    if (devices.length === 0 && inputVal) devices = [inputVal];
    if (devices.length === 0) return showToast('请至少选择一个站点', 'error');

    //获取参数
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

    // 确定当前应该显示哪个站点的进度
    const currentUiSite = inputVal || (stations.length > 0 ? stations[0] : null);

    closeModal();
    showToast('开始批量下载...');
    
    // 初始化为请求中
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

        // 更新状态条
        (res.details || []).forEach(dev => {
            if (currentUiSite && dev.device === currentUiSite) {
                (dev.results || []).forEach(r => {
                    if (r.error || r.count <= 0) {
                        updateStatusUI(r.type, "无数据/失败", "0%", start, end);
                    } else {
                        updateStatusUI(r.type, "下载完成", "100%", start, end);
                    }
                });
            }
        });

        // 处理文件列表合并
        if (res.merged) {
            const mergedList = Array.isArray(res.merged) ? res.merged : (res.merged.results || []);
            mergedList.forEach(m => {
                const rec = {
                    file: m.dataset,
                    site: m.site_id || m.device,
                    site_name: m.site_name || m.site_id,
                    sub_dir: m.sub_dir || '',
                    count: m.count, 
                    start_time: (m.time_range || '').split('~')[0],
                    end_time: (m.time_range || '').split('~')[1],
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
        console.error(err);
    });
}

// ---------------------- 删除（自定义弹框） ----------------------

function showConfirmModal(message, onConfirm) {
    const modalBg = document.getElementById('modalBg');
    const modalBody = document.getElementById('modalBody');
    const modalFooter = document.getElementById('modalFooter');

    // 隐藏底部的通用关闭按钮
    if (modalFooter) modalFooter.style.display = 'none';

    // 渲染内容
    modalBody.innerHTML = `
        <div style="text-align: center; padding: 20px 10px;">
            <div style="font-size: 16px; margin-bottom: 30px; color: #333; font-weight:500;">
                ${message}
            </div>
            <div style="display: flex; justify-content: center; gap: 15px;">
                <!-- 取消按钮：点击直接关闭 -->
                <button class="btn btn-secondary" onclick="closeModal()" 
                    style="min-width:80px;">
                    取消
                </button>
                <!-- 确定按钮 -->
                <button class="btn delete-btn" id="confirmBtnOk" style="min-width:80px;">
                    确定
                </button>
            </div>
        </div>
    `;

    modalBg.style.display = 'flex';

    const okBtn = document.getElementById('confirmBtnOk');
    okBtn.onclick = () => {
        closeModal(); // 自动恢复 footer 显示
        if (onConfirm) onConfirm();
    };
}

function deleteDataset(filename, site) {
    showConfirmModal("确定要删除此文件吗？此操作不可恢复。", () => {
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
            })
            .catch(err => showToast('删除异常: ' + err, 'error'));
    });
}

// ---------------------- 下载与上传TOS ----------------------

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
        
        if (data.status === 'success') {
            // 检查外部接口的回调结果
            const cbRes = data.dataset_upload_response || {};
            if (cbRes.error) {
                showToast(`TOS上传成功，但业务回调失败: ${cbRes.error}`, 'warning');
            } else {
                showToast(`上传成功`, 'success');
            }
        } else {
            showToast(`上传失败: ${data.error}`, 'error');
        }
    } catch (err) {
        showToast('上传出错', 'error');
        console.error(err);
    }
}

// ---------------------- 初始化与选项加载 ----------------------

async function loadOptions() {
    // 加载项目
    try {
        const projects = await request('/get_projects');
        const projSel = document.getElementById('projectSelect');
        projSel.innerHTML = '<option value="">请选择项目</option>' + projects.map(p => `<option value="${p.XMID}">${p.MC}</option>`).join('');
        
        projSel.addEventListener("change", loadStationsByProject);
    } catch (err) { console.error("项目加载失败", err); }

    // 加载站点 (默认加载 json)
    try {
        const stationsData = await request('/get_station_options');
        const datalist = document.getElementById('stationList');
        datalist.innerHTML = stationsData.map(st => `<option value="${st}">`).join('');
        
        // 保持页面初始状态为空
        
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

document.addEventListener("DOMContentLoaded", () => {
    loadOptions();
    renderStationTags();
});