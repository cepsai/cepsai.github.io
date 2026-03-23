// ── HR Storage v3: localStorage abstraction with audit, goals, training requests, backup ──

const HRStore = {
  KEYS: {
    employees:        'ceps_hr3_employees',
    idps:             'ceps_hr3_idps',
    feedback:         'ceps_hr3_feedback',
    actionLibrary:    'ceps_hr3_action_library',
    auditLog:         'ceps_hr3_audit_log',
    currentUser:      'ceps_hr3_current_user',
    settings:         'ceps_hr3_settings',
    initialized:      'ceps_hr3_initialized',
    goals:            'ceps_hr3_goals',
    trainingRequests: 'ceps_hr3_training_requests',
    lastBackup:       'ceps_hr3_last_backup',
    changeCount:      'ceps_hr3_change_count',
    warningShown:     'ceps_hr3_warning_shown'
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
      if (e.name === 'QuotaExceededError') {
        alert('localStorage is full! Please export a backup and consider removing file attachments.');
      }
      return false;
    }
  },

  // ── Entity helpers ────────────────────────────────────────────────────
  getEmployees()       { return this.load(this.KEYS.employees) || []; },
  getIDPs()            { return this.load(this.KEYS.idps) || []; },
  getFeedback()        { return this.load(this.KEYS.feedback) || []; },
  getActionLibrary()   { return this.load(this.KEYS.actionLibrary) || []; },
  getAuditLog()        { return this.load(this.KEYS.auditLog) || []; },
  getGoals()           { return this.load(this.KEYS.goals) || []; },
  getTrainingRequests(){ return this.load(this.KEYS.trainingRequests) || []; },
  getSettings()        { return this.load(this.KEYS.settings) || { aiEndpoint: 'http://localhost:11434/api/generate', aiModel: 'glm-4.7-flash', aiApiKey: '' }; },

  saveEmployees(data)       { return this.save(this.KEYS.employees, data); },
  saveIDPs(data)            { return this.save(this.KEYS.idps, data); },
  saveFeedback(data)        { return this.save(this.KEYS.feedback, data); },
  saveActionLibrary(data)   { return this.save(this.KEYS.actionLibrary, data); },
  saveAuditLog(data)        { return this.save(this.KEYS.auditLog, data); },
  saveGoals(data)           { return this.save(this.KEYS.goals, data); },
  saveTrainingRequests(data){ return this.save(this.KEYS.trainingRequests, data); },
  saveSettings(data)        { return this.save(this.KEYS.settings, data); },

  // ── Current user ──────────────────────────────────────────────────────
  getCurrentUser() {
    return this.load(this.KEYS.currentUser) || { id: 'emp_001', name: 'John Doe', viewRole: 'employee' };
  },
  setCurrentUser(user) { this.save(this.KEYS.currentUser, user); },

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

  // v3: skill history tracking
  updateEmployeeSkill(empId, skillId, level, assessedBy) {
    const emps = this.getEmployees();
    const emp = emps.find(e => e.id === empId);
    if (!emp) return false;
    if (!emp.skills) emp.skills = {};

    const existing = emp.skills[skillId];
    const history = existing?.history || [];

    // Record old level in history if it changed
    if (existing && existing.level && existing.level !== level) {
      history.push({
        level: existing.level,
        assessedBy: existing.assessedBy,
        assessedDate: existing.assessedDate
      });
    }

    emp.skills[skillId] = {
      level,
      assessedBy,
      assessedDate: new Date().toISOString().split('T')[0],
      evidence: existing?.evidence || '',
      history
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
    action.attachments = action.attachments || [];
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
    fb.attachments = fb.attachments || [];
    all.push(fb);
    this.saveFeedback(all);
    this.audit('feedback_given', fb.authorId, fb.employeeId, { type: fb.type, skillId: fb.skillId });
    return fb;
  },

  getEmployeeFeedback(empId) {
    return this.getFeedback().filter(f => f.employeeId === empId);
  },

  // ── Goals CRUD (v3) ───────────────────────────────────────────────────
  getEmployeeGoals(empId) {
    return this.getGoals().filter(g => g.employeeId === empId);
  },

  addGoal(goal) {
    const all = this.getGoals();
    goal.id = goal.id || ('goal_' + Date.now());
    goal.createdDate = goal.createdDate || new Date().toISOString().split('T')[0];
    goal.status = goal.status || 'draft';
    goal.managerApproved = goal.managerApproved || false;
    goal.managerNotes = goal.managerNotes || '';
    all.push(goal);
    this.saveGoals(all);
    this.audit('goal_created', goal.employeeId, goal.employeeId, { title: goal.title });
    return goal;
  },

  updateGoal(goalId, updates) {
    const all = this.getGoals();
    const idx = all.findIndex(g => g.id === goalId);
    if (idx === -1) return false;
    all[idx] = { ...all[idx], ...updates };
    this.saveGoals(all);
    this.audit('goal_updated', updates.approvedBy || all[idx].employeeId, all[idx].employeeId, { goalId, status: all[idx].status });
    return true;
  },

  deleteGoal(goalId) {
    const all = this.getGoals();
    const goal = all.find(g => g.id === goalId);
    this.saveGoals(all.filter(g => g.id !== goalId));
    if (goal) this.audit('goal_deleted', goal.employeeId, goal.employeeId, { goalId });
    return true;
  },

  // ── Training Requests CRUD (v3) ───────────────────────────────────────
  getEmployeeTrainingRequests(empId) {
    return this.getTrainingRequests().filter(r => r.employeeId === empId);
  },

  getTeamTrainingRequests(managerId) {
    const emps = this.getEmployees().filter(e => e.managerId === managerId);
    const empIds = new Set(emps.map(e => e.id));
    return this.getTrainingRequests().filter(r => empIds.has(r.employeeId));
  },

  addTrainingRequest(req) {
    const all = this.getTrainingRequests();
    req.id = req.id || ('treq_' + Date.now());
    req.requestDate = req.requestDate || new Date().toISOString().split('T')[0];
    req.status = req.status || 'pending';
    req.managerComment = req.managerComment || '';
    req.resolvedBy = null;
    req.resolvedDate = null;
    all.push(req);
    this.saveTrainingRequests(all);
    this.audit('training_requested', req.employeeId, req.employeeId, { title: req.title });
    return req;
  },

  resolveTrainingRequest(reqId, status, managerId, comment) {
    const all = this.getTrainingRequests();
    const req = all.find(r => r.id === reqId);
    if (!req) return false;
    req.status = status;
    req.resolvedBy = managerId;
    req.resolvedDate = new Date().toISOString().split('T')[0];
    req.managerComment = comment || '';
    this.saveTrainingRequests(all);
    this.audit('training_request_' + status, managerId, req.employeeId, { reqId, title: req.title });
    return req;
  },

  // ── Action Library management (v3 admin) ──────────────────────────────
  addLibraryItem(item) {
    const lib = this.getActionLibrary();
    item.id = item.id || ('lib_' + Date.now());
    lib.push(item);
    this.saveActionLibrary(lib);
    this.audit('library_item_added', 'system', 'system', { title: item.title });
    return item;
  },

  updateLibraryItem(itemId, updates) {
    const lib = this.getActionLibrary();
    const idx = lib.findIndex(i => i.id === itemId);
    if (idx === -1) return false;
    lib[idx] = { ...lib[idx], ...updates };
    this.saveActionLibrary(lib);
    return true;
  },

  deleteLibraryItem(itemId) {
    this.saveActionLibrary(this.getActionLibrary().filter(i => i.id !== itemId));
    return true;
  },

  // ── Audit log ─────────────────────────────────────────────────────────
  audit(action, userId, targetEmployeeId, details) {
    const log = this.getAuditLog();
    log.push({
      timestamp: new Date().toISOString(),
      userId, action, targetEmployeeId, details
    });
    this.saveAuditLog(log);
    this.incrementChangeCount();
  },

  // ── Backup tracking (v3) ──────────────────────────────────────────────
  incrementChangeCount() {
    const count = (this.load(this.KEYS.changeCount) || 0) + 1;
    this.save(this.KEYS.changeCount, count);
  },

  recordBackup() {
    this.save(this.KEYS.lastBackup, new Date().toISOString());
    this.save(this.KEYS.changeCount, 0);
  },

  getBackupStatus() {
    const lastBackup = this.load(this.KEYS.lastBackup);
    const changesSince = this.load(this.KEYS.changeCount) || 0;
    let daysSince = null;
    if (lastBackup) {
      daysSince = Math.floor((Date.now() - new Date(lastBackup).getTime()) / (86400000));
    }
    return { lastBackup, changesSince, daysSince };
  },

  isWarningShown() { return !!this.load(this.KEYS.warningShown); },
  setWarningShown() { this.save(this.KEYS.warningShown, true); },

  getStorageUsage() {
    let total = 0;
    for (const key of Object.values(this.KEYS)) {
      const item = localStorage.getItem(key);
      if (item) total += item.length * 2; // approximate bytes (UTF-16)
    }
    return total;
  },

  // ── GDPR ──────────────────────────────────────────────────────────────
  exportEmployeeData(empId) {
    const emp = this.getEmployee(empId);
    const idps = this.getIDPs().filter(i => i.employeeId === empId);
    const feedback = this.getFeedback().filter(f => f.employeeId === empId);
    const goals = this.getGoals().filter(g => g.employeeId === empId);
    const requests = this.getTrainingRequests().filter(r => r.employeeId === empId);
    const audit = this.getAuditLog().filter(a => a.targetEmployeeId === empId || a.userId === empId);
    return { employee: emp, developmentPlans: idps, feedback, goals, trainingRequests: requests, auditLog: audit };
  },

  deleteEmployee(empId) {
    this.saveEmployees(this.getEmployees().filter(e => e.id !== empId));
    this.saveIDPs(this.getIDPs().filter(i => i.employeeId !== empId));
    this.saveFeedback(this.getFeedback().filter(f => f.employeeId !== empId));
    this.saveGoals(this.getGoals().filter(g => g.employeeId !== empId));
    this.saveTrainingRequests(this.getTrainingRequests().filter(r => r.employeeId !== empId));
    this.audit('employee_deleted', 'system', empId, {});
  },

  // ── Export / Import ────────────────────────────────────────────────────
  exportAll() {
    return {
      employees: this.getEmployees(),
      idps: this.getIDPs(),
      feedback: this.getFeedback(),
      actionLibrary: this.getActionLibrary(),
      goals: this.getGoals(),
      trainingRequests: this.getTrainingRequests(),
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
    if (data.goals) this.saveGoals(data.goals);
    if (data.trainingRequests) this.saveTrainingRequests(data.trainingRequests);
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
      this.saveGoals(typeof SEED_GOALS !== 'undefined' ? SEED_GOALS : []);
      this.saveTrainingRequests(typeof SEED_TRAINING_REQUESTS !== 'undefined' ? SEED_TRAINING_REQUESTS : []);
      this.saveAuditLog([{
        timestamp: new Date().toISOString(),
        userId: 'system', action: 'system_initialized',
        targetEmployeeId: 'system',
        details: { message: 'System initialized with seed data (v3)' }
      }]);
      this.save(this.KEYS.initialized, true);
      console.log('HR System v3 initialized with seed data');
    }
  },

  reset() {
    Object.values(this.KEYS).forEach(k => localStorage.removeItem(k));
    this.init();
  }
};
