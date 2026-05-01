// ── HR Storage: localStorage abstraction with audit logging ─────────────────

const HRStore = {
  KEYS: {
    employees:     'ceps_hr2_employees',
    idps:          'ceps_hr2_idps',
    feedback:      'ceps_hr2_feedback',
    actionLibrary: 'ceps_hr2_action_library',
    auditLog:      'ceps_hr2_audit_log',
    currentUser:   'ceps_hr2_current_user',
    settings:      'ceps_hr2_settings',
    initialized:   'ceps_hr2_initialized'
  },

  // ── Core CRUD ─────────────────────────────────────────────────────────
  load(key) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      console.error('HRStore.load error:', key, e);
      return null;
    }
  },

  save(key, data) {
    try {
      localStorage.setItem(key, JSON.stringify(data));
      return true;
    } catch (e) {
      console.error('HRStore.save error:', key, e);
      return false;
    }
  },

  // ── Entity helpers ────────────────────────────────────────────────────
  getEmployees()    { return this.load(this.KEYS.employees) || []; },
  getIDPs()         { return this.load(this.KEYS.idps) || []; },
  getFeedback()     { return this.load(this.KEYS.feedback) || []; },
  getActionLibrary(){ return this.load(this.KEYS.actionLibrary) || []; },
  getAuditLog()     { return this.load(this.KEYS.auditLog) || []; },
  getSettings()     { return this.load(this.KEYS.settings) || { aiEndpoint: 'http://localhost:11434/api/generate', aiModel: 'glm-4.7-flash', aiApiKey: '' }; },

  saveEmployees(data)    { return this.save(this.KEYS.employees, data); },
  saveIDPs(data)         { return this.save(this.KEYS.idps, data); },
  saveFeedback(data)     { return this.save(this.KEYS.feedback, data); },
  saveActionLibrary(data){ return this.save(this.KEYS.actionLibrary, data); },
  saveAuditLog(data)     { return this.save(this.KEYS.auditLog, data); },
  saveSettings(data)     { return this.save(this.KEYS.settings, data); },

  // ── Current user (role switcher state) ────────────────────────────────
  getCurrentUser() {
    return this.load(this.KEYS.currentUser) || { id: 'emp_001', name: 'John Doe', viewRole: 'employee' };
  },
  setCurrentUser(user) {
    this.save(this.KEYS.currentUser, user);
  },

  // ── Employee CRUD ─────────────────────────────────────────────────────
  getEmployee(id) {
    return this.getEmployees().find(e => e.id === id) || null;
  },

  updateEmployee(id, updates) {
    const emps = this.getEmployees();
    const idx = emps.findIndex(e => e.id === id);
    if (idx === -1) return false;
    emps[idx] = { ...emps[idx], ...updates, updatedAt: new Date().toISOString() };
    this.saveEmployees(emps);
    return true;
  },

  updateEmployeeSkill(empId, skillId, level, assessedBy) {
    const emps = this.getEmployees();
    const emp = emps.find(e => e.id === empId);
    if (!emp) return false;
    if (!emp.skills) emp.skills = {};
    emp.skills[skillId] = {
      level: level,
      assessedBy: assessedBy,
      assessedDate: new Date().toISOString().split('T')[0],
      evidence: emp.skills[skillId]?.evidence || ''
    };
    emp.updatedAt = new Date().toISOString();
    this.saveEmployees(emps);
    this.audit('skill_assessed', assessedBy, empId, { skillId, newLevel: level });
    return true;
  },

  setTargetRole(empId, roleId) {
    const emps = this.getEmployees();
    const emp = emps.find(e => e.id === empId);
    if (!emp) return false;
    emp.targetRoleId = roleId;
    emp.targetRoleValidated = false;
    emp.updatedAt = new Date().toISOString();
    this.saveEmployees(emps);
    this.audit('target_role_changed', empId, empId, { newTargetRole: roleId });
    return true;
  },

  validateTargetRole(empId, managerId) {
    const emps = this.getEmployees();
    const emp = emps.find(e => e.id === empId);
    if (!emp) return false;
    emp.targetRoleValidated = true;
    emp.updatedAt = new Date().toISOString();
    this.saveEmployees(emps);
    this.audit('target_role_validated', managerId, empId, { targetRole: emp.targetRoleId });
    return true;
  },

  // ── IDP CRUD ──────────────────────────────────────────────────────────
  getIDP(empId) {
    return this.getIDPs().find(i => i.employeeId === empId && i.status === 'active') || null;
  },

  createIDP(empId, targetRoleId) {
    const idps = this.getIDPs();
    const id = 'idp_' + Date.now();
    const idp = {
      id, employeeId: empId, targetRoleId,
      createdDate: new Date().toISOString().split('T')[0],
      status: 'active', actions: [],
      reviewDates: [], managerNotes: '', lastReviewDate: null
    };
    idps.push(idp);
    this.saveIDPs(idps);
    this.audit('idp_created', empId, empId, { idpId: id, targetRoleId });
    return idp;
  },

  addIDPAction(empId, action) {
    const idps = this.getIDPs();
    const idp = idps.find(i => i.employeeId === empId && i.status === 'active');
    if (!idp) return false;
    action.id = action.id || ('act_' + Date.now());
    action.status = action.status || 'not_started';
    action.managerApproved = action.managerApproved || false;
    action.completedDate = null;
    action.notes = action.notes || '';
    idp.actions.push(action);
    this.saveIDPs(idps);
    this.audit('idp_action_added', empId, empId, { actionTitle: action.title, skillId: action.skillId });
    return true;
  },

  updateIDPActionStatus(empId, actionId, newStatus) {
    const idps = this.getIDPs();
    const idp = idps.find(i => i.employeeId === empId && i.status === 'active');
    if (!idp) return false;
    const action = idp.actions.find(a => a.id === actionId);
    if (!action) return false;
    action.status = newStatus;
    if (newStatus === 'completed') action.completedDate = new Date().toISOString().split('T')[0];
    this.saveIDPs(idps);
    this.audit('idp_action_status_changed', empId, empId, { actionId, newStatus });
    return true;
  },

  approveIDPAction(empId, actionId, managerId) {
    const idps = this.getIDPs();
    const idp = idps.find(i => i.employeeId === empId && i.status === 'active');
    if (!idp) return false;
    const action = idp.actions.find(a => a.id === actionId);
    if (!action) return false;
    action.managerApproved = true;
    this.saveIDPs(idps);
    this.audit('idp_action_approved', managerId, empId, { actionId });
    return true;
  },

  removeIDPAction(empId, actionId) {
    const idps = this.getIDPs();
    const idp = idps.find(i => i.employeeId === empId && i.status === 'active');
    if (!idp) return false;
    idp.actions = idp.actions.filter(a => a.id !== actionId);
    this.saveIDPs(idps);
    return true;
  },

  // ── Feedback CRUD ─────────────────────────────────────────────────────
  addFeedback(fb) {
    const all = this.getFeedback();
    fb.id = fb.id || ('fb_' + Date.now());
    fb.date = fb.date || new Date().toISOString().split('T')[0];
    all.push(fb);
    this.saveFeedback(all);
    this.audit('feedback_given', fb.authorId, fb.employeeId, { type: fb.type, skillId: fb.skillId });
    return fb;
  },

  getEmployeeFeedback(empId) {
    return this.getFeedback().filter(f => f.employeeId === empId);
  },

  // ── Audit log ─────────────────────────────────────────────────────────
  audit(action, userId, targetEmployeeId, details) {
    const log = this.getAuditLog();
    log.push({
      timestamp: new Date().toISOString(),
      userId, action, targetEmployeeId, details
    });
    this.saveAuditLog(log);
  },

  // ── GDPR ──────────────────────────────────────────────────────────────
  exportEmployeeData(empId) {
    const emp = this.getEmployee(empId);
    const idps = this.getIDPs().filter(i => i.employeeId === empId);
    const feedback = this.getFeedback().filter(f => f.employeeId === empId);
    const audit = this.getAuditLog().filter(a => a.targetEmployeeId === empId || a.userId === empId);
    return { employee: emp, developmentPlans: idps, feedback, auditLog: audit };
  },

  deleteEmployee(empId) {
    this.saveEmployees(this.getEmployees().filter(e => e.id !== empId));
    this.saveIDPs(this.getIDPs().filter(i => i.employeeId !== empId));
    this.saveFeedback(this.getFeedback().filter(f => f.employeeId !== empId));
    this.audit('employee_deleted', 'system', empId, {});
  },

  // ── Export / Import all data ──────────────────────────────────────────
  exportAll() {
    return {
      employees: this.getEmployees(),
      idps: this.getIDPs(),
      feedback: this.getFeedback(),
      actionLibrary: this.getActionLibrary(),
      auditLog: this.getAuditLog(),
      settings: this.getSettings(),
      exportDate: new Date().toISOString()
    };
  },

  importAll(data) {
    if (data.employees) this.saveEmployees(data.employees);
    if (data.idps) this.saveIDPs(data.idps);
    if (data.feedback) this.saveFeedback(data.feedback);
    if (data.actionLibrary) this.saveActionLibrary(data.actionLibrary);
    if (data.settings) this.saveSettings(data.settings);
    this.audit('data_imported', 'system', 'system', { date: new Date().toISOString() });
  },

  // ── Initialization ────────────────────────────────────────────────────
  init() {
    const isInit = this.load(this.KEYS.initialized);
    if (!isInit) {
      this.saveEmployees(SEED_EMPLOYEES);
      this.saveActionLibrary(ACTION_LIBRARY);
      this.saveFeedback(SEED_FEEDBACK);
      this.saveIDPs(SEED_IDPS);
      this.saveAuditLog([{
        timestamp: new Date().toISOString(),
        userId: 'system', action: 'system_initialized',
        targetEmployeeId: 'system',
        details: { message: 'System initialized with seed data' }
      }]);
      this.save(this.KEYS.initialized, true);
      console.log('HR System initialized with seed data');
    }
  },

  // ── Reset to seed data ────────────────────────────────────────────────
  reset() {
    Object.values(this.KEYS).forEach(k => localStorage.removeItem(k));
    this.init();
  }
};
