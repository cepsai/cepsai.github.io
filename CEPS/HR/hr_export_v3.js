// ── HR Export: CSV/JSON export utilities ────────────────────────────────────

const HRExport = {
  // Download helper
  _download(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  // ── JSON exports ──────────────────────────────────────────────────────
  exportAllJSON() {
    const data = HRStore.exportAll();
    this._download(JSON.stringify(data, null, 2), `ceps_hr_backup_${this._dateStr()}.json`, 'application/json');
    HRStore.recordBackup();
  },

  exportEmployeeJSON(empId) {
    const data = HRStore.exportEmployeeData(empId);
    const emp = data.employee;
    const name = emp ? emp.name.replace(/\s+/g, '_') : empId;
    this._download(JSON.stringify(data, null, 2), `ceps_hr_${name}_${this._dateStr()}.json`, 'application/json');
  },

  // ── CSV exports ───────────────────────────────────────────────────────
  exportEmployeesCSV() {
    const emps = HRStore.getEmployees();
    const skillIds = SKILLS.map(s => s.id);
    const headers = ['ID', 'Name', 'Email', 'Current Role', 'Unit', 'Target Role', 'Target Validated', ...SKILLS.map(s => s.name)];

    let csv = this._csvRow(headers);
    for (const emp of emps) {
      const role = ROLES.find(r => r.id === emp.currentRoleId);
      const targetRole = ROLES.find(r => r.id === emp.targetRoleId);
      const row = [
        emp.id, emp.name, emp.email,
        role ? role.name : emp.currentRoleId,
        emp.unit,
        targetRole ? targetRole.name : (emp.targetRoleId || ''),
        emp.targetRoleValidated ? 'Yes' : 'No',
        ...skillIds.map(sid => emp.skills?.[sid]?.level || '')
      ];
      csv += this._csvRow(row);
    }
    this._download(csv, `ceps_hr_employees_${this._dateStr()}.csv`, 'text/csv');
  },

  exportGapAnalysisCSV() {
    const emps = HRStore.getEmployees();
    const headers = ['Employee', 'Current Role', 'Target Role', 'Skill', 'Current Level', 'Required Level', 'Gap'];

    let csv = this._csvRow(headers);
    for (const emp of emps) {
      if (!emp.targetRoleId) continue;
      const targetRole = ROLES.find(r => r.id === emp.targetRoleId);
      if (!targetRole) continue;
      const currentRole = ROLES.find(r => r.id === emp.currentRoleId);

      for (const skill of SKILLS) {
        const required = targetRole.requirements[skill.id];
        if (!required) continue;
        const current = emp.skills?.[skill.id]?.level || null;
        const gap = lvNum(required) - lvNum(current);
        if (gap > 0) {
          csv += this._csvRow([
            emp.name,
            currentRole ? currentRole.name : emp.currentRoleId,
            targetRole.name,
            skill.name,
            current || 'Not assessed',
            required,
            gap + ' level(s)'
          ]);
        }
      }
    }
    this._download(csv, `ceps_hr_gap_analysis_${this._dateStr()}.csv`, 'text/csv');
  },

  exportIDPsCSV() {
    const idps = HRStore.getIDPs();
    const emps = HRStore.getEmployees();
    const headers = ['Employee', 'Target Role', 'IDP Status', 'Action', 'Skill', 'Type', 'Status', 'Deadline', 'Manager Approved'];

    let csv = this._csvRow(headers);
    for (const idp of idps) {
      const emp = emps.find(e => e.id === idp.employeeId);
      const targetRole = ROLES.find(r => r.id === idp.targetRoleId);
      for (const action of idp.actions) {
        const skill = SKILLS.find(s => s.id === action.skillId);
        csv += this._csvRow([
          emp ? emp.name : idp.employeeId,
          targetRole ? targetRole.name : idp.targetRoleId,
          idp.status,
          action.title,
          skill ? skill.name : action.skillId,
          action.type,
          action.status,
          action.deadline || '',
          action.managerApproved ? 'Yes' : 'No'
        ]);
      }
    }
    this._download(csv, `ceps_hr_development_plans_${this._dateStr()}.csv`, 'text/csv');
  },

  exportFeedbackCSV() {
    const feedback = HRStore.getFeedback();
    const emps = HRStore.getEmployees();
    const headers = ['Date', 'Employee', 'Author', 'Role', 'Type', 'Skill', 'Content'];

    let csv = this._csvRow(headers);
    for (const fb of feedback) {
      const emp = emps.find(e => e.id === fb.employeeId);
      const author = emps.find(e => e.id === fb.authorId);
      const skill = fb.skillId ? SKILLS.find(s => s.id === fb.skillId) : null;
      csv += this._csvRow([
        fb.date,
        emp ? emp.name : fb.employeeId,
        author ? author.name : fb.authorId,
        fb.authorRole,
        fb.type,
        skill ? skill.name : 'General',
        fb.content
      ]);
    }
    this._download(csv, `ceps_hr_feedback_${this._dateStr()}.csv`, 'text/csv');
  },

  exportAuditLogCSV() {
    const log = HRStore.getAuditLog();
    const emps = HRStore.getEmployees();
    const headers = ['Timestamp', 'User', 'Action', 'Target Employee', 'Details'];

    let csv = this._csvRow(headers);
    for (const entry of log) {
      const user = emps.find(e => e.id === entry.userId);
      const target = emps.find(e => e.id === entry.targetEmployeeId);
      csv += this._csvRow([
        entry.timestamp,
        user ? user.name : entry.userId,
        entry.action,
        target ? target.name : entry.targetEmployeeId,
        JSON.stringify(entry.details || {})
      ]);
    }
    this._download(csv, `ceps_hr_audit_log_${this._dateStr()}.csv`, 'text/csv');
  },

  // ── Goals CSV (v3) ───────────────────────────────────────────────────
  exportGoalsCSV() {
    const goals = HRStore.getGoals();
    const emps = HRStore.getEmployees();
    const headers = ['Employee', 'Title', 'Description', 'Deadline', 'Status', 'Linked Skill', 'Manager Approved', 'Created'];
    let csv = this._csvRow(headers);
    for (const g of goals) {
      const emp = emps.find(e => e.id === g.employeeId);
      const skill = g.linkedSkillId ? SKILLS.find(s => s.id === g.linkedSkillId) : null;
      csv += this._csvRow([
        emp ? emp.name : g.employeeId, g.title, g.description,
        g.deadline || '', g.status, skill ? skill.name : '',
        g.managerApproved ? 'Yes' : 'No', g.createdDate || ''
      ]);
    }
    this._download(csv, `ceps_hr_goals_${this._dateStr()}.csv`, 'text/csv');
  },

  // ── Training Requests CSV (v3) ─────────────────────────────────────
  exportTrainingRequestsCSV() {
    const reqs = HRStore.getTrainingRequests();
    const emps = HRStore.getEmployees();
    const headers = ['Employee', 'Title', 'Type', 'Est. Cost', 'Duration', 'Skill', 'Status', 'Request Date', 'Resolved By', 'Manager Comment'];
    let csv = this._csvRow(headers);
    for (const r of reqs) {
      const emp = emps.find(e => e.id === r.employeeId);
      const resolver = r.resolvedBy ? emps.find(e => e.id === r.resolvedBy) : null;
      const skill = r.linkedSkillId ? SKILLS.find(s => s.id === r.linkedSkillId) : null;
      csv += this._csvRow([
        emp ? emp.name : r.employeeId, r.title, r.type,
        r.estimatedCost || 0, r.estimatedDuration || '',
        skill ? skill.name : '', r.status, r.requestDate || '',
        resolver ? resolver.name : '', r.managerComment || ''
      ]);
    }
    this._download(csv, `ceps_hr_training_requests_${this._dateStr()}.csv`, 'text/csv');
  },

  // ── Import ────────────────────────────────────────────────────────────
  importJSON(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result);
          HRStore.importAll(data);
          resolve(data);
        } catch (err) {
          reject(new Error('Invalid JSON file: ' + err.message));
        }
      };
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  },

  // ── Helpers ───────────────────────────────────────────────────────────
  _dateStr() {
    return new Date().toISOString().split('T')[0];
  },

  _csvRow(fields) {
    return fields.map(f => {
      const s = String(f).replace(/"/g, '""');
      return s.includes(',') || s.includes('"') || s.includes('\n') ? `"${s}"` : s;
    }).join(',') + '\n';
  }
};
