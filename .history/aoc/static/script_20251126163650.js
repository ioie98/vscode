let datasets = [];
let currentPage = 1;
const pageSize = 5;

// 站点队列
let stations = [];

// 当前下载模式（train or pred），默认 train
let currentDownloadMode = "train";

// 将当前输入添加到站点队列
function addStationFromInput() {
    const inp = document.getElementById('stationSelect');
    if(!inp) return;
    const v = (inp.value || '').trim();
    if(!v) { showToast('请输入站点再添加','error'); return; }
    if(stations.includes(v)) { showToast(`${v} 已在列表中`); inp.value=''; return; }
    stations.push(v);
    renderStationTags();

    inp.value = v;
    loadSiteDatasets();
}

// 回车添加
function onStationInputKeydown(e){
    if(e.key === 'Enter'){
        e.preventDefault();
        addStationFromInput();
    }
}

// 渲染标签
function renderStationTags(){
    const box = document.getElementById('stationTags');
    if(!box) return;
    box.innerHTML = '';
    stations.forEach(s=>{
        const span = document.createElement('span');
        span.className = 'station-tag';
        span.innerHTML = `${s} <span class="remove-tag" onclick="removeStation('${s}')">×</span>`;
        box.appendChild(span);
    });
}

// 移除站点
function removeStation(s){
    stations = stations.filter(x=>x!==s);
    renderStationTags();

    const input = document.getElementById('stationSelect');
    if(input){
        input.value = stations.length>0 ? stations[0] : '';
    }

    loadSiteDatasets();
}

// 清空站点列表
function clearStationList(){
    stations = [];
    renderStationTags();
    const input = document.getElementById('stationSelect');
    if(input) input.value = '';
    showToast('站点列表已清空');

    datasets = [];
    currentPage = 1;
    const tbody = document.getElementById('datasetTableBody');
    const datasetCount = document.getElementById('datasetCount');
    if(tbody) tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;">暂无数据</td></tr>`;
    if(datasetCount) datasetCount.innerText = '';

    renderPagination();
}

// Toast
function showToast(message, type='success') {
    let toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.style.background = type==='error' ? '#f44336' : '#4caf50';
    toast.innerText = message;
    document.body.appendChild(toast);
    setTimeout(()=>{ toast.style.opacity = 1; }, 100);
    setTimeout(()=>{ toast.style.opacity = 0; setTimeout(()=> document.body.removeChild(toast), 500); }, 2500);
}

// 上传弹框
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
    dragArea.addEventListener('dragover', e => { e.preventDefault(); dragArea.classList.add('dragover'); });
    dragArea.addEventListener('dragleave', e => { e.preventDefault(); dragArea.classList.remove('dragover'); });
    dragArea.addEventListener('drop', e => {
        e.preventDefault();
        dragArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        document.getElementById('fileInfo').innerText = `文件名: ${file.name}, 大小: ${file.size} bytes`;
    });
    fileInput.onchange = e => {
        const file = e.target.files[0];
        document.getElementById('fileInfo').innerText = `文件名: ${file.name}, 大小: ${file.size} bytes`;
    };
    modalBg.style.display = 'flex';
}

function startUpload(type) {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    if (!file) { showToast('请选择文件', 'error'); return; }

    const stationSelect = document.getElementById('stationSelect');
    const stationId = stationSelect.value;
    if(!stationId){ showToast('请先选择站点','error'); return; }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);
    formData.append('device', stationId);

    const statusId = { pwv: "pwvStatus", weather: "weatherStatus", rain: "rainStatus" }[type];
    const row = document.getElementById(statusId);
    const progress = row ? row.parentElement.querySelector(".progress") : null;
    if(row) row.textContent = "上传中...";
    if(progress) progress.style.width = "30%";

    fetch('/upload_data', { method: 'POST', body: formData })
      .then(res => res.json())
      .then(res => {
          if (res.error) {
              if(row) row.textContent = "上传失败";
              showToast("上传失败：" + res.error, 'error');
          } else {
              if(row) row.textContent = "上传完成";
              if(progress) progress.style.width = "100%";
              showToast("上传完成: " + file.name);
              if(res.start_time && res.end_time){
                  const rangeId = { pwv:"pwvTimeRange", weather:"weatherTimeRange", rain:"rainTimeRange" }[type];
                  if(rangeId) document.getElementById(rangeId).innerText = `${res.start_time} - ${res.end_time}`;
              }
          }
          closeModal();
          loadSiteDatasets();
      }).catch(err=>{
          if(row) row.textContent = "上传失败";
          if(progress) progress.style.width = "0%";
          showToast("上传异常: " + err, 'error');
          closeModal();
      });
}

// 批量下载（保留原逻辑，只调整路径）
function startUnifiedDownload() {
    let devices = Array.from(stations);
    const inputVal = (document.getElementById('stationSelect')?.value || '').trim();
    if (devices.length === 0 && inputVal) devices = [inputVal];
    if (devices.length === 0) { showToast('请添加或选择至少一个站点', 'error'); return; }

    const start = document.getElementById('unifiedStart')?.value;
    const end = document.getElementById('unifiedEnd')?.value;
    if (!start || !end) { showToast('请选择起始与结束时间', 'error'); return; }

    const types = [];
    if (document.getElementById('chk_pw').checked) types.push('pwv');
    if (document.getElementById('chk_hw').checked) types.push('weather');
    if (document.getElementById('chk_rn').checked) types.push('rain');
    if (types.length === 0) { showToast('请选择至少一种数据类型', 'error'); return; }

    const modeEl = document.querySelector('input[name="downloadMode"]:checked');
    const mode = modeEl ? modeEl.value : 'train';

    const pElems = Array.from(document.querySelectorAll('#unifiedPriorityList .priority-item'));
    const priorityOrder = pElems.map(e => e.dataset.source);

    closeModal();
    showToast('开始批量下载任务，正在下载并自动整合……');

    fetch('/batch_download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ types, start_time: start, end_time: end, devices, priority: priorityOrder, mode })
    })
        .then(res => res.json())
        .then(res => {
            if (res.error) { showToast('批量下载失败: ' + res.error, 'error'); console.error(res); return; }

            const details = res.details || [];
            for (const dev of details) {
                const device = dev.device;
                for (const r of dev.results || []) {
                    if (r.error) {
                        showToast(`站点 ${device} - ${r.type} 失败：${r.error}`, 'error');
                    } else if (r.count === 0) {
                        showToast(`站点 ${device} - ${r.type} 无数据`);
                    } else {
                        showToast(`站点 ${device} - ${r.type} 下载 ${r.count} 条`);
                    }
                    const curSite = (document.getElementById('stationSelect')?.value || '').trim();
                    if (curSite && curSite === device) {
                        const statusId = { pwv: "pwvStatus", weather: "weatherStatus", rain: "rainStatus" }[r.type];
                        const statusEl = document.getElementById(statusId);
                        const progress = statusEl ? statusEl.parentElement.querySelector(".progress") : null;
                        if (r.error || r.count <= 0) {
                            if (statusEl) statusEl.textContent = "下载失败/无数据";
                            if (progress) progress.style.width = "0%";
                        } else {
                            if (statusEl) statusEl.textContent = "下载完成";
                            if (progress) progress.style.width = "100%";
                            const rangeId = { pwv: "pwvTimeRange", weather: "weatherTimeRange", rain: "rainTimeRange" }[r.type];
                            if (rangeId) document.getElementById(rangeId).innerText = `${start} - ${end}`;
                        }
                    }
                }
            }

            if (res.merged && ((res.merged.results && Array.isArray(res.merged.results)) || Array.isArray(res.merged))) {
                const mergedList = res.merged.results ? res.merged.results : res.merged;
                mergedList.forEach(m => {
                    const rec = {
                        file: m.dataset.split('/').pop() || `${m.site_id || 'site'}_unknown.csv`,
                        site: m.site_id || m.device || 'unknown',
                        site_name: m.site_name || m.site_id || m.device || '未知站点',
                        sub_dir: m.sub_dir || '', // train/pred
                        start_time: m.time_range?.split('~')[0]?.trim() || '',
                        end_time: m.time_range?.split('~')[1]?.trim() || '',
                        created_at: new Date().toLocaleString(),
                        path: m.dataset // 后端返回完整路径 train/b100/b100_250301_250320.csv
                    };
                    if (!datasets.some(d => d.path === rec.path && d.site === rec.site && d.sub_dir === rec.sub_dir)) {
                        datasets.push(rec);
                    }
                });
                datasets.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                renderDatasetTableMultiSite(datasets);
                showToast('整合完成');
            }
        })
        .catch(err => { showToast('批量下载异常: ' + err, 'error'); console.error(err); });
}

// 渲染多站点表格
function renderDatasetTableMultiSite(fileList){
    const tbody = document.getElementById('datasetTableBody');
    if(!tbody) return;
    tbody.innerHTML = '';

    if(!fileList || fileList.length === 0){
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;">暂无数据</td></tr>`;
        return;
    }

    fileList.forEach(item => {
        const file = item.file || '';
        const siteId = item.site || '未知站点';
        const siteName = item.site_name || ('站点' + siteId);
        const startTime = item.start_time || '';
        const endTime = item.end_time || '';
        const createdAt = item.created_at || '';
        const filePath = `${item.sub_dir || 'train'}/${siteId}/${file}`;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${file}</td>
            <td>${siteId}</td>
            <td>${siteName}</td>
            <td>${startTime} ~ ${endTime}</td>
            <td>${createdAt}</td>
            <td>
                <button class="btn detail-btn" onclick="showDetails('${siteId}','${item.sub_dir || 'train'}','${file}')">详情</button>
                <button class="btn delete-btn" onclick="deleteDataset('${encodeURIComponent(filePath)}','${siteId}')">删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// 站点列表加载
function loadStationList(){
    fetch('/get_datasets')
    .then(res=>res.json())
    .then(data=>{
        const dataList = document.getElementById('stationList');
        const input = document.getElementById('stationSelect');
        if(!dataList || !input) return;

        dataList.innerHTML = '';
        for(const site of data){
            const opt = document.createElement('option');
            opt.value = site.site_id;
            dataList.appendChild(opt);
        }

        if(stations.length === 0 && data.length>0){
            stations.push(data[0].site_id);
            renderStationTags();
        }
        if(data.length>0){
            input.value = stations[0] || data[0].site_id;
        }

        loadSiteDatasets();
    }).catch(err=>console.error('加载站点列表失败', err));
}

// 加载当前站点 train/pred 数据
function loadSiteDatasets() {
    const site = document.getElementById('stationSelect')?.value.trim();
    if(!site) return;

    const tbody = document.getElementById('datasetTableBody');
    const datasetCount = document.getElementById('datasetCount');
    if(!tbody || !datasetCount) return;

    tbody.innerHTML = '';
    datasetCount.innerText = '';
    datasets = [];
    currentPage = 1;
    renderPagination();

    fetch(`/get_datasets?site=${encodeURIComponent(site)}`)
        .then(r => r.json())
        .then(res => {
            const trainList = res.train || [];
            const predList = res.pred || [];

            trainList.forEach(d => datasets.push({ ...d, sub_dir:'train' }));
            predList.forEach(d => datasets.push({ ...d, sub_dir:'pred' }));

            if(datasets.length === 0){
                tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;">暂无数据</td></tr>`;
                datasetCount.innerText = '';
                renderPagination();
                return;
            }

            datasets.sort((a,b)=> new Date(b.created_at) - new Date(a.created_at));
            currentPage = 1;
            renderDatasetTable(currentPage);
        })
        .catch(err => console.error('加载数据集失败:', err));
}

// 删除文件
function deleteDataset(filename, site){
    const siteVal = site || (document.getElementById('stationSelect')?.value || '').trim();
    if(!siteVal){ showToast('站点未选择','error'); return; }

    fetch(`/delete_dataset/${filename}/${siteVal}`, { method:'DELETE' })
        .then(res=>res.json())
        .then(res=>{
            if(res.status==='success'){
                showToast('删除成功');
                datasets = datasets.filter(d => `${d.sub_dir}/${d.site}/${d.file}` !== decodeURIComponent(filename));
                if(datasets.length === 0){
                    document.getElementById('datasetTableBody').innerHTML = `<tr><td colspan="6" style="text-align:center;">暂无数据</td></tr>`;
                    document.getElementById('datasetCount').innerText = '';
                } else renderDatasetTable(currentPage);
            } else showToast('删除失败: '+(res.message||''),'error');
        })
        .catch(err=>showToast('删除异常: '+err,'error'));
}

// 显示详情
function showDetails(site, mode, file){
    const modalBg = document.getElementById('modalBg');
    const modalBody = document.getElementById('modalBody');

    fetch(`/get_file_rows?site=${encodeURIComponent(site)}&mode=${encodeURIComponent(mode)}&file=${encodeURIComponent(file)}`)
    .then(res=>res.json())
    .then(data=>{
        if(data.error){
            modalBody.innerHTML = `<h3>${file} - ${site} 数据详情</h3>
                                   <p style="color:red;">${data.error}</p>`;
        } else {
            const rows = data.rows || [];
            let tableHTML = `<h3>${file} - ${site} 数据详情</h3>
                             <div style="max-height:400px; overflow:auto;">
                             <table>
                               <thead>
                                 <tr>
                                   <th>date</th>
                                   <th>t2m</th>
                                   <th>sp</th>
                                   <th>rh</th>
                                   <th>pwv</th>
                                   <th>tp</th>
                                 </tr>
                               </thead>
                               <tbody>`;
            for(const r of rows){
                tableHTML += `<tr>
                                <td>${r.date || ''}</td>
                                <td>${r.t2m !== null ? r.t2m : ''}</td>
                                <td>${r.sp !== null ? r.sp : ''}</td>
                                <td>${r.rh !== null ? r.rh : ''}</td>
                                <td>${r.pwv !== null ? r.pwv : ''}</td>
                                <td>${r.tp !== null ? r.tp : ''}</td>
                              </tr>`;
            }
            tableHTML += `</tbody></table></div>`;
            modalBody.innerHTML = tableHTML;
        }
        modalBg.style.display = 'flex';
    })
    .catch(err=>{ showToast('获取详情失败: '+err,'error'); });
}

function closeModal(){
    document.getElementById('modalBg').style.display = 'none';
}

window.onload = ()=>{
    loadStationList();
    renderStationTags();
    const inp = document.getElementById('stationSelect');
    if(inp) inp.addEventListener('keydown', onStationInputKeydown);
};
