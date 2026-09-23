const API='/api/admin';
const state={token:sessionStorage.getItem('ufhAdminToken'),admin:JSON.parse(sessionStorage.getItem('ufhAdmin')||'null'),emergencies:[],incidents:[],officerWorkloads: [],officers:[],users:[],campuses:[]};
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const escapeHtml=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const fmt=d=>d?new Date(d).toLocaleString('en-ZA',{dateStyle:'medium',timeStyle:'short'}):'—';
const pill=v=>`<span class="status ${String(v||'').toLowerCase()}">${escapeHtml(String(v||'—').replaceAll('_',' '))}</span>`;
async function request(path,options={}){const headers={...(options.headers||{})};if(state.token)headers.Authorization=`Bearer ${state.token}`;const r=await fetch(API+path,{...options,headers});const text=await r.text();let data;try{data=JSON.parse(text)}catch{data=text}if(!r.ok)throw new Error(data?.message||data||`Request failed (${r.status})`);return data}
function message(el,text,ok=false){el.textContent=text;el.style.color=ok?'#137b57':'#d92d3f'}
$('#detailsForm').addEventListener('submit',async e=>{e.preventDefault();const employeeNumber=$('#employeeNumber').value.trim(),universityEmail=$('#universityEmail').value.trim();message($('#loginMessage'),'Sending code…',true);try{const result=await request(`/send-code?employeeNumber=${encodeURIComponent(employeeNumber)}&universityEmail=${encodeURIComponent(universityEmail)}`,{method:'POST'});sessionStorage.setItem('pendingAdminEmployee',employeeNumber);$('#detailsForm').classList.add('hidden');$('#codeForm').classList.remove('hidden');$('#verificationCode').focus();const developmentCode=result.verificationCode?` Development code: ${result.verificationCode}`:'';message($('#codeMessage'),'Verification code created.'+developmentCode,true)}catch(err){message($('#loginMessage'),err.message)}});
$('#codeForm').addEventListener('submit',async e=>{e.preventDefault();const employeeNumber=sessionStorage.getItem('pendingAdminEmployee'),code=$('#verificationCode').value.trim();message($('#codeMessage'),'Verifying…',true);try{const data=await request(`/confirm-code?employeeNumber=${encodeURIComponent(employeeNumber)}&code=${encodeURIComponent(code)}`,{method:'POST'});state.token=data.token;state.admin=data.administrator;sessionStorage.setItem('ufhAdminToken',state.token);sessionStorage.setItem('ufhAdmin',JSON.stringify(state.admin));showDashboard()}catch(err){message($('#codeMessage'),err.message)}});
$('#backToDetails').onclick=()=>{$('#codeForm').classList.add('hidden');$('#detailsForm').classList.remove('hidden')};
async function showDashboard(){if(!state.token)return;$('#loginPage').classList.add('hidden');$('#dashboardPage').classList.remove('hidden');const a=state.admin||{},name=`${a.firstName||''} ${a.lastName||''}`.trim()||'Administrator';$('#adminName').textContent=name;$('#adminCampus').textContent=a.campus?.campusName||'University of Fort Hare';$('#adminInitials').textContent=(a.firstName?.[0]||'A')+(a.lastName?.[0]||'D');$('#welcomeName').textContent=`Good day, ${a.firstName||'Administrator'}`;$('#todayLabel').textContent=new Date().toLocaleDateString('en-ZA',{weekday:'long',day:'numeric',month:'long',year:'numeric'});await loadAll()}
async function loadAll() {

    setGlobal("");

    try {

        const [
            stats,
            users,
            officers,
            officerWorkloads,
            emergencies,
            incidents,
            campuses
        ] = await Promise.all([
            request("/dashboard"),
            request("/users"),
            request("/officers"),
            request("/officers/workloads"),
            request("/emergencies"),
            request("/incidents"),
            request("/campuses")
        ]);

        Object.assign(state, {
            users,
            officers,
            officerWorkloads,
            emergencies,
            incidents,
            campuses
        });

        $("#statUsers").textContent =
            stats.users;

        $("#statOfficers").textContent =
            stats.officers;

        $("#statEmergencies").textContent =
            stats.activeEmergencies;

        $("#statIncidents").textContent =
            stats.openIncidents;

        $("#emergencyBadge").textContent =
            stats.activeEmergencies;

        renderAll();

    } catch (error) {

        if (/session|forbidden|401|403/i.test(
            error.message)) {

            logout();
            return;
        }

        setGlobal(error.message);
    }
}
function renderAll(){renderEmergencies();renderIncidents();renderOfficers();renderUsers();renderCampuses();const recent=state.emergencies.slice().sort((a,b)=>new Date(b.createdAt)-new Date(a.createdAt)).slice(0,5);$('#recentEmergencies').innerHTML=recent.length?recent.map(e=>`<div class="activity-item"><i class="activity-dot"></i><div><b>${escapeHtml(e.user?.firstName)} ${escapeHtml(e.user?.lastName)}</b><small>${escapeHtml(e.emergencyType||'Emergency alert')} · ${fmt(e.createdAt)}</small></div>${pill(e.alertStatus)}</div>`).join(''):'<div class="activity-item"><div><b>No emergencies recorded</b><small>New alerts will appear here.</small></div></div>'}
function renderEmergencies(){const filter=$('#emergencyFilter').value;const rows=state.emergencies.filter(e=>!filter||e.alertStatus===filter);$('#emergencyTable tbody').innerHTML=rows.map(e=>`<tr><td>#${e.emergencyId}</td><td><b>${escapeHtml(e.user?.firstName)} ${escapeHtml(e.user?.lastName)}</b><small>${escapeHtml(e.user?.studentStaffNumber)}</small></td><td>${escapeHtml(e.user?.phoneNumber||'—')}</td><td>${e.location?escapeHtml(e.location.locationName||e.location.name):`GPS: ${Number(e.latitude||0).toFixed(5)}, ${Number(e.longitude||0).toFixed(5)}`}</td><td>${pill(e.alertStatus)}</td><td>${fmt(e.createdAt)}</td></tr>`).join('')||emptyRow(6,'No emergency alerts found.')}
function renderIncidents(){$('#incidentTable tbody').innerHTML=state.incidents.map(i=>`<tr><td>#${i.incidentId}</td><td><b>${escapeHtml(i.incidentType)}</b><small>${escapeHtml(i.description).slice(0,55)}</small></td><td>${escapeHtml(i.user?.firstName)} ${escapeHtml(i.user?.lastName)}</td><td>${escapeHtml(i.location?.locationName||i.location?.name||'—')}</td><td>${pill(i.severity)}</td><td>${pill(i.incidentStatus)}</td><td>${fmt(i.reportedAt)}</td></tr>`).join('')||emptyRow(7,'No incident reports found.')}
function renderOfficers() {

    const officers = state.officerWorkloads;

    $("#officerCards").innerHTML =
        officers.map(officer => {

            const activeCases =
                officer.activeCases || [];

            const casePreview =
                activeCases.slice(0, 2)
                    .map(caseItem => `
                        <div class="case-preview">

                            <span>
                                ${escapeHtml(caseItem.caseType)}
                                #${caseItem.caseId}
                            </span>

                            <b>
                                ${escapeHtml(
                        caseItem.title || "Case"
                    )}
                            </b>

                            <small>
                                ${escapeHtml(
                        caseItem.location ||
                        "Location unavailable"
                    )}

                                ·

                                ${escapeHtml(
                        String(
                            caseItem.status || ""
                        ).replaceAll("_", " ")
                    )}
                            </small>

                        </div>
                    `)
                    .join("");

            return `
                <article class="officer-card">

                    <div class="officer-top">

                        <div class="officer-avatar">
                            ${escapeHtml(
                officer.firstName?.[0] || "S"
            )}
                            ${escapeHtml(
                officer.lastName?.[0] || "O"
            )}
                        </div>

                        <div>
                            <h3>
                                ${escapeHtml(officer.firstName)}
                                ${escapeHtml(officer.lastName)}
                            </h3>

                            <small>
                                ${escapeHtml(
                officer.employeeNumber
            )}
                            </small>
                        </div>

                    </div>

                    <div class="meta">

                        <span>
                            Campus:
                            <b>
                                ${escapeHtml(
                officer.campusName || "—"
            )}
                            </b>
                        </span>

                        <span>
                            Phone:
                            <b>
                                ${escapeHtml(
                officer.phoneNumber ||
                "Not supplied"
            )}
                            </b>
                        </span>

                    </div>

                    <div class="officer-status-row">

                        ${pill(officer.availabilityStatus)}

                        <span class="workload-count">

                            ${officer.activeCaseCount || 0}
                            active

                            ${
                officer.activeCaseCount === 1
                    ? "case"
                    : "cases"
            }

                        </span>

                    </div>

                    <div class="case-preview-list">

                        ${
                casePreview ||
                `<p class="no-workload">
                                Not currently handling a case.
                            </p>`
            }

                    </div>

                    <button
                        class="secondary view-workload"
                        data-officer-id="${officer.officerId}">

                        View cases

                    </button>

                </article>
            `;
        })
            .join("");

    if (officers.length === 0) {

        $("#officerCards").innerHTML = `
            <div class="panel" style="padding:25px">
                No security officers registered.
            </div>
        `;
    }

    $$(".view-workload").forEach(button => {

        button.onclick = () => {

            showOfficerWorkload(
                Number(button.dataset.officerId)
            );
        };
    });
}
function showOfficerWorkload(officerId) {

    const officer =
        state.officerWorkloads.find(
            item => item.officerId === officerId
        );

    if (!officer) {
        return;
    }

    $("#workloadOfficerName").textContent =
        `${officer.firstName} ${officer.lastName}`;

    $("#workloadOfficerDetails").textContent =
        `${officer.employeeNumber} · `
        + `${officer.campusName} · `
        + `${officer.activeCaseCount} active `
        + `${officer.activeCaseCount === 1
            ? "case"
            : "cases"}`;

    const cases = officer.activeCases || [];

    $("#workloadCaseList").innerHTML =
        cases.length
            ? cases.map(caseItem => `
                <article class="workload-case">

                    <div class="workload-case-head">

                        <div>
                            <span class="case-kind">
                                ${escapeHtml(caseItem.caseType)}
                            </span>

                            <h3>
                                #${caseItem.caseId}
                                ${escapeHtml(
                caseItem.title || "Case"
            )}
                            </h3>
                        </div>

                        ${pill(caseItem.status)}

                    </div>

                    <dl>

                        <div>
                            <dt>Location</dt>
                            <dd>
                                ${escapeHtml(
                caseItem.location || "—"
            )}
                            </dd>
                        </div>

                        <div>
                            <dt>Reporter</dt>
                            <dd>
                                ${escapeHtml(
                caseItem.reporterName || "—"
            )}

                                <small>
                                    ${escapeHtml(
                caseItem.reporterNumber || ""
            )}
                                </small>
                            </dd>
                        </div>

                        <div>
                            <dt>Started</dt>
                            <dd>${fmt(caseItem.startedAt)}</dd>
                        </div>

                        <div>
                            <dt>Last updated</dt>
                            <dd>${fmt(caseItem.updatedAt)}</dd>
                        </div>

                    </dl>

                </article>
            `).join("")

            : `
                <div class="empty-workload">

                    <b>No active cases</b>

                    <p>
                        This officer is not currently handling
                        an emergency or incident.
                    </p>

                </div>
            `;

    $("#workloadModal").classList.remove("hidden");
}
function renderUsers(){$('#userTable tbody').innerHTML=state.users.map(u=>`<tr><td><b>${escapeHtml(u.firstName)} ${escapeHtml(u.lastName)}</b><small>${escapeHtml(u.email)}</small></td><td>${escapeHtml(u.studentStaffNumber)}</td><td>${escapeHtml(u.role?.roleName||'—')}</td><td>${escapeHtml(u.campus?.campusName||'—')}</td><td>${escapeHtml(u.phoneNumber||'—')}</td><td>${pill(u.accountStatus)}</td><td><select class="status-select" data-user="${u.userId}"><option ${u.accountStatus==='ACTIVE'?'selected':''}>ACTIVE</option><option ${u.accountStatus==='SUSPENDED'?'selected':''}>SUSPENDED</option><option ${u.accountStatus==='BLOCKED'?'selected':''}>BLOCKED</option></select></td></tr>`).join('')||emptyRow(7,'No users found.');$$('.status-select').forEach(s=>s.onchange=async()=>{try{await request(`/users/${s.dataset.user}/status?status=${s.value}`,{method:'PUT'});await loadAll()}catch(e){setGlobal(e.message)}})}
function renderCampuses(){$('#campusSelect').innerHTML='<option value="">Select campus</option>'+state.campuses.map(c=>`<option value="${c.campusId}">${escapeHtml(c.campusName)}</option>`).join('')}
function emptyRow(n,text){return `<tr><td colspan="${n}" style="text-align:center;padding:35px;color:#6c7a8c">${text}</td></tr>`}
function setGlobal(text){const el=$('#globalMessage');el.textContent=text;el.classList.toggle('hidden',!text)}
function openView(name){$$('.view').forEach(v=>v.classList.toggle('active',v.id===name+'View'));$$('.nav-item').forEach(n=>n.classList.toggle('active',n.dataset.view===name));const titles={overview:'Security overview',emergencies:'Emergency alerts',incidents:'Incident reports',officers:'Security officers',users:'Students and staff'};$('#pageTitle').textContent=titles[name];$('.sidebar').classList.remove('open')}
$$('.nav-item').forEach(b=>b.onclick=()=>openView(b.dataset.view));$$('[data-open]').forEach(b=>b.onclick=()=>openView(b.dataset.open));$('#menuButton').onclick=()=>$('.sidebar').classList.toggle('open');$('#refreshButton').onclick=loadAll;$('#emergencyFilter').onchange=renderEmergencies;$$('[data-search]').forEach(input=>input.oninput=()=>{const q=input.value.toLowerCase();$$(`#${input.dataset.search} tbody tr`).forEach(row=>row.style.display=row.textContent.toLowerCase().includes(q)?'':'none')});
function logout(){sessionStorage.removeItem('ufhAdminToken');sessionStorage.removeItem('ufhAdmin');state.token=null;location.reload()}$('#logoutButton').onclick=logout;
const modal=$('#officerModal');$('#addOfficerButton').onclick=()=>modal.classList.remove('hidden');$('#closeModal').onclick=$('#cancelModal').onclick=()=>modal.classList.add('hidden');modal.onclick=e=>{if(e.target===modal)modal.classList.add('hidden')};
$('#officerForm').onsubmit=async e=>{e.preventDefault();const form=new FormData(e.target),params=new URLSearchParams(form);message($('#officerMessage'),'Creating officer account…',true);try{await request('/officers?'+params.toString(),{method:'POST'});e.target.reset();modal.classList.add('hidden');await loadAll();openView('officers')}catch(err){message($('#officerMessage'),err.message)}};
const workloadModal =
    $("#workloadModal");

function closeWorkloadModal() {
    workloadModal.classList.add("hidden");
}

$("#closeWorkloadModal").onclick =
    closeWorkloadModal;

$("#closeWorkloadButton").onclick =
    closeWorkloadModal;

workloadModal.onclick = event => {

    if (event.target === workloadModal) {
        closeWorkloadModal();
    }
};
if(state.token)showDashboard();
