let datasets = [];
let currentPage = 1;
const pageSize = 5;

// 站点队列
let stations = [];

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

// 添加站点
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
    if(e.key === 'Enter'){ e.preventDefault(); addStationFromInput(); }
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
    if(input) input.value = stations.length>0 ? stations[0] : '';
    loadSiteDatasets();
}

// 清空站点列表
function clearStationList(){
    stations = [];
    renderStationTags();
    const input = document.getElementById('stationSelect');
    if(input) input.value = '';
    datasets = [];
    currentPage = 1;
    renderDatasetTable(1);
    showToast('站点列表已清空');
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
        e.preventDefault(); dragArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        document.getElementById('fileInfo').innerText = `文件名: ${file.name}, 大小: ${file.size} bytes`;
    });
    fileInput.onchange = e => {
        const file = e.target.files[0];
        document.getElementById('fileInfo').innerText = `文件名: ${file.name}, 大小: ${file.size} bytes`;
    };
    modalBg.style.display = 'flex';
}

// 开始上传
function startUpload(type) {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    if (!file) { showToast('请选择文件', 'error'); return; }
    const stationId = document.getElementById('stationSelect')?.value;
    if(!stationId){ showToast('请先选择站点','error'); return; }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);
    formData.append('device', stationId);

    fetch('/upload_data', { method: 'POST', body: formData })
      .then(res => res.json())
      .then(res => {
          if(res.error){ showToast("上传失败：" + res.error,'error'); }
          else{
              showToast("上传完成: " + file.name);
              const rangeId = { pwv:"pwvTimeRange", weather:"weatherTimeRange", rain:"rainTimeRange" }[type];
              if(rangeId && res.start_time && res.end_time)
                  document.getElementById(rangeId).innerText = `${res.start_time} - ${res.end_time}`;
              loadSiteDatasets();
          }
          closeModal();
      })
      .catch(err=>{ showToast("上传异常: " + err,'error'); closeModal(); });
}

// 下载弹框（批量）
function openUnifiedDownloadModal(){
    const modalBg = document.getElementById('modalBg');
    const modalBody = document.getElementById('modalBody');
    const defaultPriority = ['deviced','cros','ec','era5'];

    modalBody.innerHTML = `
        <h3>下载数据（批量）</h3>
        <label>起始时间: </label><input type="datetime-local" id="unifiedStart"><br><br>
        <label>结束时间: </label><input type="datetime-local" id="unifiedEnd"><br><br>
        <div class="download-mode">
            <label><input type="radio" name="downloadMode" value="train" checked> train</label>
            <label><input type="radio" name="downloadMode" value="pred"> pred</label>
        </div>
        <div>
            <label><input type="checkbox" id="chk_pw" checked> PWV</label>
            <label><input type="checkbox" id="chk_hw" checked> 气象(HWS)</label>
            <label><input type="checkbox" id="chk_rn" checked> 雨量(Rain)</label>
        </div>
        <div style="margin-top:12px;">
            <div style="font-weight:600;margin-bottom:6px;">数据源优先级（上→下：高优先→低优先）</div>
            <div id="unifiedPriorityList" class="priority-list"></div>
        </div>
        <div style="margin-top:12px; text-align:right;">
            <button class="btn" onclick="startUnifiedDownload()">确认下载</button>
        </div>
    `;
    const pList = document.getElementById('unifiedPriorityList');
    defaultPriority.forEach(p=>{
        const div = document.createElement('div');
        div.className='priority-item';
        div.dataset.source=p;
        div.style='display:flex; align-items:center; gap:8px; margin-bottom:6px;';
        div.innerHTML = `<span style="flex:1;">${p}</span>
                         <button class="btn small" onclick="movePriority(this,-1)">↑</button>
                         <button class="btn small" onclick="movePriority(this,1)">↓</button>`;
        pList.appendChild(div);
    });
    modalBg.style.display = 'flex';
}

// 调整优先级
function movePriority(btn, dir){
    const item = btn.closest('.priority-item');
    const list = btn.closest('.priority-list');
    if(!item||!list) return;
    if(dir===-1 && item.previousElementSibling) list.insertBefore(item, item.previousElementSibling);
    if(dir===1 && item.nextElementSibling) list.insertBefore(item.nextElementSibling, item);
}

// 批量下载
function startUnifiedDownload() {
    let devices = Array.from(stations);
    const inputVal = (document.getElementById('stationSelect')?.value || '').trim();
    if(devices.length===0 && inputVal) devices=[inputVal];
    if(devices.length===0){ showToast('请添加或选择至少一个站点','error'); return; }

    const start = document.getElementById('unifiedStart')?.value;
    const end = document.getElementById('unifiedEnd')?.value;
    if(!start || !end){ showToast('请选择起始与结束时间','error'); return; }

    const types = [];
    if(document.getElementById('chk_pw').checked) types.push('pwv');
    if(document.getElementById('chk_hw').checked) types.push('weather');
    if(document.getElementById('chk_rn').checked) types.push('rain');
    if(types.length===0){ showToast('请选择至少一种数据类型','error'); return; }

    const modeEl = document.querySelector('input[name="downloadMode"]:checked');
    const mode = modeEl ? modeEl.value : 'train';

    const priorityOrder = Array.from(document.querySelectorAll('#unifiedPriorityList .priority-item')).map(e=>e.dataset.source);

    closeModal();
    showToast('开始批量下载任务...');

    fetch('/batch_download',{
        method:'POST',
        headers:{ 'Content-Type':'application/json' },
        body: JSON.stringify({ types, start_time:start, end_time:end, devices, priority:priorityOrder, mode })
    }).then(res=>res.json())
      .then(res=>{
          if(res.error){ showToast('批量下载失败: '+res.error,'error'); return; }

          if(res.merged && Array.isArray(res.merged.results)){
              res.merged.results.forEach(m=>{
                  const rec = {
                      file: m.dataset,
                      site: m.site_id,
                      site_name: m.site_name || m.site_id,
                      sub_dir: m.sub_dir || '',
                      start_time: m.time_range?.split('~')[0]?.trim() || '',
                      end_time: m.time_range?.split('~')[1]?.trim() || '',
                      created_at: new Date().toLocaleString(),
                      path: m.dataset
                  };
                  if(!datasets.some(d=>d.path===rec.path && d.site===rec.site)) datasets.push(rec);
              });
              datasets.sort((a,b)=> new Date(b.created_at)-new Date(a.created_at));
              renderDatasetTable(1);
              showToast('整合完成');
          }
      }).catch(err=>{ showToast('批量下载异常: '+err,'error'); });
}

// 渲染表格
function renderDatasetTable(page){
    currentPage=page;
    const tbody=document.getElementById('datasetTableBody');
    tbody.innerHTML='';
    const startIdx=(page-1)*pageSize;
    const pageData=datasets.slice(startIdx,startIdx+pageSize);
    if(pageData.length===0){
        tbody.innerHTML=`<tr><td colspan="6" style="text-align:center;">暂无数据</td></tr>`;
        return;
    }
    pageData.forEach(ds=>{
        const file=ds.file||'';
        const siteId=ds.site||'未知站点';
        const siteName=ds.site_name||('站点'+siteId);
        const startTime=ds.start_time||'';
        const endTime=ds.end_time||'';
        const createdAt=ds.created_at||'';
        const subDir=ds.sub_dir||'train';
        const filePath=[subDir||'', ds.file].filter(Boolean).join('/');
        const tr=document.createElement('tr');
        tr.innerHTML=`
            <td>${file}</td>
            <td>${siteId}</td>
            <td>${siteName}</td>
            <td>${startTime} ~ ${endTime}</td>
            <td>${createdAt}</td>
            <td>
                <button class="btn detail-btn" onclick="showDetails('${siteId}','${subDir}','${file}')">详情</button>
                <button class="btn delete-btn" onclick="deleteDataset('${encodeURIComponent(filePath)}','${siteId}')">删除</button>
            </td>`;
        tbody.appendChild(tr);
    });
    const datasetCount=document.getElementById('datasetCount');
    if(datasetCount) datasetCount.innerText=`共 ${datasets.length} 条`;
    renderPagination();
}

// 分页
function renderPagination(){
    const pagination=document.getElementById('datasetPagination');
    if(!pagination) return;
    pagination.innerHTML='';
    if(datasets.length===0) return;
    const countSpan=document.createElement('span');
    countSpan.textContent=`共 ${datasets.length} 条`;
    pagination.appendChild(countSpan);
    const totalPages=Math.ceil(datasets.length/pageSize);
    for(let i=1;i<=totalPages;i++){
        const btn=document.createElement('button');
        btn.textContent=i;
        if(i===currentPage) btn.classList.add('active');
        btn.onclick=()=> renderDatasetTable(i);
        pagination.appendChild(btn);
    }
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
            datasets=datasets.filter(d=>[d.sub_dir||'',d.file].filter(Boolean).join('/')!==decodeURIComponent(filename) || d.site!==siteVal);
            renderDatasetTable(currentPage);
        }else showToast('删除失败: '+(res.message||''),'error');
    }).catch(err=>showToast('删除异常: '+err,'error'));
}

// 详情
function showDetails(site, mode, file){
    const modalBg = document.getElementById('modalBg');
    const modalBody = document.getElementById('modalBody');
    fetch(`/get_file_rows?site=${encodeURIComponent(site)}&mode=${encodeURIComponent(mode)}&file=${encodeURIComponent(file)}`)
    .then(res=>res.json())
    .then(data=>{
        if(data.error){
            modalBody.innerHTML=`<h3>${file} - ${site} 数据详情</h3><p style="color:red;">${data.error}</p>`;
        }else{
            const rows=data.rows||[];
            let tableHTML=`<h3>${file} - ${site} 数据详情</h3><div style="max-height:400px; overflow:auto;"><table>
            <thead><tr><th>date</th><th>t2m</th><th>sp</th><th>rh</th><th>pwv</th><th>tp</th></tr></thead><tbody>`;
            rows.forEach(r=>{
                tableHTML+=`<tr><td>${r.date||''}</td><td>${r.t2m!==null?r.t2m:''}</td><td>${r.sp!==null?r.sp:''}</td>
                            <td>${r.rh!==null?r.rh:''}</td><td>${r.pwv!==null?r.pwv:''}</td><td>${r.tp!==null?r.tp:''}</td></tr>`;
            });
            tableHTML+='</tbody></table></div>';
            modalBody.innerHTML=tableHTML;
        }
        modalBg.style.display='flex';
    }).catch(err=>{ showToast('获取详情失败: '+err,'error'); });
}

// 关闭弹框
function closeModal(){ document.getElementById('modalBg').style.display='none'; }

// 加载站点列表
function loadStationList(){
    fetch('/get_datasets')
    .then(res=>res.json())
    .then(data=>{
        const dataList=document.getElementById('stationList');
        const input=document.getElementById('stationSelect');
        if(!dataList||!input) return;
        dataList.innerHTML='';
        data.forEach(site=>{
            const opt=document.createElement('option');
            opt.value=site.site_id;
            dataList.appendChild(opt);
        });
        if(stations.length===0 && data.length>0){
            stations.push(data[0].site_id);
            renderStationTags();
        }
        if(data.length>0) input.value=stations[0]||data[0].site_id;
        loadSiteDatasets();
    }).catch(err=>console.error('加载站点列表失败',err));
}

// 初始化
window.onload = ()=>{
    loadStationList();
    renderStationTags();
    const inp = document.getElementById('stationSelect');
    if(inp) inp.addEventListener('keydown', onStationInputKeydown);
};
