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
            opt.textContent = site.site_id; // 不加“站点”前缀
            select.appendChild(opt);
        }
        // 自动选第一个站点并加载
        if(data.length>0){
            select.value = data[0].site_id;
            loadSiteDatasets();
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
    datasets = [];

    fetch('/get_datasets')
        .then(res => res.json())
        .then(allData => {
            const site = allData.find(s => s.site_id === siteId);
            if (!site) return;

            // 所有合并文件
            site.merged.forEach(file => {
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
                        datasets.push({file, site_id: site.site_id, timeRange, created: now.toLocaleString()});
                        renderPagination(); // 每次异步添加时刷新分页
                    });
            });
        });
}

// ---------- 删除 ----------
function deleteDataset(filename, site){
    fetch(`/delete_dataset/${filename}/${site}`, { method:'DELETE' })
        .then(res=>res.json())
        .then(res=>{
            if(res.status==='success'){
                showToast('删除成功');
                loadSiteDatasets();
            }else showToast('删除失败: '+(res.message||''),'error');
        }).catch(err=>showToast('删除异常: '+err,'error'));
}

// ---------- 分页显示 ----------
function renderDatasetTable(page=1){
    currentPage = page;
    const tbody = document.getElementById('datasetTableBody');
    tbody.innerHTML = "";
    if(datasets.length===0) return;

    const start = (currentPage-1)*pageSize;
    const end = Math.min(start + pageSize, datasets.length);
    for(let i=start;i<end;i++){
        const d = datasets[i];
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${d.file}</td>
            <td>${d.site_id}</td>
            <td>${d.site_id}</td>
            <td>${d.timeRange}</td>
            <td>${d.created}</td>
            <td>
                <button class="btn" onclick="showDetails('${d.file}','${d.site_id}')">详情</button>
                <button class="btn red" onclick="deleteDataset('${d.file}','${d.site_id}')">删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    }

    renderPagination();
}

function renderPagination() {
    const pagination = document.getElementById('datasetPagination');
    pagination.innerHTML = "";

    if(datasets.length===0) return;

    // 显示总条数
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
        modalBody.innerHTML = `<h3>${file} - ${site} 数据详情</h3>
            <pre>${JSON.stringify(data.rows.slice(0,50), null, 2)}</pre>`;
        modalBg.style.display = 'flex';
    });
}

// ---------- 关闭弹框 ----------
function closeModal(){
    document.getElementById('modalBg').style.display = 'none';
}

// ---------- 初始化 ----------
window.onload = ()=>{
    loadStationList();
};
