let datasets = [];
let currentPage = 1;
const pageSize = 5;

document.addEventListener('DOMContentLoaded', () => loadSiteDatasets());

function loadSiteDatasets() {
    const site = document.getElementById('stationSelect').value;
    if(!site) return;
    fetch(`/get_datasets/${site}`)
    .then(res => res.json())
    .then(res => {
        datasets = res.datasets || [];
        currentPage = 1;
        renderDatasetTable();
    });
}

function renderDatasetTable() {
    const tbody = document.getElementById('datasetTableBody');
    tbody.innerHTML = '';
    if(datasets.length === 0) return;

    const start = (currentPage - 1) * pageSize;
    const pageData = datasets.slice(start, start + pageSize);

    pageData.forEach(file => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${file.name}</td>
            <td>${file.station}</td>
            <td>站点${file.station}</td>
            <td>${file.time_range}</td>
            <td>${file.create_time}</td>
            <td>
                <button class="btn red" onclick="deleteDataset('${file.name}','${file.station}')">删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    // 更新计数
    document.getElementById('datasetCount').textContent = `共 ${datasets.length} 条`;

    // 分页
    const pageCount = Math.ceil(datasets.length / pageSize);
    const pagination = document.getElementById('datasetPagination');
    pagination.innerHTML = '';
    for(let i=1;i<=pageCount;i++){
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = (i===currentPage)?'active':'';
        btn.onclick = () => { currentPage=i; renderDatasetTable(); };
        pagination.appendChild(btn);
    }
}

function deleteDataset(filename, site){
    fetch(`/delete_dataset/${filename}/${site}`, {method:'DELETE'})
    .then(res => res.json())
    .then(res => {
        showToast(res.status==='success'?'删除成功':'删除失败: '+res.message);
        if(res.status==='success') loadSiteDatasets();
    })
    .catch(err => showToast('删除异常: '+err,'error'));
}

function showToast(msg,type='success'){
    const div = document.createElement('div');
    div.className = 'toast-message';
    if(type==='error') div.style.background='#dc3545';
    div.textContent = msg;
    document.body.appendChild(div);
    setTimeout(()=>{ div.style.opacity=1; },10);
    setTimeout(()=>{ div.style.opacity=0; setTimeout(()=>div.remove(),500); },2000);
}

// 下载弹框
function openDownloadModal() {
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div class="modal-body-section">
            <label>选择时间范围：</label>
            <input id="downloadStart" placeholder="开始时间">
            <input id="downloadEnd" placeholder="结束时间">
        </div>
        <div class="modal-body-section">
            <label>排序方式：</label>
            <select id="sortType">
                <option value="default">默认排序</option>
                <option value="manual">手动排序</option>
            </select>
        </div>
        <div class="modal-body-section" id="manualSortContainer" style="display:none;">
            <label>PWV 优先级排序：</label>
            <ul id="pwvSort" class="sortable-list">
                <li>deviced</li><li>ec</li><li>era5</li><li>cros</li>
            </ul>
            <label>HWS 优先级排序：</label>
            <ul id="hwsSort" class="sortable-list">
                <li>deviced</li><li>ec</li><li>era5</li><li>cros</li>
            </ul>
            <label>RAIN 优先级排序：</label>
            <ul id="rainSort" class="sortable-list">
                <li>deviced</li><li>ec</li><li>era5</li><li>cros</li>
            </ul>
        </div>
        <div class="modal-body-section">
            <button class="btn" onclick="downloadMergeData()">下载并合并</button>
        </div>
    `;
    flatpickr('#downloadStart', {enableTime:true,dateFormat:"Y/m/d H:i"});
    flatpickr('#downloadEnd', {enableTime:true,dateFormat:"Y/m/d H:i"});

    const sortType = modalBody.querySelector('#sortType');
    sortType.onchange = e=>{
        document.getElementById('manualSortContainer').style.display = (e.target.value==='manual')?'block':'none';
    };

    ['pwvSort','hwsSort','rainSort'].forEach(id=>{
        new Sortable(document.getElementById(id), {animation:150});
    });

    document.getElementById('modalBg').style.display='flex';
}

function closeModal(){
    document.getElementById('modalBg').style.display='none';
}

// 下载并合并逻辑
function downloadMergeData() {
    const site = document.getElementById('stationSelect').value;
    if(!site){ showToast('请选择站点','error'); return; }
    const start = document.getElementById('downloadStart').value;
    const end = document.getElementById('downloadEnd').value;
    const sortType = document.getElementById('sortType').value;

    let pwvSort=[], hwsSort=[], rainSort=[];
    if(sortType==='manual'){
        pwvSort = Array.from(document.getElementById('pwvSort').children).map(li=>li.textContent);
        hwsSort = Array.from(document.getElementById('hwsSort').children).map(li=>li.textContent);
        rainSort = Array.from(document.getElementById('rainSort').children).map(li=>li.textContent);
    }

    fetch('/download_merge/'+site,{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({start,end,sortType,pwvSort,hwsSort,rainSort})
    })
    .then(res=>res.blob())
    .then(blob=>{
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(blob);
        a.download = `dataset_${site}_${Date.now()}.csv`;
        a.click();
        closeModal();
        showToast('下载并合并完成');
        loadSiteDatasets();
    })
    .catch(err=>showToast('下载异常: '+err,'error'));
}
