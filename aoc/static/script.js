let datasets = [];
let currentPage = 1;
const pageSize = 5;

// ---------- Toast ----------
function showToast(message, type='success') {
    let toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.style.background = type==='error' ? '#f44336' : '#4caf50';
    toast.innerText = message;
    document.body.appendChild(toast);
    setTimeout(()=>{ toast.style.opacity = 1; }, 100);
    setTimeout(()=>{
        toast.style.opacity = 0;
        setTimeout(()=> document.body.removeChild(toast), 500);
    }, 2500);
}

// ---------- 上传弹框 ----------
function openUploadModal(type) {
    const modalBg = document.getElementById('modalBg');
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <h3>上传 ${type.toUpperCase()} 数据</h3>
        <div class="drag-area" id="dragArea">拖拽文件到这里或点击选择</div>
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
    const progress = row.parentElement.querySelector(".progress");
    row.textContent = "上传中...";
    progress.style.width = "30%";

    fetch('/upload_data', { method: 'POST', body: formData })
      .then(res => res.json())
      .then(res => {
          if (res.error) {
              row.textContent = "上传失败";
              showToast("上传失败：" + res.error, 'error');
          } else {
              row.textContent = "上传完成";
              progress.style.width = "100%";
              showToast("上传完成: " + file.name);
              if(res.start_time && res.end_time){
                  const rangeId = { pwv:"pwvTimeRange", weather:"weatherTimeRange", rain:"rainTimeRange" }[type];
                  document.getElementById(rangeId).innerText = `${res.start_time} - ${res.end_time}`;
              }
          }
          closeModal();
          loadSiteDatasets();
      }).catch(err=>{
          row.textContent = "上传失败";
          progress.style.width = "0%";
          showToast("上传异常: " + err, 'error');
          closeModal();
      });
}

// ---------- 下载弹框 ----------
function openUnifiedDownloadModal(){
    const stationSelect = document.getElementById('stationSelect');
    const stationId = stationSelect.value;
    if(!stationId){ showToast('请先选择站点','error'); return; }

    const modalBg = document.getElementById('modalBg');
    const modalBody = document.getElementById('modalBody');

    const defaultPriority = ['deviced','cros','ec','era5'];

    modalBody.innerHTML = `
        <h3>下载数据（批量）</h3>
        <label>起始时间: </label><input type="datetime-local" id="unifiedStart"><br><br>
        <label>结束时间: </label><input type="datetime-local" id="unifiedEnd"><br><br>

        <div>
            <label style="margin-right:10px;"><input type="checkbox" id="chk_pw" checked> PWV</label>
            <label style="margin-right:10px;"><input type="checkbox" id="chk_hw" checked> 气象（HWS）</label>
            <label style="margin-right:10px;"><input type="checkbox" id="chk_rn" checked> 雨量筒</label>
        </div>

        <div style="margin-top:12px;">
            <div style="font-weight:600;margin-bottom:6px;">数据源优先级（上→下：高优先→低优先）</div>
            <div id="unifiedPriorityList" class="priority-list"></div>
            <div style="margin-top:8px; font-size:12px; color:#666;">
                说明：将按此优先级合并同一时间点数据。
            </div>
        </div>

        <div style="margin-top:12px; text-align:right;">
            <button class="btn" onclick="startUnifiedDownload()">确认下载</button>
        </div>
    `;

    const pList = document.getElementById('unifiedPriorityList');
    defaultPriority.forEach(p=>{
        const div = document.createElement('div');
        div.className = 'priority-item';
        div.dataset.source = p;
        div.style = 'display:flex; align-items:center; gap:8px; margin-bottom:6px;';
        div.innerHTML = `
            <span style="flex:1;">${p}</span>
            <button class="btn small" onclick="movePriority(this, -1)">↑</button>
            <button class="btn small" onclick="movePriority(this, 1)">↓</button>
        `;
        pList.appendChild(div);
    });

    modalBg.style.display = 'flex';
}

function movePriority(btn, dir){
    const item = btn.closest('.priority-item');
    const list = btn.closest('.priority-list');
    if(!item || !list) return;
    if(dir === -1 && item.previousElementSibling){
        list.insertBefore(item, item.previousElementSibling);
    }else if(dir === 1 && item.nextElementSibling){
        list.insertBefore(item.nextElementSibling, item);
    }
}

function startUnifiedDownload(){
    const stationSelect = document.getElementById('stationSelect');
    const stationId = stationSelect.value;
    if(!stationId){ showToast('请先选择站点','error'); return; }

    const start = document.getElementById('unifiedStart')?.value;
    const end = document.getElementById('unifiedEnd')?.value;
    if(!start || !end){ showToast('请选择起始与结束时间','error'); return; }

    const types = [];
    if(document.getElementById('chk_pw').checked) types.push('pwv');
    if(document.getElementById('chk_hw').checked) types.push('weather');
    if(document.getElementById('chk_rn').checked) types.push('rain');
    if(types.length === 0){ showToast('请选择至少一种数据类型','error'); return; }

    const pElems = Array.from(document.querySelectorAll('#unifiedPriorityList .priority-item'));
    const priorityOrder = pElems.map(e => e.dataset.source);

    closeModal();
    showToast('开始下载任务（批量），请稍候…');

    fetch('/batch_download', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ types, start_time: start, end_time: end, device: stationId, priority: priorityOrder })
    })
    .then(res=>res.json())
    .then(res=>{
        if(res.error){
            showToast('批量下载失败: '+res.error, 'error');
        }else{
            for(const item of res.results || []){
                const statusId = { pwv: "pwvStatus", weather: "weatherStatus", rain: "rainStatus" }[item.type];
                const statusEl = document.getElementById(statusId);
                const progress = statusEl.parentElement.querySelector(".progress");
                if(item.count >= 0){
                    statusEl.textContent = "下载完成";
                    progress.style.width = "100%";
                    const rangeId = { pwv:"pwvTimeRange", weather:"weatherTimeRange", rain:"rainTimeRange" }[item.type];
                    document.getElementById(rangeId).innerText = `${start} - ${end}`;
                    showToast(`类型 ${item.type} 下载完成：${item.count} 条`);
                }else{
                    statusEl.textContent = "下载失败";
                    progress.style.width = "0%";
                    showToast(`类型 ${item.type} 下载失败`, 'error');
                }
            }
            loadSiteDatasets();
        }
    })
    .catch(err=>{ showToast('批量下载异常: '+err, 'error'); });
}

// ---------- 数据整合 ----------
function integrateData() {
    const site = document.getElementById('stationSelect').value;
    const messageBox = document.getElementById('messageBox');
    messageBox.innerText = '';
    messageBox.style.color = '#f00';

    if (!site) {
        messageBox.innerText = '请先选择站点';
        return;
    }

    const pwvStatus = document.getElementById('pwvStatus').innerText;
    const weatherStatus = document.getElementById('weatherStatus').innerText;
    const rainStatus = document.getElementById('rainStatus').innerText;

    if([pwvStatus, weatherStatus, rainStatus].some(s => s==='未操作' || s==='')){
        messageBox.innerText = '请确保所有数据已上传或下载完成';
        return;
    }

    fetch('/merge_datasets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ site })
    })
    .then(res => res.json())
    .then(res => {
        if (res.status === 'success') {
            messageBox.style.color = '#28a745';
            messageBox.innerText = '数据整合成功！';
            loadSiteDatasets();
        } else {
            messageBox.innerText = '整合失败: ' + res.error;
        }
    })
    .catch(err => { messageBox.innerText = '请求失败: ' + err; });
}

// ---------- 站点列表 ----------
function loadStationList(){
    fetch('/get_datasets')
    .then(res=>res.json())
    .then(data=>{
        const select = document.getElementById('stationSelect');
        select.innerHTML = `<option value="">--请选择站点--</option>`;
        for(const site of data){
            const opt = document.createElement('option');
            opt.value = site.site_id;
            opt.textContent = site.site_id;
            select.appendChild(opt);
        }
        if(data.length>0){
            select.value = data[0].site_id;
            loadSiteDatasets();
        }
    });
}

// ---------- 当前站点数据 ----------
function loadSiteDatasets() {
    const site = document.getElementById('stationSelect').value;
    const tbody = document.getElementById('datasetTableBody');
    const datasetCount = document.getElementById('datasetCount');
    tbody.innerHTML = '';
    datasetCount.innerText = '';

    if (!site) return;

    fetch(`/get_datasets?site=${site}`)
        .then(res => res.json())
        .then(data => {
            // 只显示合并后的文件
            datasets = (data.datasets || []).filter(d => d.name && d.name.includes('dataset_'));

            if(datasets.length === 0){
                tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;">暂无数据</td></tr>`;
                return;
            }
            renderPagination();
            renderDatasetTable(currentPage);
        })
        .catch(err => console.error('加载数据集失败:', err));
}

// ---------- 删除 ----------
function deleteDataset(filename){
    const site = document.getElementById('stationSelect').value;
    fetch(`/delete_dataset/${filename}/${site}`, { method:'DELETE' })
        .then(res=>res.json())
        .then(res=>{
            if(res.status==='success'){
                showToast('删除成功');
                loadSiteDatasets();
            }else showToast('删除失败: '+(res.message||''),'error');
        }).catch(err=>showToast('删除异常: '+err,'error'));
}

// ---------- 分页渲染 ----------
function renderDatasetTable(page){
    currentPage = page;
    const tbody = document.getElementById('datasetTableBody');
    tbody.innerHTML = '';

    const startIdx = (page-1)*pageSize;
    const pageData = datasets.slice(startIdx, startIdx+pageSize);

    pageData.forEach(ds => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${ds.name}</td>
            <td>${ds.site}</td>
            <td>${ds.site_name}</td>
            <td>${ds.start_time} - ${ds.end_time}</td>
            <td>${ds.created_at}</td>
            <td>
                <button class="btn detail-btn" onclick="showDetails('${ds.name}','${ds.site}')">详情</button>
                <button class="btn delete-btn" onclick="deleteDataset('${ds.name}')">删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    renderPagination();
}

function renderPagination(){
    const pagination = document.getElementById('datasetPagination');
    pagination.innerHTML = "";
    if(datasets.length === 0) return;

    const countSpan = document.createElement('span');
    countSpan.textContent = `共 ${datasets.length} 条`;
    pagination.appendChild(countSpan);

    const totalPages = Math.ceil(datasets.length/pageSize);
    for(let i=1;i<=totalPages;i++){
        const btn = document.createElement('button');
        btn.textContent = i;
        if(i===currentPage) btn.classList.add('active');
        btn.onclick = ()=> renderDatasetTable(i);
        pagination.appendChild(btn);
    }
}

// ---------- 详情弹框 ----------
function showDetails(file, site){
    fetch(`/tmp_data_preview/${file}/${site}`)
    .then(res=>res.json())
    .then(data=>{
        const modalBg = document.getElementById('modalBg');
        const modalBody = document.getElementById('modalBody');

        if(data.error){
            modalBody.innerHTML = `<h3>${file} - ${site} 数据详情</h3>
                                   <p style="color:red;">${data.error}</p>`;
        } else {
            const rows = data.rows;
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

// ---------- 关闭弹框 ----------
function closeModal(){
    document.getElementById('modalBg').style.display = 'none';
}

// ---------- 初始化 ----------
window.onload = ()=>{
    loadStationList();
};
