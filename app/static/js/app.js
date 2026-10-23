// Main Application Controller for USTA Perfil Emprendedor
const App = {
    currentUser: null,
    activeView: 'resumen',
    periods: [],
    faculties: [],
    semesters: [],
    currentPeriod: 'Todos',
    currentFaculty: 'Todas',
    tempUploadId: null,

    async init() {
        this.bindNavigation();
        const authed = await this.checkAuth();
        if (authed) {
            await this.loadInitialData();
        }
    },

    async checkAuth() {
        try {
            const res = await fetch('/api/auth/me');
            if (res.ok) {
                this.currentUser = await res.json();
                this.renderUserBadge();
                return true;
            } else {
                this.currentUser = null;
                this.renderUserBadge();
                return false;
            }
        } catch (e) {
            this.currentUser = null;
            this.renderUserBadge();
            return false;
        }
    },

    renderUserBadge() {
        const userContainer = document.getElementById('user-header-status');
        const loginBtn = document.getElementById('btn-open-login');
        const adminElements = document.querySelectorAll('.admin-only');
        const authPortal = document.getElementById('auth-portal');
        const mainLayout = document.getElementById('app-main-layout');

        if (this.currentUser) {
            if (authPortal) authPortal.classList.add('hidden');
            if (mainLayout) mainLayout.classList.remove('hidden');
            if (userContainer) {
                userContainer.classList.remove('hidden');
                document.getElementById('user-display-name').textContent = this.currentUser.full_name;
                const roleBadge = document.getElementById('user-display-role');
                if (this.currentUser.role === 'admin') {
                    roleBadge.textContent = 'Administrador';
                    roleBadge.className = 'px-2 py-0.5 rounded text-xs font-semibold badge-admin';
                    adminElements.forEach(el => el.classList.remove('hidden'));
                } else {
                    roleBadge.textContent = 'Consulta';
                    roleBadge.className = 'px-2 py-0.5 rounded text-xs font-semibold badge-consulta';
                    adminElements.forEach(el => el.classList.add('hidden'));
                }
            }
            if (loginBtn) loginBtn.classList.add('hidden');
        } else {
            if (authPortal) authPortal.classList.remove('hidden');
            if (mainLayout) mainLayout.classList.add('hidden');
            if (userContainer) userContainer.classList.add('hidden');
            if (loginBtn) loginBtn.classList.remove('hidden');
            adminElements.forEach(el => el.classList.add('hidden'));
        }
    },

    bindNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const view = link.getAttribute('data-view');
                this.switchView(view);
            });
        });
    },

    switchView(viewName) {
        this.activeView = viewName;
        document.querySelectorAll('.view-section').forEach(sec => sec.classList.add('hidden'));
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active', 'bg-blue-900', 'text-yellow-400', 'border-l-4', 'border-yellow-400');
            if (link.getAttribute('data-view') === viewName) {
                link.classList.add('active', 'bg-blue-900', 'text-yellow-400', 'border-l-4', 'border-yellow-400');
            }
        });

        const targetSec = document.getElementById(`view-${viewName}`);
        if (targetSec) targetSec.classList.remove('hidden');

        // Trigger view specific loaders
        if (viewName === 'resumen') this.loadResumenView();
        else if (viewName === 'dashboard') this.loadDashboardView();
        else if (viewName === 'facultad') this.loadFacultadView();
        else if (viewName === 'comparacion') this.loadComparacionView();
        else if (viewName === 'informes') this.loadInformesView();
        else if (viewName === 'historico') this.loadHistoricoView();
        else if (viewName === 'admin') this.loadAdminView();
    },

    async loadInitialData() {
        try {
            const [pRes, fRes, sRes] = await Promise.all([
                fetch('/api/periods'),
                fetch('/api/faculties'),
                fetch('/api/semesters')
            ]);
            this.periods = await pRes.json();
            this.faculties = await fRes.json();
            this.semesters = await sRes.json();

            this.populateSelectors();
            this.loadResumenView();
        } catch (e) {
            console.error('Error cargando catálogos iniciales:', e);
        }
    },

    populateSelectors() {
        const periodSelects = [
            'dash-filter-period', 'fac-select-period', 'comp-select-p1', 'comp-select-p2',
            'rep-select-period', 'rep-zip-period', 'rep-gen-period', 'rep-comp-p1', 'rep-comp-p2'
        ];
        periodSelects.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            const currentVal = el.value;
            el.innerHTML = id.includes('filter') ? '<option value="Todos">Todos los periodos</option>' : '';
            this.periods.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.code;
                opt.textContent = `${p.code} (${p.authorized_responses} encuestas)`;
                el.appendChild(opt);
            });
            if (currentVal && el.querySelector(`option[value="${currentVal}"]`)) {
                el.value = currentVal;
            } else if (this.periods.length > 0 && !id.includes('filter')) {
                el.value = this.periods[0].code;
            }
        });

        const facultySelects = [
            'dash-filter-faculty', 'fac-select-faculty', 'comp-select-faculty', 'rep-select-faculty', 'rep-comp-faculty'
        ];
        facultySelects.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            const currentVal = el.value;
            el.innerHTML = id.includes('filter') || id.includes('comp') ? '<option value="Todas">Todas las facultades</option>' : '';
            this.faculties.forEach(f => {
                const opt = document.createElement('option');
                opt.value = f;
                opt.textContent = f;
                el.appendChild(opt);
            });
            if (currentVal && el.querySelector(`option[value="${currentVal}"]`)) {
                el.value = currentVal;
            } else if (this.faculties.length > 0 && !id.includes('filter') && !id.includes('comp')) {
                el.value = this.faculties[0];
            }
        });

        const semSelect = document.getElementById('dash-filter-semester');
        if (semSelect) {
            semSelect.innerHTML = '<option value="Todos">Todos los semestres</option>';
            this.semesters.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s;
                opt.textContent = s;
                semSelect.appendChild(opt);
            });
        }
    },

    // =========================================================================
    // VIEW 1: RESUMEN / INICIO
    // =========================================================================
    async loadResumenView() {
        try {
            const res = await fetch('/api/stats/dashboard?period_code=Todos');
            const data = await res.json();
            const k = data.kpis;

            document.getElementById('res-total-encuestas').textContent = k.total_encuestas.toLocaleString();
            document.getElementById('res-total-autorizadas').textContent = k.autorizadas.toLocaleString();
            document.getElementById('res-con-iniciativa').textContent = `${k.con_iniciativa.toLocaleString()} (${k.pct_con_iniciativa}%)`;
            document.getElementById('res-facultades-count').textContent = k.facultades_count;
            document.getElementById('res-periodos-count').textContent = this.periods.length;

            // Render mini overview table
            const tbody = document.getElementById('res-periods-table-body');
            if (tbody) {
                tbody.innerHTML = '';
                this.periods.forEach(p => {
                    const tr = document.createElement('tr');
                    tr.className = 'hover:bg-gray-50';
                    tr.innerHTML = `
                        <td class="px-4 py-3 font-semibold text-blue-900">${p.code}</td>
                        <td class="px-4 py-3 text-gray-700">${p.total_responses}</td>
                        <td class="px-4 py-3 text-green-700 font-medium">${p.authorized_responses}</td>
                        <td class="px-4 py-3 text-gray-600">${p.faculty_count}</td>
                        <td class="px-4 py-3 text-gray-500">${p.last_update ? new Date(p.last_update).toLocaleDateString() : 'N/A'}</td>
                        <td class="px-4 py-3">
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${p.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
                                ${p.is_active ? 'Activo' : 'Cerrado'}
                            </span>
                        </td>
                        <td class="px-4 py-3 text-right space-x-2">
                            <button onclick="App.quickExplorePeriod('${p.code}')" class="text-xs bg-blue-50 text-blue-800 hover:bg-blue-100 px-2 py-1 rounded">Explorar</button>
                            <button onclick="App.downloadGeneralReport('${p.code}')" class="text-xs bg-gray-100 text-gray-700 hover:bg-gray-200 px-2 py-1 rounded">PDF</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        } catch (e) {
            console.error('Error cargando resumen:', e);
        }
    },

    async onDashboardPeriodChange() {
        const period = document.getElementById('dash-filter-period')?.value || 'Todos';
        const facSelect = document.getElementById('dash-filter-faculty');
        if (facSelect) {
            const currentFac = facSelect.value;
            try {
                const res = await fetch(`/api/faculties?period_code=${encodeURIComponent(period)}`);
                const facs = await res.json();
                facSelect.innerHTML = '<option value="Todas">Todas las facultades</option>';
                facs.forEach(f => {
                    const opt = document.createElement('option');
                    opt.value = f;
                    opt.textContent = f;
                    facSelect.appendChild(opt);
                });
                if (facs.includes(currentFac)) {
                    facSelect.value = currentFac;
                } else {
                    facSelect.value = 'Todas';
                }
            } catch (e) {}
        }
        await this.loadDashboardView();
    },

    async onFacultyViewPeriodChange() {
        const period = document.getElementById('fac-select-period')?.value;
        const facSelect = document.getElementById('fac-select-faculty');
        if (!period || !facSelect) return;
        const currentFac = facSelect.value;
        try {
            const res = await fetch(`/api/faculties?period_code=${encodeURIComponent(period)}`);
            const facs = await res.json();
            facSelect.innerHTML = '';
            facs.forEach(f => {
                const opt = document.createElement('option');
                opt.value = f;
                opt.textContent = f;
                facSelect.appendChild(opt);
            });
            if (facs.includes(currentFac)) {
                facSelect.value = currentFac;
            } else if (facs.length > 0) {
                facSelect.value = facs[0];
            }
        } catch (e) {}
        await this.loadFacultadView();
    },

    async onReportPeriodChange() {
        const period = document.getElementById('rep-select-period')?.value;
        const facSelect = document.getElementById('rep-select-faculty');
        if (!period || !facSelect) return;
        const currentFac = facSelect.value;
        try {
            const res = await fetch(`/api/faculties?period_code=${encodeURIComponent(period)}`);
            const facs = await res.json();
            facSelect.innerHTML = '';
            facs.forEach(f => {
                const opt = document.createElement('option');
                opt.value = f;
                opt.textContent = f;
                facSelect.appendChild(opt);
            });
            if (facs.includes(currentFac)) {
                facSelect.value = currentFac;
            } else if (facs.length > 0) {
                facSelect.value = facs[0];
            }
        } catch (e) {}
    },

    // =========================================================================
    // VIEW 2: PANEL DE ANÁLISIS (DASHBOARD)
    // =========================================================================
    async loadDashboardView() {
        const period = document.getElementById('dash-filter-period')?.value || 'Todos';
        const faculty = document.getElementById('dash-filter-faculty')?.value || 'Todas';
        const semester = document.getElementById('dash-filter-semester')?.value || 'Todos';
        const initiative = document.getElementById('dash-filter-status')?.value || 'Todos';
        const stage = document.getElementById('dash-filter-stage')?.value || 'Todas';

        const params = new URLSearchParams({
            period_code: period,
            faculty_name: faculty,
            semester: semester,
            initiative_status: initiative,
            stage: stage
        });

        try {
            const res = await fetch(`/api/stats/dashboard?${params.toString()}`);
            const data = await res.json();
            const k = data.kpis;

            // KPIs
            document.getElementById('dash-kpi-participantes').textContent = k.total_encuestas.toLocaleString();
            document.getElementById('dash-kpi-autorizados').textContent = `${k.autorizadas.toLocaleString()} autorizados`;
            document.getElementById('dash-kpi-con-iniciativa').textContent = k.con_iniciativa.toLocaleString();
            document.getElementById('dash-kpi-pct-con').textContent = `${k.pct_con_iniciativa}% del total`;
            document.getElementById('dash-kpi-sin-iniciativa').textContent = k.sin_iniciativa.toLocaleString();
            document.getElementById('dash-kpi-pct-sin').textContent = `${k.pct_sin_iniciativa}% del total`;
            document.getElementById('dash-kpi-apoyo').textContent = k.apoyo_recibido_count.toLocaleString();
            document.getElementById('dash-kpi-pct-apoyo').textContent = `${k.pct_apoyo_recibido}% de iniciativas`;

            // Charts
            // 1. Situación Doughnut
            ChartManager.renderDoughnut(
                'chart-situacion',
                ['Con idea o emprendimiento', 'Sin emprendimiento'],
                [k.con_iniciativa, k.sin_iniciativa],
                ['#2563EB', '#CBD5E1']
            );

            // 2. Semestres Bar
            const semLabels = data.dist_semestres.map(d => d.label);
            const semData = data.dist_semestres.map(d => d.count);
            ChartManager.renderBar('chart-semestres', semLabels, semData, 'Estudiantes', '#0B2545');

            // 3. Etapas INNPulsa Bar
            const etapaLabels = data.dist_etapas.map(d => d.label);
            const etapaData = data.dist_etapas.map(d => d.count);
            ChartManager.renderBar('chart-etapas', etapaLabels, etapaData, 'Iniciativas', '#0D9488');

            // 4. Sectores Horiz Bar
            const secLabels = data.dist_sectores.map(d => d.label);
            const secData = data.dist_sectores.map(d => d.count);
            ChartManager.renderBar('chart-sectores', secLabels, secData, 'Iniciativas', '#133E87', true);

            // 5. Fuentes Bar
            const fuentesLabels = data.dist_fuentes.map(d => d.label);
            const fuentesData = data.dist_fuentes.map(d => d.count);
            ChartManager.renderBar('chart-fuentes', fuentesLabels, fuentesData, 'Menciones', '#FDB813');

            // 6. Apoyo Doughnut
            const apoyoLabels = data.dist_apoyo.map(d => d.label);
            const apoyoData = data.dist_apoyo.map(d => d.count);
            ChartManager.renderDoughnut('chart-apoyo', apoyoLabels, apoyoData, ['#10B981', '#94A3B8', '#E2E8F0']);

            // 7. Profile Accordion / Cards
            this.renderProfileQuestions(data.dist_perfil);

        } catch (e) {
            console.error('Error cargando dashboard:', e);
        }
    },

    renderProfileQuestions(perfilData) {
        const container = document.getElementById('dash-perfil-container');
        if (!container) return;
        container.innerHTML = '';

        const questionMeta = [
            { key: 'P13', title: 'Iniciativa emprendedora (P13)', desc: 'Preferencia entre procesos estructurados vs. ideación de proyectos nuevos' },
            { key: 'P16', title: 'Comunicación e influencia social (P16)', desc: 'Capacidad para persuadir y transmitir ideas en equipo y redes' },
            { key: 'P17', title: 'Orientación comercial (P17)', desc: 'Postura frente a ventas, mercadeo y promoción directa' },
            { key: 'P20', title: 'Actitud frente al riesgo (P20)', desc: 'Disposición a asumir riesgos calculados vs. moderados' },
            { key: 'P21', title: 'Validación y viabilidad (P21)', desc: 'Prioridad de estudio de mercado y validación de capacidades' }
        ];

        questionMeta.forEach(qm => {
            const q = perfilData[qm.key];
            if (!q || !q.top_options) return;

            const card = document.createElement('div');
            card.className = 'usta-card p-4 border border-gray-200';

            let optionsHtml = '';
            q.top_options.forEach(opt => {
                optionsHtml += `
                    <div class="mb-2">
                        <div class="flex justify-between text-xs font-medium text-gray-700 mb-1">
                            <span class="truncate pr-2">${opt.label}</span>
                            <span class="font-bold text-blue-900">${opt.count} (${opt.percentage}%)</span>
                        </div>
                        <div class="w-full bg-gray-100 rounded-full h-2">
                            <div class="bg-blue-800 h-2 rounded-full" style="width: ${opt.percentage}%"></div>
                        </div>
                    </div>
                `;
            });
            if (q.other_count > 0) {
                optionsHtml += `
                    <div class="mb-2">
                        <div class="flex justify-between text-xs font-medium text-gray-500 mb-1">
                            <span>Otras respuestas</span>
                            <span>${q.other_count} (${q.other_pct}%)</span>
                        </div>
                        <div class="w-full bg-gray-100 rounded-full h-2">
                            <div class="bg-gray-400 h-2 rounded-full" style="width: ${q.other_pct}%"></div>
                        </div>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="flex items-center justify-between border-b pb-2 mb-3">
                    <h4 class="text-sm font-bold text-blue-950">${qm.title}</h4>
                    <span class="text-xs bg-blue-50 text-blue-800 px-2 py-0.5 rounded font-medium">${q.valid_responses} válidas</span>
                </div>
                <p class="text-xs text-gray-500 mb-3">${qm.desc}</p>
                ${optionsHtml}
            `;
            container.appendChild(card);
        });
    },

    // =========================================================================
    // VIEW 3: ANÁLISIS POR FACULTAD
    // =========================================================================
    async loadFacultadView() {
        const period = document.getElementById('fac-select-period')?.value;
        const faculty = document.getElementById('fac-select-faculty')?.value;
        if (!period || !faculty) return;

        try {
            const res = await fetch(`/api/stats/faculty-detail?period_code=${encodeURIComponent(period)}&faculty_name=${encodeURIComponent(faculty)}`);
            const data = await res.json();
            const k = data.kpis;

            document.getElementById('fac-view-title').textContent = data.faculty_name;
            document.getElementById('fac-view-period').textContent = `Periodo Académico ${data.period_code}`;
            document.getElementById('fac-kpi-part').textContent = k.total_encuestas;
            document.getElementById('fac-kpi-con').textContent = `${k.con_iniciativa} (${k.pct_con_iniciativa}%)`;
            document.getElementById('fac-kpi-sin').textContent = `${k.sin_iniciativa} (${k.pct_sin_iniciativa}%)`;
            document.getElementById('fac-resumen-text').textContent = data.resumen_ejecutivo;

            // Render Etapas Table
            const etapasBody = document.getElementById('fac-etapas-tbody');
            if (etapasBody) {
                etapasBody.innerHTML = '';
                data.etapas.forEach(item => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="px-3 py-2 text-gray-800">${item.label}</td>
                        <td class="px-3 py-2 text-right font-medium">${item.count}</td>
                        <td class="px-3 py-2 text-right font-bold text-blue-900">${item.percentage.toFixed(1)} %</td>
                    `;
                    etapasBody.appendChild(tr);
                });
            }

            // Render Sectores Table
            const secBody = document.getElementById('fac-sectores-tbody');
            if (secBody) {
                secBody.innerHTML = '';
                (data.sectores.slice(0, 7)).forEach(item => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="px-3 py-2 text-gray-800">${item.label}</td>
                        <td class="px-3 py-2 text-right font-medium">${item.count}</td>
                        <td class="px-3 py-2 text-right font-bold text-blue-900">${item.percentage.toFixed(1)} %</td>
                    `;
                    secBody.appendChild(tr);
                });
            }

            // Accompaniment Lines
            const o = data.orientaciones;
            document.getElementById('fac-acomp-exploracion').textContent = o.exploracion;
            document.getElementById('fac-acomp-validacion').textContent = o.validacion;
            document.getElementById('fac-acomp-fortalecimiento').textContent = o.fortalecimiento;

        } catch (e) {
            console.error('Error cargando detalle de facultad:', e);
        }
    },

    downloadFacultyCurrentReport() {
        const period = document.getElementById('fac-select-period')?.value;
        const faculty = document.getElementById('fac-select-faculty')?.value;
        if (!period || !faculty) return;
        window.open(`/api/reports/faculty-pdf?period_code=${encodeURIComponent(period)}&faculty_name=${encodeURIComponent(faculty)}&download=true`, '_blank');
    },

    previewFacultyCurrentReport() {
        const period = document.getElementById('fac-select-period')?.value;
        const faculty = document.getElementById('fac-select-faculty')?.value;
        if (!period || !faculty) return;
        this.openPdfModal(`/api/reports/faculty-pdf?period_code=${encodeURIComponent(period)}&faculty_name=${encodeURIComponent(faculty)}&download=false`, `Informe ${faculty} - ${period}`);
    },

    // =========================================================================
    // VIEW 4: COMPARACIÓN DE PERIODOS
    // =========================================================================
    async loadComparacionView() {
        const p1 = document.getElementById('comp-select-p1')?.value;
        const p2 = document.getElementById('comp-select-p2')?.value;
        const fac = document.getElementById('comp-select-faculty')?.value || 'Todas';

        if (!p1 || !p2) return;

        try {
            const res = await fetch(`/api/stats/comparison?period_1=${encodeURIComponent(p1)}&period_2=${encodeURIComponent(p2)}&faculty_name=${encodeURIComponent(fac)}`);
            const data = await res.json();
            const kc = data.kpi_comparison;

            document.getElementById('comp-commentary').textContent = data.analytical_commentary;

            // Render KPI diff cards
            document.getElementById('comp-val-part-p1').textContent = kc.participantes.val1;
            document.getElementById('comp-val-part-p2').textContent = kc.participantes.val2;
            const diffPart = document.getElementById('comp-diff-part');
            diffPart.textContent = `${kc.participantes.diff >= 0 ? '+' : ''}${kc.participantes.diff} (${kc.participantes.rel_pct >= 0 ? '+' : ''}${kc.participantes.rel_pct}%)`;
            diffPart.className = `text-xs font-bold ${kc.participantes.diff >= 0 ? 'text-green-600' : 'text-red-600'}`;

            document.getElementById('comp-val-init-p1').textContent = `${kc.pct_con_iniciativa.val1}%`;
            document.getElementById('comp-val-init-p2').textContent = `${kc.pct_con_iniciativa.val2}%`;
            const diffInit = document.getElementById('comp-diff-init');
            diffInit.textContent = `${kc.pct_con_iniciativa.diff >= 0 ? '+' : ''}${kc.pct_con_iniciativa.diff} pp`;
            diffInit.className = `text-xs font-bold ${kc.pct_con_iniciativa.diff >= 0 ? 'text-green-600' : 'text-red-600'}`;

            // Render Faculty Breakdown Table
            const fbBody = document.getElementById('comp-fac-tbody');
            if (fbBody) {
                fbBody.innerHTML = '';
                data.fac_breakdown.forEach(f => {
                    const tr = document.createElement('tr');
                    const diffColor = f.diff_pp >= 0 ? 'text-green-700' : 'text-red-700';
                    tr.innerHTML = `
                        <td class="px-3 py-2 font-medium text-gray-800">${f.faculty}</td>
                        <td class="px-3 py-2 text-right">${f.total_p1}</td>
                        <td class="px-3 py-2 text-right font-medium">${f.pct_p1}%</td>
                        <td class="px-3 py-2 text-right">${f.total_p2}</td>
                        <td class="px-3 py-2 text-right font-medium">${f.pct_p2}%</td>
                        <td class="px-3 py-2 text-right font-bold ${diffColor}">${f.diff_pp >= 0 ? '+' : ''}${f.diff_pp} pp</td>
                    `;
                    fbBody.appendChild(tr);
                });
            }

            // Render Stage Comparison Table
            const stBody = document.getElementById('comp-stage-tbody');
            if (stBody) {
                stBody.innerHTML = '';
                data.stage_comparison.forEach(s => {
                    const tr = document.createElement('tr');
                    const diffColor = s.diff_pp >= 0 ? 'text-green-700' : 'text-red-700';
                    tr.innerHTML = `
                        <td class="px-3 py-2 font-medium text-gray-800">${s.stage}</td>
                        <td class="px-3 py-2 text-right">${s.count_p1} (${s.pct_p1}%)</td>
                        <td class="px-3 py-2 text-right">${s.count_p2} (${s.pct_p2}%)</td>
                        <td class="px-3 py-2 text-right font-bold ${diffColor}">${s.diff_pp >= 0 ? '+' : ''}${s.diff_pp} pp</td>
                    `;
                    stBody.appendChild(tr);
                });
            }
        } catch (e) {
            console.error('Error cargando comparación:', e);
        }
    },

    downloadComparativeReport() {
        const p1 = document.getElementById('comp-select-p1')?.value;
        const p2 = document.getElementById('comp-select-p2')?.value;
        const fac = document.getElementById('comp-select-faculty')?.value || 'Todas';
        if (!p1 || !p2) return;
        window.open(`/api/reports/comparative-pdf?period_1=${encodeURIComponent(p1)}&period_2=${encodeURIComponent(p2)}&faculty_name=${encodeURIComponent(fac)}&download=true`, '_blank');
    },

    // =========================================================================
    // VIEW 5: CARGAR INFORMACIÓN (EXCEL FORMS)
    // =========================================================================
    async handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;
        await this.processUploadFile(file);
        e.target.value = '';
    },

    async processUploadFile(file) {
        if (!this.currentUser || this.currentUser.role !== 'admin') {
            alert('Atención: Solo los funcionarios con rol de Administrador pueden cargar o actualizar información en la base de datos.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        const pSelect = document.getElementById('upload-target-period');
        if (pSelect && pSelect.value) {
            formData.append('period_code', pSelect.value);
        }

        const progressDiv = document.getElementById('upload-progress');
        if (progressDiv) progressDiv.classList.remove('hidden');

        try {
            const res = await fetch('/api/upload/preview', {
                method: 'POST',
                body: formData
            });

            if (progressDiv) progressDiv.classList.add('hidden');

            if (!res.ok) {
                let errMsg = 'No se pudo leer el archivo';
                try {
                    const err = await res.json();
                    errMsg = err.detail || errMsg;
                } catch (_) {}
                alert(`Error en validación: ${errMsg}`);
                return;
            }

            const preview = await res.json();
            this.showPreviewModal(preview);
        } catch (e) {
            if (progressDiv) progressDiv.classList.add('hidden');
            console.error('Error al procesar la carga:', e);
            alert(`Error al procesar el archivo: ${e.message || 'Error de comunicación'}`);
        }
    },

    showPreviewModal(preview) {
        this.tempUploadId = preview.temp_file_id;
        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val !== undefined && val !== null ? val : '';
        };

        setVal('prev-filename', preview.filename);
        setVal('prev-period', preview.detected_period);

        // Populate period selector
        const pSel = document.getElementById('prev-period-select');
        if (pSel) {
            pSel.innerHTML = '';

            const detectedKeys = preview.periods_detected ? Object.keys(preview.periods_detected) : [];
            if (detectedKeys.length > 1) {
                const summary = Object.entries(preview.periods_detected).map(([k, v]) => `${k} (${v})`).join(', ');
                const optAuto = document.createElement('option');
                optAuto.value = 'auto_split';
                optAuto.textContent = `⚡ Distribuir automáticamente por fecha: ${summary}`;
                pSel.appendChild(optAuto);
            }

            detectedKeys.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p;
                opt.textContent = `Asignar todos los registros a ${p}`;
                pSel.appendChild(opt);
            });

            if (this.periods) {
                this.periods.forEach(p => {
                    if (!detectedKeys.includes(p.code)) {
                        const opt = document.createElement('option');
                        opt.value = p.code;
                        opt.textContent = `Asignar todos los registros a ${p.code}`;
                        pSel.appendChild(opt);
                    }
                });
            }

            if (detectedKeys.length > 1) {
                pSel.value = 'auto_split';
            } else if (preview.detected_period) {
                pSel.value = preview.detected_period;
            }
        }

        setVal('prev-total-rows', (preview.total_rows || 0).toLocaleString());
        setVal('prev-auth-rows', (preview.authorized_rows || 0).toLocaleString());
        setVal('prev-unauth-rows', (preview.unauthorized_rows || 0).toLocaleString());
        setVal('prev-new-rows', (preview.new_rows || 0).toLocaleString());
        setVal('prev-updated-rows', (preview.updated_rows || 0).toLocaleString());
        setVal('prev-unchanged-rows', (preview.unchanged_rows || 0).toLocaleString());
        setVal('prev-db-count', (preview.current_db_count || 0).toLocaleString());

        const warnContainer = document.getElementById('prev-warnings-container');
        if (warnContainer) {
            warnContainer.innerHTML = '';
            if (preview.warnings && preview.warnings.length > 0) {
                preview.warnings.forEach(w => {
                    const p = document.createElement('p');
                    p.className = 'text-xs text-amber-800 bg-amber-50 p-2 rounded border border-amber-200 mb-1';
                    p.textContent = `⚠️ ${w}`;
                    warnContainer.appendChild(p);
                });
            }
        }

        const sampleBody = document.getElementById('prev-samples-tbody');
        if (sampleBody) {
            sampleBody.innerHTML = '';
            (preview.preview_samples || []).forEach(s => {
                const tr = document.createElement('tr');
                let badgeClass = 'bg-blue-100 text-blue-800';
                if (s.status === 'SIN CAMBIOS') badgeClass = 'bg-gray-100 text-gray-800';
                else if (s.status === 'MODIFICADO') badgeClass = 'bg-amber-100 text-amber-800';
                tr.innerHTML = `
                    <td class="px-3 py-2 font-mono text-xs">${s.original_id}</td>
                    <td class="px-3 py-2 text-xs">${s.faculty}</td>
                    <td class="px-3 py-2 text-xs">${s.semester}</td>
                    <td class="px-3 py-2 text-xs">${s.authorized}</td>
                    <td class="px-3 py-2 text-xs font-semibold"><span class="px-2 py-0.5 rounded text-xs ${badgeClass}">${s.status}</span></td>
                `;
                sampleBody.appendChild(tr);
            });
        }

        const prevModal = document.getElementById('preview-modal');
        if (prevModal) prevModal.classList.remove('hidden');
    },

    closePreviewModal() {
        document.getElementById('preview-modal').classList.add('hidden');
        this.tempUploadId = null;
    },

    async confirmUploadCommit() {
        if (!this.tempUploadId) return;

        const periodSelect = document.getElementById('prev-period-select');
        const periodCode = (periodSelect && periodSelect.value) ? periodSelect.value : document.getElementById('prev-period').textContent;
        const mode = document.getElementById('upload-mode-select')?.value || 'smart_update';

        try {
            const res = await fetch('/api/upload/confirm', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    temp_file_id: this.tempUploadId,
                    period_code: periodCode,
                    mode: mode
                })
            });

            if (!res.ok) {
                const err = await res.json();
                alert(`Error al confirmar la carga: ${err.detail}`);
                return;
            }

            const data = await res.json();
            this.closePreviewModal();
            alert(`✅ ${data.message}\nRegistros nuevos: ${data.new_records}\nActualizados: ${data.updated_records}\nSin cambios: ${data.unchanged_records}`);

            await this.loadInitialData();
            this.switchView('dashboard');
        } catch (e) {
            alert('Error al confirmar la carga en el servidor.');
        }
    },

    // =========================================================================
    // VIEW 6: GENERAR INFORMES (PDF Y ZIP)
    // =========================================================================
    loadInformesView() {
        // Just verify selectors are loaded
    },

    downloadFacultyReportDirect() {
        const period = document.getElementById('rep-select-period')?.value;
        const faculty = document.getElementById('rep-select-faculty')?.value;
        if (!period || !faculty) return;
        window.open(`/api/reports/faculty-pdf?period_code=${encodeURIComponent(period)}&faculty_name=${encodeURIComponent(faculty)}&download=true`, '_blank');
    },

    previewFacultyReportDirect() {
        const period = document.getElementById('rep-select-period')?.value;
        const faculty = document.getElementById('rep-select-faculty')?.value;
        if (!period || !faculty) return;
        this.openPdfModal(`/api/reports/faculty-pdf?period_code=${encodeURIComponent(period)}&faculty_name=${encodeURIComponent(faculty)}&download=false`, `Informe ${faculty} - ${period}`);
    },

    downloadZipDirect() {
        const period = document.getElementById('rep-zip-period')?.value;
        if (!period) return;
        window.open(`/api/reports/faculties-zip?period_code=${encodeURIComponent(period)}`, '_blank');
    },

    downloadGeneralReport(periodCode = null) {
        const period = periodCode || document.getElementById('rep-gen-period')?.value;
        if (!period) return;
        window.open(`/api/reports/general-pdf?period_code=${encodeURIComponent(period)}&download=true`, '_blank');
    },

    downloadComparativeReportDirect() {
        const p1 = document.getElementById('rep-comp-p1')?.value;
        const p2 = document.getElementById('rep-comp-p2')?.value;
        const fac = document.getElementById('rep-comp-faculty')?.value || 'Todas';
        if (!p1 || !p2) return;
        window.open(`/api/reports/comparative-pdf?period_1=${encodeURIComponent(p1)}&period_2=${encodeURIComponent(p2)}&faculty_name=${encodeURIComponent(fac)}&download=true`, '_blank');
    },

    openPdfModal(url, title) {
        document.getElementById('pdf-modal-title').textContent = title;
        document.getElementById('pdf-modal-frame').src = url;
        document.getElementById('pdf-modal').classList.remove('hidden');
    },

    closePdfModal() {
        document.getElementById('pdf-modal-frame').src = '';
        document.getElementById('pdf-modal').classList.add('hidden');
    },

    // =========================================================================
    // VIEW 7: HISTÓRICO DE PERIODOS
    // =========================================================================
    async loadHistoricoView() {
        const tbody = document.getElementById('hist-periods-tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        this.periods.forEach(p => {
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-gray-50';
            tr.innerHTML = `
                <td class="px-4 py-3 font-bold text-blue-950">${p.code}</td>
                <td class="px-4 py-3 text-gray-700">${p.created_at ? new Date(p.created_at).toLocaleDateString() : 'N/A'}</td>
                <td class="px-4 py-3 text-gray-700">${p.last_update ? new Date(p.last_update).toLocaleDateString() : 'N/A'}</td>
                <td class="px-4 py-3 font-semibold text-gray-900">${p.total_responses}</td>
                <td class="px-4 py-3 font-bold text-green-700">${p.authorized_responses}</td>
                <td class="px-4 py-3 text-gray-700">${p.faculty_count}</td>
                <td class="px-4 py-3">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${p.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
                        ${p.is_active ? 'Vigente' : 'Histórico'}
                    </span>
                </td>
                <td class="px-4 py-3 text-right space-x-2">
                    <button onclick="App.quickExplorePeriod('${p.code}')" class="text-xs bg-blue-100 text-blue-900 hover:bg-blue-200 px-2.5 py-1 rounded font-medium">Dashboard</button>
                    <button onclick="App.downloadGeneralReport('${p.code}')" class="text-xs bg-amber-100 text-amber-900 hover:bg-amber-200 px-2.5 py-1 rounded font-medium">PDF General</button>
                    <button onclick="App.downloadZipDirectByCode('${p.code}')" class="text-xs bg-indigo-100 text-indigo-900 hover:bg-indigo-200 px-2.5 py-1 rounded font-medium">ZIP Facultades</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Load load history audit table
        try {
            const res = await fetch('/api/upload/history');
            const history = await res.json();
            const hBody = document.getElementById('hist-uploads-tbody');
            if (hBody) {
                hBody.innerHTML = '';
                history.forEach(h => {
                    const tr = document.createElement('tr');
                    tr.className = 'hover:bg-gray-50 text-xs';
                    tr.innerHTML = `
                        <td class="px-3 py-2 text-gray-500">${new Date(h.loaded_at).toLocaleString()}</td>
                        <td class="px-3 py-2 font-semibold text-blue-900">${h.period_code}</td>
                        <td class="px-3 py-2 text-gray-700 truncate max-w-xs">${h.filename}</td>
                        <td class="px-3 py-2 text-right">${h.total_rows}</td>
                        <td class="px-3 py-2 text-right text-green-700 font-bold">+${h.new_rows}</td>
                        <td class="px-3 py-2 text-right text-amber-700 font-bold">${h.updated_rows}</td>
                        <td class="px-3 py-2 text-right text-gray-500">${h.unchanged_rows}</td>
                        <td class="px-3 py-2 text-gray-600">${h.loaded_by || 'Sistema'}</td>
                    `;
                    hBody.appendChild(tr);
                });
            }
        } catch (e) {
            console.error('Error cargando historial de cargas:', e);
        }
    },

    downloadZipDirectByCode(pCode) {
        window.open(`/api/reports/faculties-zip?period_code=${encodeURIComponent(pCode)}`, '_blank');
    },

    // =========================================================================
    // VIEW 8: ADMINISTRACIÓN
    // =========================================================================
    async loadAdminView() {
        if (!this.currentUser || this.currentUser.role !== 'admin') {
            alert('Acceso restringido a Administradores.');
            this.switchView('resumen');
            return;
        }
        this.loadUsersList();
        this.loadAuditLogs();
    },

    async loadUsersList() {
        try {
            const res = await fetch('/api/admin/users');
            const users = await res.json();
            const tbody = document.getElementById('admin-users-tbody');
            if (!tbody) return;
            tbody.innerHTML = '';

            users.forEach(u => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-gray-50';
                tr.innerHTML = `
                    <td class="px-4 py-3 font-semibold text-gray-900">${u.full_name}</td>
                    <td class="px-4 py-3 text-gray-600 font-mono text-xs">${u.username}</td>
                    <td class="px-4 py-3">
                        <span class="px-2 py-0.5 rounded text-xs font-semibold ${u.role === 'admin' ? 'badge-admin' : 'badge-consulta'}">
                            ${u.role === 'admin' ? 'Administrador' : 'Consulta'}
                        </span>
                    </td>
                    <td class="px-4 py-3">
                        <span class="px-2 py-0.5 rounded text-xs font-semibold ${u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                            ${u.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                    </td>
                    <td class="px-4 py-3 text-gray-500 text-xs">${u.last_login ? new Date(u.last_login).toLocaleString() : 'Sin registro'}</td>
                    <td class="px-4 py-3 text-right">
                        <button onclick="App.toggleUserActive(${u.id}, ${!u.is_active})" class="text-xs px-2 py-1 rounded ${u.is_active ? 'bg-red-50 text-red-700 hover:bg-red-100' : 'bg-green-50 text-green-700 hover:bg-green-100'}">
                            ${u.is_active ? 'Desactivar' : 'Activar'}
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } catch (e) {
            console.error('Error cargando usuarios:', e);
        }
    },

    async toggleUserActive(userId, newStatus) {
        try {
            const res = await fetch(`/api/admin/users/${userId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: newStatus })
            });
            if (res.ok) {
                this.loadUsersList();
            }
        } catch (e) {
            alert('Error actualizando estado del usuario');
        }
    },

    async createNewUser() {
        const name = prompt('Nombre completo del funcionario:');
        if (!name) return;
        const email = prompt('Correo electrónico institucional:');
        if (!email) return;
        const role = prompt('Rol (escriba "admin" para Administrador o "consulta" para Consulta):', 'consulta');
        if (!role) return;
        const pass = prompt('Contraseña inicial:');
        if (!pass) return;

        try {
            const res = await fetch('/api/admin/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    full_name: name,
                    username: email,
                    role: role.toLowerCase() === 'admin' ? 'admin' : 'consulta',
                    password: pass
                })
            });
            if (res.ok) {
                alert('Usuario creado exitosamente');
                this.loadUsersList();
            } else {
                const err = await res.json();
                alert(`Error: ${err.detail}`);
            }
        } catch (e) {
            alert('Error al crear usuario');
        }
    },

    async createNewPeriodPrompt() {
        const code = prompt('Ingrese el código del nuevo periodo académico (formato AAAA-1 o AAAA-2, ej: 2027-1):');
        if (!code) return;
        const desc = prompt('Descripción del periodo (opcional):', `Periodo Académico ${code}`);

        try {
            const res = await fetch('/api/periods', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code: code.trim(),
                    description: desc
                })
            });
            if (res.ok) {
                alert(`Periodo ${code} creado exitosamente.`);
                await this.loadInitialData();
            } else {
                const err = await res.json();
                alert(`Error: ${err.detail}`);
            }
        } catch (e) {
            alert('Error al crear periodo');
        }
    },

    downloadBackupFile() {
        window.open('/api/admin/backup/download', '_blank');
    },

    async handleBackupRestore(e) {
        const file = e.target.files[0];
        if (!file) return;

        if (!confirm('¿Confirma que desea restaurar este archivo de respaldo institucional? Esta acción integrará los periodos y registros contenidos.')) {
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/admin/backup/restore', {
                method: 'POST',
                body: formData
            });
            if (res.ok) {
                const data = await res.json();
                alert(data.message);
                await this.loadInitialData();
            } else {
                const err = await res.json();
                alert(`Error al restaurar: ${err.detail}`);
            }
        } catch (e) {
            alert('Error en la comunicación con el servidor al restaurar.');
        }
    },

    async loadAuditLogs() {
        try {
            const res = await fetch('/api/admin/audit-logs');
            const logs = await res.json();
            const tbody = document.getElementById('admin-audit-tbody');
            if (!tbody) return;
            tbody.innerHTML = '';
            logs.forEach(l => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-gray-50 text-xs';
                tr.innerHTML = `
                    <td class="px-3 py-2 text-gray-500">${new Date(l.created_at).toLocaleString()}</td>
                    <td class="px-3 py-2 font-medium text-blue-900">${l.user_email || 'Sistema'}</td>
                    <td class="px-3 py-2 font-semibold text-gray-800">${l.action}</td>
                    <td class="px-3 py-2 text-gray-600 truncate max-w-sm">${l.details || ''}</td>
                    <td class="px-3 py-2 text-gray-400 font-mono">${l.ip_address || ''}</td>
                `;
                tbody.appendChild(tr);
            });
        } catch (e) {}
    },

    // =========================================================================
    // AUTH MODAL & LOGOUT
    // =========================================================================
    openLoginModal() {
        document.getElementById('login-modal').classList.remove('hidden');
    },

    closeLoginModal() {
        document.getElementById('login-modal').classList.add('hidden');
    },

    async submitPortalLogin(e) {
        e.preventDefault();
        const u = document.getElementById('portal-email').value;
        const p = document.getElementById('portal-password').value;

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: u, password: p })
            });

            if (res.ok) {
                const data = await res.json();
                this.currentUser = data.user;
                this.renderUserBadge();
                await this.loadInitialData();
                this.switchView('resumen');
            } else {
                const err = await res.json();
                alert(`Error de autenticación: ${err.detail || 'Credenciales no autorizadas'}`);
            }
        } catch (e) {
            alert('Error de conexión con el servidor institucional.');
        }
    },

    async submitLogin(e) {
        e.preventDefault();
        const u = document.getElementById('login-email').value;
        const p = document.getElementById('login-password').value;

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: u, password: p })
            });

            if (res.ok) {
                const data = await res.json();
                this.currentUser = data.user;
                this.renderUserBadge();
                this.closeLoginModal();
                await this.loadInitialData();
                this.switchView('resumen');
            } else {
                const err = await res.json();
                alert(`Error: ${err.detail || 'Credenciales inválidas'}`);
            }
        } catch (e) {
            alert('Error de conexión con el servidor.');
        }
    },

    async logout() {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
            this.currentUser = null;
            this.renderUserBadge();
        } catch (e) {
            this.currentUser = null;
            this.renderUserBadge();
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
