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
    setTimeout(()=>{ toast.style.opacity = 0; setTimeout(()=> document.body.removeChild(toast), 500); }, 2500);
}

// ---------- 上传/下载弹框 ----------
function openUploadModal(type) {
    const modalBg = document.getElementById('modalBg');
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <h3>上传 ${type.toUpperCase()} 数据</h3>
        <div class="drag-area" id="dragArea">拖拽文件或点击选择</div>
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

    const stationSelect = document.getElementById('stationSelect');
    const stationId = stationSelect.value || "b91";  
    formData.append('station', stationId);

    const statusId = { pwv: "pwvStatus", weather: "weatherStatus", rain: "rainStatus" }[type];
    const row = document.getElementById(statusId);
    const progress = row.parentElement.querySelector(".progress");
    row.textContent = "上传中...";
    progress.style.width = "30%";

    fetch('/upload_data', { method: 'POST', body: formData })
      .then(res => res.json())
      .then(res => {
          if (res.error) { row.textContent = "上传失败"; showToast("上传失败：" + res.error, 'error'); }
          else {
              row.textContent = "上传完成";
              progress.style.width = "100%";
              showToast("上传完成: " + file.name);
              if(res.start_time && res.end_time){
                  const rangeId = { pwv:"pwvTimeRange", weather:"weatherTimeRange", rain:"rainTimeRange" }[type];
                  document.getElementById(rangeId).innerText = `${res.start_time} - ${res.end_time}`;
              }
          }
          closeModal();
      }).catch(err=>{ row.textContent="上传失败"; progress.style.width="0%"; showToast("上传异常:"+err,'error'); closeModal(); });
}

// ---------- 数据整合 ----------
function integrateData(){
    const stationSelect = document.getElementById('stationSelect');
    const stationId = stationSelect.value || "b91";  
    fetch('/merge_datasets', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({station:stationId}) })
    .then(res=>res.json())
    .then(res=>{
        if(res.error){ showToast("整合失败：" + res.error, 'error'); }
        else{
            const now = new Date();
            const datasetName = res.dataset.split('/').pop();
            datasets.push({
                name: datasetName,
                folder: stationId,
                timeRange: res.time_range || "未知",
                createdAt: now.toLocaleString()
            });
            renderDatasetTable();
            showToast("数据整合完成: " + datasetName);
        }
    }).catch(err=>{ showToast("整合异常: "+err,'error'); });
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
            <td>${ds.folder}</td>
            <td>${ds.timeRange}</td>
            <td>${ds.createdAt}</td>
            <td>
                <button class="btn" onclick="showDetails('${ds.folder}','${ds.name}')">详情</button>
                <button class="btn red" onclick="deleteDataset('${ds.folder}','${ds.name}')">删除</button>
            </td>`;
        tbody.appendChild(tr);
    }
    renderPagination();
}

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

function showDetails(folder, filename){
    fetch(`/tmp_data/${folder}/${filename}`)
    .then(res=>res.json())
    .then(data=>{
        if(!data || data.error){ showToast(data?.error || '返回数据为空','error'); return; }
        const columns = ['date','t2m','sp','rh','pwv','tp'];
        const rows = data.rows || [];
        const html = `<table>
            <thead><tr>${columns.map(c=>`<th>${c}</th>`).join('')}</tr></thead>
            <tbody>${rows.map(r=>`<tr>${columns.map(c=>`<td>${r[c]??''}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
        document.getElementById('modalBody').innerHTML = html;
        document.getElementById('modalBg').style.display='flex';
    }).catch(err=>showToast('详情获取失败: '+err,'error'));
}

function deleteDataset(folder, filename){
    fetch(`/delete_dataset/${folder}/${filename}`,{method:'DELETE'})
    .then(res=>res.json())
    .then(res=>{
        if(res.success){
            const idx = datasets.findIndex(d=>d.name===filename);
            if(idx!==-1) datasets.splice(idx,1);
            renderDatasetTable();
            showToast('删除成功');
        } else showToast('删除失败','error');
    }).catch(err=>showToast('删除异常:'+err,'error'));
}

function closeModal(){ document.getElementById('modalBg').style.display='none'; }
