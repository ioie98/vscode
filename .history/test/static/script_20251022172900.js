const datasets = [];
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

// ---------- 页面初始化，加载已有合并数据 ----------
window.onload = async function() {
    await loadExistingDatasets();
};

// ---------- 加载已有合并数据 ----------
async function loadExistingDatasets() {
    try {
        const res = await fetch('/get_datasets');
        const data = await res.json();
        datasets.length = 0; // 清空旧数据
        data.forEach(site => {
            site.merged.forEach(f => {
                datasets.push({
                    name: f,
                    stationId: site.site_id,
                    stationName: `站点${site.site_id}`,
                    timeRange: site.time_range || '未知',
                    createdAt: site.created_at || '未知'
                });
            });
        });
        renderDatasetTable();
    } catch(e){
        showToast('加载已有数据失败: ' + e, 'error');
    }
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

    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

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
              // 更新时间范围
              if(res.start_time && res.end_time){
                  const rangeId = { pwv:"pwvTimeRange", weather:"weatherTimeRange", rain:"rainTimeRange" }[type];
                  document.getElementById(rangeId).innerText = `${res.start_time} - ${res.end_time}`;
              }
          }
          closeModal();
      }).catch(err=>{
          row.textContent = "上传失败";
          progress.style.width = "0%";
          showToast("上传异常: " + err, 'error');
          closeModal();
      });
}

function openDownloadModal(type){
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
    const stationId = stationSelect.value || "B91";  
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
            // 更新时间范围
            const rangeId = { pwv:"pwvTimeRange", weather:"weatherTimeRange", rain:"rainTimeRange" }[type];
            document.getElementById(rangeId).innerText = `${start} - ${end}`;
        }
        closeModal();
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
            const station = document.getElementById('stationSelect').value || "B91";
            const now = new Date();
            const datasetName = res.dataset.split('/').pop();
            const timeRange = res.time_range || "未知";

            datasets.push({
                name: datasetName,
                stationId: station,
                stationName: `站点${station}`,
                timeRange: timeRange,
                createdAt: now.toLocaleString()
            });
            renderDatasetTable();
            showToast("数据整合完成: " + datasetName);
        }
    })
    .catch(err=>{ showToast("整合异常: "+err, 'error'); });
}

// ---------- 数据集表格 ----------
function renderDatasetTable(){
    const tbody = document.getElementById('datasetTableBody');
    tbody.innerHTML = "";
    const start = (currentPage-1)*pageSize;
    const end = start+pageSize;
    const pageData = datasets.slice(start,end);
    for(const ds of pageData){
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${ds.name}</td>
            <td>${ds.stationId}</td>
            <td>${ds.stationName}</td>
            <td>${ds.timeRange}</td>
            <td>${ds.createdAt}</td>
            <td>
                <button class="btn" onclick="showDetails('${ds.name}')">详情</button>
                <button class="btn red" onclick="deleteDataset('${ds.name}')">删除</button>
            </td>`;
        tbody.appendChild(tr);
    }
    renderPagination();
}

// ---------- 详情 ----------
function showDetails(filename) {
    fetch(`/tmp_data_preview/${filename}`)
        .then(res => res.json())
        .then(data => {
            if (!data || data.error) {
                showToast(data?.error || '返回数据为空', 'error');
                return;
            }
            const rows = data.rows || data.data?.rows || [];
            if (!Array.isArray(rows) || rows.length === 0) {
                showToast('未获取到数据行', 'error');
                return;
            }

            const columns = ['date', 't2m', 'sp', 'rh', 'pwv', 'tp'];
            const mappedRows = rows.map(row => (columns.reduce((obj,c)=>{
                obj[c] = row[c]??'';
                return obj;
            },{})));

            const html = `<table>
                <thead><tr>${columns.map(c=>`<th>${c}</th>`).join('')}</tr></thead>
                <tbody>${mappedRows.map(r=>`<tr>${columns.map(c=>`<td>${r[c]}</td>`).join('')}</tr>`).join('')}</tbody>
            </table>`;
            const modalBody = document.getElementById('modalBody');
            modalBody.innerHTML = html;
            document.getElementById('modalBg').style.display = 'flex';
        }).catch(err=>showToast('详情获取失败: '+err, 'error'));
}

// ---------- 删除 ----------
function deleteDataset(filename){
    fetch(`/delete_dataset/${filename}`, { method:'DELETE' })
        .then(res=>res.json())
        .then(res=>{
            if(res.success){
                const idx = datasets.findIndex(d=>d.name===filename);
                if(idx!==-1) datasets.splice(idx,1);
                renderDatasetTable();
                showToast('删除成功');
            }else showToast('删除失败', 'error');
        }).catch(err=>showToast('删除异常: '+err,'error'));
}

// ---------- 分页 ----------
function renderPagination(){
    const container = document.getElementById('datasetPagination');
    container.innerHTML = "";
    const totalPages = Math.ceil(datasets.length/pageSize);
    for(let i=1;i<=totalPages;i++){
        const btn = document.createElement('button');
        btn.textContent = i;
        if(i===currentPage) btn.classList.add('active');
        btn.onclick = ()=>{ currentPage=i; renderDatasetTable(); };
        container.appendChild(btn);
    }
}

// ---------- 关闭弹框 ----------
function closeModal(){
    document.getElementById('modalBg').style.display='none';
}
