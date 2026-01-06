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

// ---------- 上传/下载弹框 ----------
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
          loadSiteDatasets(); // 上传完成刷新当前站点已有数据
      }).catch(err=>{
          row.textContent = "上传失败";
          progress.style.width = "0%";
          showToast("上传异常: " + err, 'error');
          closeModal();
      });
}

function openDownloadModal(type){
    const stationSelect = document.getElementById('stationSelect');
    const stationId = stationSelect.value;
    if(!stationId){ showToast('请先选择站点','error'); return; }

    const modalBg = document.getElementById('modalBg');
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `<h3>下载 ${type.toUpperCase()} 数据</h3>
        <label>起始时间: </label><input type="datetime-local" id="startTime"><br><br>
        <label>结束时间: </label><input type="datetime-local" id="endTime"><br><br>
        <button class="btn" onclick="startDownload('${type}')">开始下载</button>
        <div id="downloadResult" style="margin-top:10px;"></div>`;
    modalBg.style.display = 'flex';
}

function startDownload(type){
    const start = document.getElementById('startTime').value;
    const end = document.getElementById('endTime').value;
    const stationSelect = document.getElementById('stationSelect');
    const stationId = stationSelect.value;
    if(!stationId){ showToast('请先选择站点','error'); return; }

    const statusId = { pwv: "pwvStatus", weather: "weatherStatus", rain: "rainStatus" }[type];
    const statusEl = document.getElementById(statusId);
    statusEl.textContent = "下载中...";
    const progress = statusEl.parentElement.querySelector(".progress");
    progress.style.width = "30%";

    fetch('/download_data', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ type, start_time: start, end_time: end, device: stationId })
    })
    .then(res=>res.json())
    .then(res=>{
        if(res.error){
            statusEl.textContent = "下载失败";
            progress.style.width = "0%";
            showToast("下载失败: "+res.error, 'error');
        }else{
            statusEl.textContent = "下载完成";
            progress.style.width = "100%";
            showToast(`下载完成，共 ${res.count} 条数据`);
            const rangeId = { pwv:"pwvTimeRange", weather:"weatherTimeRange", rain:"rainTimeRange" }[type];
            document.getElementById(rangeId).innerText = `${start} - ${end}`;
        }
        closeModal();
        loadSiteDatasets(); // 下载完成刷新当前站点已有数据
    })
    .catch(err=>{
        statusEl.textContent = "下载失败";
        progress.style.width = "0%";
        showToast("下载异常: "+err, 'error');
        closeModal();
    });
}

// ---------- 数据整合 ----------
function integrateData(){
    fetch('/merge_datasets', { method:'POST' })
    .then(res=>res.json())
    .then(res=>{
        if(res.error){
            showToast("整合失败：" + res.error, 'error');
        }else{
            showToast("数据整合完成");
            loadSiteDatasets();
        }
    })
    .catch(err=>{ showToast("整合异常: "+err, 'error'); });
}

// ---------- 加载站点列表 ----------
function loadStationList(){
    fetch('/get_datasets')
    .then(res=>res.json())
    .then(data=>{
        const select = document.getElementById('stationSelect');
        select.innerHTML = `<option value="">--请选择站点--</option>`;
        for(const site of data){
            const opt = document.createElement('option');
            opt.value = site.site_id;
            opt.textContent = site.site_id; // 显示 b72 / b99 / b100
            select.appendChild(opt);
        }
    });
}

// ---------- 加载当前选择站点的已有数据 ----------
function loadSiteDatasets() {
    const stationSelect = document.getElementById('stationSelect');
    const siteId = stationSelect.value;
    if (!siteId) return;

    const tbody = document.getElementById('datasetTableBody');
    tbody.innerHTML = ""; // 清空表格

    fetch('/get_datasets')
        .then(res => res.json())
        .then(allData => {
            const site = allData.find(s => s.site_id === siteId);
            if (!site || !site.merged.length) return;

            // 按文件名时间排序，显示最新合并文件
            const sortedMerged = site.merged.sort().reverse();

            sortedMerged.forEach(file => {
                fetch(`/tmp_data_preview/${file}/${site.site_id}`)
                    .then(res => res.json())
                    .then(data => {
                        let timeRange = "未知";
                        if(data.rows && data.rows.length>0){
                            const dates = data.rows.map(r=>new Date(r.date)).filter(d=>!isNaN(d));
                            if(dates.length>0){
                                const minDate = new Date(Math.min(...dates));
                                const maxDate = new Date(Math.max(...dates));
                                timeRange = `${minDate.getFullYear()}/${(minDate.getMonth()+1).toString().padStart(2,'0')}/${minDate.getDate().toString().padStart(2,'0')} ${minDate.getHours().toString().padStart(2,'0')}:${minDate.getMinutes().toString().padStart(2,'0')}:${minDate.getSeconds().toString().padStart(2,'0')} ~ ` +
                                            `${maxDate.getFullYear()}/${(maxDate.getMonth()+1).toString().padStart(2,'0')}/${maxDate.getDate().toString().padStart(2,'0')} ${maxDate.getHours().toString().padStart(2,'0')}:${maxDate.getMinutes().toString().padStart(2,'0')}:${maxDate.getSeconds().toString().padStart(2,'0')}`;
                            }
                        }

                        const now = new Date();
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                          <td>${file}</td>
                          <td>${site.site_id}</td>
                          <td>${site.site_id}</td>
                          <td>${timeRange}</td>
                          <td>${now.toLocaleString()}</td>
                          <td>
                              <button class="btn" onclick="showDetails('${file}', '${site.site_id}')">详情</button>
                              <button class="btn red" onclick="deleteDataset('${file}', '${site.site_id}')">删除</button>
                          </td>
                        `;
                        tbody.appendChild(tr);
                    });
            });
        });
}


// ---------- 详情 ----------
function showDetails(filename, site) {
    fetch(`/tmp_data_preview/${filename}/${site}`)
        .then(res => res.json())
        .then(data => {
            if (!data || data.error) {
                showToast(data?.error || '返回数据为空', 'error');
                return;
            }
            const rows = data.rows || [];
            const columns = ['date', 't2m', 'sp', 'rh', 'pwv', 'tp'];
            const html = `<table>
                <thead><tr>${columns.map(c=>`<th>${c}</th>`).join('')}</tr></thead>
                <tbody>${rows.map(r=>`<tr>${columns.map(c=>`<td>${r[c]??''}</td>`).join('')}</tr>`).join('')}</tbody>
            </table>`;
            const modalBody = document.getElementById('modalBody');
            modalBody.innerHTML = html;
            document.getElementById('modalBg').style.display = 'flex';
        }).catch(err=>showToast('详情获取失败: '+err, 'error'));
}

// ---------- 删除 ----------
function deleteDataset(filename, site){
    fetch(`/delete_dataset/${filename}/${site}`, { method:'DELETE' })
        .then(res=>res.json())
        .then(res=>{
            if(res.status==='success'){
                showToast('删除成功');
                loadSiteDatasets(); // 删除后刷新表格
            } else {
                showToast('删除失败: ' + (res.message || ''), 'error');
            }
        })
        .catch(err=>{
            showToast('删除异常: ' + err, 'error');
        });
}



// ---------- 关闭弹框 ----------
function closeModal(){
    document.getElementById('modalBg').style.display='none';
}

// ---------- 初始化 ----------
window.onload = () => {
    loadStationList();

    const stationSelect = document.getElementById('stationSelect');
    stationSelect.onchange = () => {
        loadSiteDatasets(); // 切换站点时自动加载已有合并数据
    };
};


