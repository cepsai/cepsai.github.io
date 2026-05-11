// ── HR Data: Employees, Action Library, Feedback seed data ──────────────────
// This file extends the SKILLS/ROLES/ASSESSMENT defined in skills_matrix.html

// Skill ID lookup helper for ASSESSMENT entries with null skillId
const SKILL_NAME_MAP = {
  "Making an impact": "making_impact",
  "Knowing oneself": "kwowing_onseself",
  "Working in teams": "work_in_teams"
};

// ── EMPLOYEES seed data ─────────────────────────────────────────────────────
const SEED_EMPLOYEES = [
  // Migrated from ASSESSMENT
  {
    id: "emp_001", name: "John Doe", email: "john.doe@ceps.eu",
    currentRoleId: "researcher", managerId: "emp_003", unit: "Economic Policy",
    startDate: "2023-06-01",
    skills: {
      funding_income_generation: { level: "L1", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      project_management:        { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      disciplinary_expertise:    { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      research_methodology:      { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      writing:                   { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      making_impact:             { level: "L3", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      cognitive_thinking:        { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      developing_oneself:        { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      kwowing_onseself:          { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L3", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" }
    },
    targetRoleId: "research_fellow", targetRoleValidated: false
  },
  {
    id: "emp_002", name: "Clara Santa", email: "clara.santa@ceps.eu",
    currentRoleId: "researcher", managerId: "emp_003", unit: "Economic Policy",
    startDate: "2024-01-15",
    skills: {
      funding_income_generation: { level: "L1", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      project_management:        { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      disciplinary_expertise:    { level: "L1", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      research_methodology:      { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      writing:                   { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      making_impact:             { level: "L1", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      cognitive_thinking:        { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      developing_oneself:        { level: "L1", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      kwowing_onseself:          { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" }
    },
    targetRoleId: "research_fellow", targetRoleValidated: false
  },
  {
    id: "emp_003", name: "Josey Dorsey", email: "josey.dorsey@ceps.eu",
    currentRoleId: "research_fellow", managerId: "emp_006", unit: "Economic Policy",
    startDate: "2020-09-01",
    skills: {
      funding_income_generation: { level: "L2", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" },
      project_management:        { level: "L1", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" },
      disciplinary_expertise:    { level: "L3", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" },
      research_methodology:      { level: "L2", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" },
      writing:                   { level: "L3", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" },
      making_impact:             { level: "L3", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" },
      cognitive_thinking:        { level: "L3", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" },
      developing_oneself:        { level: "L3", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" },
      kwowing_onseself:          { level: "L3", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" },
      team_leadership:           { level: "L2", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" },
      work_in_teams:             { level: "L3", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" }
    },
    targetRoleId: "head_of_program", targetRoleValidated: true
  },
  // Additional demo employees
  {
    id: "emp_004", name: "Anna Bergström", email: "anna.bergstrom@ceps.eu",
    currentRoleId: "research_assistant", managerId: "emp_003", unit: "Digital Policy",
    startDate: "2025-02-01",
    skills: {
      funding_income_generation: { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      project_management:        { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      disciplinary_expertise:    { level: "L1", assessedBy: "emp_003", assessedDate: "2025-06-01", evidence: "" },
      research_methodology:      { level: "L1", assessedBy: "emp_003", assessedDate: "2025-06-01", evidence: "" },
      writing:                   { level: "L1", assessedBy: "emp_003", assessedDate: "2025-06-01", evidence: "" },
      making_impact:             { level: "L1", assessedBy: "emp_003", assessedDate: "2025-06-01", evidence: "" },
      cognitive_thinking:        { level: "L1", assessedBy: "emp_003", assessedDate: "2025-06-01", evidence: "" },
      developing_oneself:        { level: "L1", assessedBy: "emp_003", assessedDate: "2025-06-01", evidence: "" },
      kwowing_onseself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L1", assessedBy: "emp_003", assessedDate: "2025-06-01", evidence: "" }
    },
    targetRoleId: "researcher", targetRoleValidated: true
  },
  {
    id: "emp_005", name: "Marco Rossi", email: "marco.rossi@ceps.eu",
    currentRoleId: "researcher", managerId: "emp_007", unit: "Energy & Climate",
    startDate: "2022-03-15",
    skills: {
      funding_income_generation: { level: "L2", assessedBy: "emp_007", assessedDate: "2025-10-01", evidence: "" },
      project_management:        { level: "L2", assessedBy: "emp_007", assessedDate: "2025-10-01", evidence: "" },
      disciplinary_expertise:    { level: "L2", assessedBy: "emp_007", assessedDate: "2025-10-01", evidence: "" },
      research_methodology:      { level: "L2", assessedBy: "emp_007", assessedDate: "2025-10-01", evidence: "" },
      writing:                   { level: "L2", assessedBy: "emp_007", assessedDate: "2025-10-01", evidence: "" },
      making_impact:             { level: "L2", assessedBy: "emp_007", assessedDate: "2025-10-01", evidence: "" },
      cognitive_thinking:        { level: "L2", assessedBy: "emp_007", assessedDate: "2025-10-01", evidence: "" },
      developing_oneself:        { level: "L2", assessedBy: "emp_007", assessedDate: "2025-10-01", evidence: "" },
      kwowing_onseself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L2", assessedBy: "emp_007", assessedDate: "2025-10-01", evidence: "" }
    },
    targetRoleId: "research_fellow", targetRoleValidated: true
  },
  {
    id: "emp_006", name: "Sophie Laurent", email: "sophie.laurent@ceps.eu",
    currentRoleId: "head_of_program", managerId: "emp_008", unit: "Economic Policy",
    startDate: "2015-05-01",
    skills: {
      funding_income_generation: { level: "L3", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      project_management:        { level: "L3", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      disciplinary_expertise:    { level: "L3", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      research_methodology:      { level: "L4", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      writing:                   { level: "L4", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      making_impact:             { level: "L3", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      cognitive_thinking:        { level: "L4", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      developing_oneself:        { level: "L3", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      kwowing_onseself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: "L3", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      work_in_teams:             { level: "L4", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" }
    },
    targetRoleId: "head_of_unit", targetRoleValidated: true
  },
  {
    id: "emp_007", name: "Peter Müller", email: "peter.mueller@ceps.eu",
    currentRoleId: "research_fellow", managerId: "emp_008", unit: "Energy & Climate",
    startDate: "2018-11-01",
    skills: {
      funding_income_generation: { level: "L2", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      project_management:        { level: "L2", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      disciplinary_expertise:    { level: "L3", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      research_methodology:      { level: "L3", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      writing:                   { level: "L2", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      making_impact:             { level: "L2", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      cognitive_thinking:        { level: "L3", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      developing_oneself:        { level: "L2", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      kwowing_onseself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: "L2", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      work_in_teams:             { level: "L2", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" }
    },
    targetRoleId: "senior_research_fellow", targetRoleValidated: false
  },
  {
    id: "emp_008", name: "Elena Vasquez", email: "elena.vasquez@ceps.eu",
    currentRoleId: "head_of_unit", managerId: null, unit: "All Units",
    startDate: "2010-01-15",
    skills: {
      funding_income_generation: { level: "L4", assessedBy: null, assessedDate: "2025-06-01", evidence: "" },
      project_management:        { level: "L4", assessedBy: null, assessedDate: "2025-06-01", evidence: "" },
      disciplinary_expertise:    { level: "L4", assessedBy: null, assessedDate: "2025-06-01", evidence: "" },
      research_methodology:      { level: "L4", assessedBy: null, assessedDate: "2025-06-01", evidence: "" },
      writing:                   { level: "L4", assessedBy: null, assessedDate: "2025-06-01", evidence: "" },
      making_impact:             { level: "L4", assessedBy: null, assessedDate: "2025-06-01", evidence: "" },
      cognitive_thinking:        { level: "L4", assessedBy: null, assessedDate: "2025-06-01", evidence: "" },
      developing_oneself:        { level: "L4", assessedBy: null, assessedDate: "2025-06-01", evidence: "" },
      kwowing_onseself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: "L4", assessedBy: null, assessedDate: "2025-06-01", evidence: "" },
      work_in_teams:             { level: "L4", assessedBy: null, assessedDate: "2025-06-01", evidence: "" }
    },
    targetRoleId: null, targetRoleValidated: true
  },
  {
    id: "emp_009", name: "Lukas Andersen", email: "lukas.andersen@ceps.eu",
    currentRoleId: "research_assistant", managerId: "emp_007", unit: "Energy & Climate",
    startDate: "2025-09-01",
    skills: {
      funding_income_generation: { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      project_management:        { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      disciplinary_expertise:    { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" },
      research_methodology:      { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" },
      writing:                   { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" },
      making_impact:             { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      cognitive_thinking:        { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" },
      developing_oneself:        { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" },
      kwowing_onseself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" }
    },
    targetRoleId: "researcher", targetRoleValidated: false
  },
  {
    id: "emp_010", name: "Marie Dubois", email: "marie.dubois@ceps.eu",
    currentRoleId: "researcher", managerId: "emp_006", unit: "Economic Policy",
    startDate: "2023-04-01",
    skills: {
      funding_income_generation: { level: "L1", assessedBy: "emp_006", assessedDate: "2025-10-01", evidence: "" },
      project_management:        { level: "L1", assessedBy: "emp_006", assessedDate: "2025-10-01", evidence: "" },
      disciplinary_expertise:    { level: "L2", assessedBy: "emp_006", assessedDate: "2025-10-01", evidence: "" },
      research_methodology:      { level: "L1", assessedBy: "emp_006", assessedDate: "2025-10-01", evidence: "" },
      writing:                   { level: "L2", assessedBy: "emp_006", assessedDate: "2025-10-01", evidence: "" },
      making_impact:             { level: "L1", assessedBy: "emp_006", assessedDate: "2025-10-01", evidence: "" },
      cognitive_thinking:        { level: "L2", assessedBy: "emp_006", assessedDate: "2025-10-01", evidence: "" },
      developing_oneself:        { level: "L1", assessedBy: "emp_006", assessedDate: "2025-10-01", evidence: "" },
      kwowing_onseself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L2", assessedBy: "emp_006", assessedDate: "2025-10-01", evidence: "" }
    },
    targetRoleId: "research_fellow", targetRoleValidated: false
  },
  {
    id: "emp_011", name: "Thomas Weber", email: "thomas.weber@ceps.eu",
    currentRoleId: "research_fellow", managerId: "emp_006", unit: "Economic Policy",
    startDate: "2019-07-01",
    skills: {
      funding_income_generation: { level: "L2", assessedBy: "emp_006", assessedDate: "2025-09-01", evidence: "" },
      project_management:        { level: "L3", assessedBy: "emp_006", assessedDate: "2025-09-01", evidence: "" },
      disciplinary_expertise:    { level: "L3", assessedBy: "emp_006", assessedDate: "2025-09-01", evidence: "" },
      research_methodology:      { level: "L3", assessedBy: "emp_006", assessedDate: "2025-09-01", evidence: "" },
      writing:                   { level: "L3", assessedBy: "emp_006", assessedDate: "2025-09-01", evidence: "" },
      making_impact:             { level: "L3", assessedBy: "emp_006", assessedDate: "2025-09-01", evidence: "" },
      cognitive_thinking:        { level: "L3", assessedBy: "emp_006", assessedDate: "2025-09-01", evidence: "" },
      developing_oneself:        { level: "L3", assessedBy: "emp_006", assessedDate: "2025-09-01", evidence: "" },
      kwowing_onseself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: "L2", assessedBy: "emp_006", assessedDate: "2025-09-01", evidence: "" },
      work_in_teams:             { level: "L3", assessedBy: "emp_006", assessedDate: "2025-09-01", evidence: "" }
    },
    targetRoleId: "head_of_program", targetRoleValidated: true
  },
  {
    id: "emp_012", name: "Katarina Novak", email: "katarina.novak@ceps.eu",
    currentRoleId: "researcher", managerId: "emp_007", unit: "Energy & Climate",
    startDate: "2024-06-01",
    skills: {
      funding_income_generation: { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" },
      project_management:        { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" },
      disciplinary_expertise:    { level: "L2", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" },
      research_methodology:      { level: "L2", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" },
      writing:                   { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" },
      making_impact:             { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" },
      cognitive_thinking:        { level: "L2", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" },
      developing_oneself:        { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" },
      kwowing_onseself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" }
    },
    targetRoleId: "research_fellow", targetRoleValidated: false
  }
];

// ── ACTION LIBRARY ──────────────────────────────────────────────────────────
// Predefined development actions mapped to skill level transitions
const ACTION_LIBRARY = [
  // Funding & income generation
  { id:"lib_001", skillId:"funding_income_generation", fromLevel:"L1", toLevel:"L2", type:"training", title:"Grant Writing Workshop", description:"Intensive 3-day workshop on identifying funding sources and writing successful grant proposals for EU research programmes.", duration:"3 days", provider:"internal" },
  { id:"lib_002", skillId:"funding_income_generation", fromLevel:"L1", toLevel:"L2", type:"mentoring", title:"Funding Mentor Pairing", description:"6-month mentoring relationship with a senior researcher experienced in securing Horizon Europe and national grants.", duration:"6 months", provider:"internal" },
  { id:"lib_003", skillId:"funding_income_generation", fromLevel:"L2", toLevel:"L3", type:"project", title:"Lead a Grant Application", description:"Take the lead on a medium-scale grant application (€200K-500K) with guidance from a senior colleague.", duration:"3 months", provider:"internal" },
  { id:"lib_004", skillId:"funding_income_generation", fromLevel:"L2", toLevel:"L3", type:"training", title:"Budget Planning & Financial Management", description:"Training on research budget planning, financial reporting, and resource management for project leads.", duration:"2 days", provider:"external" },
  { id:"lib_005", skillId:"funding_income_generation", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Strategic Funding Portfolio Development", description:"Develop a multi-year funding strategy for your unit including diversification of funding sources.", duration:"6 months", provider:"internal" },
  { id:"lib_006", skillId:"funding_income_generation", fromLevel:"L3", toLevel:"L4", type:"project", title:"Lead a Consortium Application", description:"Lead a large-scale international consortium grant application (€1M+).", duration:"6 months", provider:"internal" },

  // Project Management
  { id:"lib_007", skillId:"project_management", fromLevel:"L1", toLevel:"L2", type:"training", title:"Project Management Fundamentals", description:"Introduction to project management tools, timelines, deliverables, and risk management for research projects.", duration:"2 days", provider:"external" },
  { id:"lib_008", skillId:"project_management", fromLevel:"L1", toLevel:"L2", type:"stretch", title:"Co-lead a Research Project", description:"Take co-leadership responsibility for a small research project, managing timelines and deliverables.", duration:"4 months", provider:"internal" },
  { id:"lib_009", skillId:"project_management", fromLevel:"L2", toLevel:"L3", type:"training", title:"Advanced Project Management", description:"Advanced techniques for managing multiple projects, stakeholder management, and strategic alignment.", duration:"3 days", provider:"external" },
  { id:"lib_010", skillId:"project_management", fromLevel:"L2", toLevel:"L3", type:"project", title:"Manage a Cross-Unit Project", description:"Lead a project that involves collaboration across two or more CEPS units.", duration:"6 months", provider:"internal" },
  { id:"lib_011", skillId:"project_management", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Design Project Governance Framework", description:"Design and implement a project governance structure for large interdisciplinary initiatives.", duration:"3 months", provider:"internal" },

  // Disciplinary expertise
  { id:"lib_012", skillId:"disciplinary_expertise", fromLevel:"L1", toLevel:"L2", type:"training", title:"EU Policy Research Methods Course", description:"Deep-dive course covering EU institutional landscape, policy analysis, and evidence-based research techniques.", duration:"1 week", provider:"external" },
  { id:"lib_013", skillId:"disciplinary_expertise", fromLevel:"L1", toLevel:"L2", type:"self-study", title:"Literature Review Deep Dive", description:"Conduct a comprehensive literature review in your specific policy area and present findings to the team.", duration:"2 months", provider:"internal" },
  { id:"lib_014", skillId:"disciplinary_expertise", fromLevel:"L2", toLevel:"L3", type:"mentoring", title:"Senior Researcher Mentoring", description:"6-month structured mentoring with a Senior Research Fellow to deepen domain expertise.", duration:"6 months", provider:"internal" },
  { id:"lib_015", skillId:"disciplinary_expertise", fromLevel:"L2", toLevel:"L3", type:"project", title:"Lead a Policy Paper", description:"Author a major CEPS policy paper demonstrating original contributions to the field.", duration:"3 months", provider:"internal" },
  { id:"lib_016", skillId:"disciplinary_expertise", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Establish New Research Stream", description:"Identify and establish a new research area or programme at CEPS, positioning yourself as a thought leader.", duration:"12 months", provider:"internal" },

  // Research methodology
  { id:"lib_017", skillId:"research_methodology", fromLevel:"L1", toLevel:"L2", type:"training", title:"Applied Research Methods", description:"Hands-on training in quantitative and qualitative research methods for policy analysis.", duration:"5 days", provider:"external" },
  { id:"lib_018", skillId:"research_methodology", fromLevel:"L1", toLevel:"L2", type:"self-study", title:"Data Analysis Skills Development", description:"Self-paced learning in statistical analysis tools (R, Stata, or Python) with weekly check-ins.", duration:"3 months", provider:"internal" },
  { id:"lib_019", skillId:"research_methodology", fromLevel:"L2", toLevel:"L3", type:"training", title:"Advanced Econometrics & Policy Evaluation", description:"Summer school on causal inference, impact evaluation, and advanced econometric techniques.", duration:"2 weeks", provider:"external" },
  { id:"lib_020", skillId:"research_methodology", fromLevel:"L2", toLevel:"L3", type:"project", title:"Design and Lead a Research Study", description:"Independently design and execute a research study with novel methodological approach.", duration:"6 months", provider:"internal" },
  { id:"lib_021", skillId:"research_methodology", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Develop Methodological Innovation", description:"Create or adapt a new research framework or methodology that can be adopted by the team.", duration:"6 months", provider:"internal" },

  // Writing
  { id:"lib_022", skillId:"writing", fromLevel:"L1", toLevel:"L2", type:"training", title:"Academic Writing for Policy", description:"Workshop on structuring research reports, policy briefs, and academic publications for different audiences.", duration:"3 days", provider:"internal" },
  { id:"lib_023", skillId:"writing", fromLevel:"L1", toLevel:"L2", type:"mentoring", title:"Writing Mentor Programme", description:"Paired with a senior writer who reviews and provides feedback on your drafts over 4 months.", duration:"4 months", provider:"internal" },
  { id:"lib_024", skillId:"writing", fromLevel:"L2", toLevel:"L3", type:"project", title:"Lead Author on Major Report", description:"Serve as lead author on a comprehensive CEPS report, managing the editorial process.", duration:"4 months", provider:"internal" },
  { id:"lib_025", skillId:"writing", fromLevel:"L2", toLevel:"L3", type:"training", title:"Strategic Communication Writing", description:"Advanced course on adapting complex policy topics for media, policymakers, and public audiences.", duration:"2 days", provider:"external" },
  { id:"lib_026", skillId:"writing", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Editorial Leadership", description:"Take editorial responsibility for CEPS publication standards, mentoring junior writers.", duration:"ongoing", provider:"internal" },

  // Making impact
  { id:"lib_027", skillId:"making_impact", fromLevel:"L1", toLevel:"L2", type:"training", title:"Policy Communication & Engagement", description:"Workshop on effective presentation at policy events, stakeholder engagement, and media interactions.", duration:"2 days", provider:"internal" },
  { id:"lib_028", skillId:"making_impact", fromLevel:"L1", toLevel:"L2", type:"stretch", title:"Present at External Event", description:"Present research findings at an external policy event or conference.", duration:"1 month prep", provider:"internal" },
  { id:"lib_029", skillId:"making_impact", fromLevel:"L2", toLevel:"L3", type:"project", title:"Build a Stakeholder Network", description:"Develop and maintain relationships with 5+ key policymakers or organisations in your research area.", duration:"6 months", provider:"internal" },
  { id:"lib_030", skillId:"making_impact", fromLevel:"L2", toLevel:"L3", type:"training", title:"Media Training", description:"Professional media training covering interviews, op-eds, and social media for research dissemination.", duration:"1 day", provider:"external" },
  { id:"lib_031", skillId:"making_impact", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Strategic Engagement Leadership", description:"Lead CEPS engagement strategy for a major policy dossier, coordinating with EU institutions.", duration:"12 months", provider:"internal" },

  // Cognitive thinking
  { id:"lib_032", skillId:"cognitive_thinking", fromLevel:"L1", toLevel:"L2", type:"training", title:"Critical Thinking & Analysis", description:"Workshop developing skills in logical reasoning, evidence evaluation, and creative problem-solving.", duration:"2 days", provider:"external" },
  { id:"lib_033", skillId:"cognitive_thinking", fromLevel:"L1", toLevel:"L2", type:"self-study", title:"Cross-Disciplinary Reading Programme", description:"Structured reading programme covering adjacent policy fields to broaden analytical perspective.", duration:"3 months", provider:"internal" },
  { id:"lib_034", skillId:"cognitive_thinking", fromLevel:"L2", toLevel:"L3", type:"stretch", title:"Lead an Interdisciplinary Analysis", description:"Design and lead a research initiative that integrates perspectives from multiple disciplines.", duration:"6 months", provider:"internal" },
  { id:"lib_035", skillId:"cognitive_thinking", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Strategic Foresight Exercise", description:"Lead a strategic foresight exercise identifying emerging trends and their policy implications.", duration:"3 months", provider:"internal" },

  // Developing oneself
  { id:"lib_036", skillId:"developing_oneself", fromLevel:"L1", toLevel:"L2", type:"mentoring", title:"Career Development Mentoring", description:"Structured mentoring focused on career goals, professional network building, and skill planning.", duration:"6 months", provider:"internal" },
  { id:"lib_037", skillId:"developing_oneself", fromLevel:"L1", toLevel:"L2", type:"self-study", title:"Professional Development Plan", description:"Create and execute a personal development plan with quarterly milestones and self-assessment.", duration:"12 months", provider:"internal" },
  { id:"lib_038", skillId:"developing_oneself", fromLevel:"L2", toLevel:"L3", type:"stretch", title:"Become a Mentor", description:"Mentor a junior colleague, developing coaching skills while supporting others' growth.", duration:"6 months", provider:"internal" },
  { id:"lib_039", skillId:"developing_oneself", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Innovation Champion", description:"Challenge and improve existing processes within your unit, driving constructive change.", duration:"ongoing", provider:"internal" },

  // Team leadership
  { id:"lib_040", skillId:"team_leadership", fromLevel:"L1", toLevel:"L2", type:"training", title:"Leadership Fundamentals", description:"Training on delegation, goal-setting, conflict resolution, and motivating team members.", duration:"3 days", provider:"external" },
  { id:"lib_041", skillId:"team_leadership", fromLevel:"L1", toLevel:"L2", type:"stretch", title:"Lead a Small Project Team", description:"Take leadership of a 2-3 person project team with full responsibility for coordination and delivery.", duration:"4 months", provider:"internal" },
  { id:"lib_042", skillId:"team_leadership", fromLevel:"L2", toLevel:"L3", type:"training", title:"Advanced Leadership & Team Dynamics", description:"Workshop on situational leadership, team performance management, and coaching techniques.", duration:"2 days", provider:"external" },
  { id:"lib_043", skillId:"team_leadership", fromLevel:"L2", toLevel:"L3", type:"project", title:"Lead a Cross-Functional Research Team", description:"Lead a research team of 4+ people across different specialisations.", duration:"6 months", provider:"internal" },
  { id:"lib_044", skillId:"team_leadership", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Organisational Leadership", description:"Take responsibility for unit-level strategic decisions, staff development, and performance management.", duration:"12 months", provider:"internal" },

  // Work in teams
  { id:"lib_045", skillId:"work_in_teams", fromLevel:"L1", toLevel:"L2", type:"training", title:"Effective Collaboration Workshop", description:"Skills for productive teamwork: communication, feedback, time management, and conflict resolution.", duration:"1 day", provider:"internal" },
  { id:"lib_046", skillId:"work_in_teams", fromLevel:"L1", toLevel:"L2", type:"stretch", title:"Cross-Unit Collaboration", description:"Participate actively in a project with a different CEPS unit to broaden teamwork experience.", duration:"3 months", provider:"internal" },
  { id:"lib_047", skillId:"work_in_teams", fromLevel:"L2", toLevel:"L3", type:"stretch", title:"Team Culture Initiative", description:"Lead an initiative to improve team dynamics, inclusion, or collaboration practices within your unit.", duration:"3 months", provider:"internal" },
  { id:"lib_048", skillId:"work_in_teams", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Organisational Culture Ambassador", description:"Drive organisation-wide culture improvement initiatives and model exemplary collaborative behaviour.", duration:"ongoing", provider:"internal" }
];

// ── SEED FEEDBACK ───────────────────────────────────────────────────────────
const SEED_FEEDBACK = [
  { id:"fb_001", employeeId:"emp_001", authorId:"emp_003", authorRole:"manager", date:"2026-02-15", skillId:"making_impact", type:"positive", content:"Excellent presentation at the EU Digital Policy Forum. Your ability to translate complex research into actionable policy recommendations was very well received by the audience.", visibility:"employee_manager" },
  { id:"fb_002", employeeId:"emp_001", authorId:"emp_003", authorRole:"manager", date:"2026-01-20", skillId:"writing", type:"developmental", content:"The latest policy brief needs more structured argumentation. Consider using the CEPS template for better flow. Happy to review your next draft together.", visibility:"employee_manager" },
  { id:"fb_003", employeeId:"emp_002", authorId:"emp_003", authorRole:"manager", date:"2026-03-01", skillId:"disciplinary_expertise", type:"developmental", content:"To progress from L1 to L2 in disciplinary expertise, I'd recommend deepening your knowledge of EU competition policy frameworks. The upcoming CEPS workshop would be a good start.", visibility:"employee_manager" },
  { id:"fb_004", employeeId:"emp_005", authorId:"emp_007", authorRole:"manager", date:"2026-02-28", skillId:null, type:"positive", content:"Great teamwork on the energy transition report. You coordinated well with the external partners and kept the project on track.", visibility:"employee_manager" },
  { id:"fb_005", employeeId:"emp_003", authorId:"emp_006", authorRole:"manager", date:"2026-01-10", skillId:"project_management", type:"developmental", content:"Your project management skills need attention — the last two deliverables were submitted late. Let's work on a structured project plan with clear milestones.", visibility:"employee_manager" },
  { id:"fb_006", employeeId:"emp_004", authorId:"emp_003", authorRole:"manager", date:"2026-03-10", skillId:"research_methodology", type:"positive", content:"Good progress on learning quantitative methods. Your data analysis in the latest report shows clear improvement.", visibility:"employee_manager" },
  { id:"fb_007", employeeId:"emp_001", authorId:"emp_002", authorRole:"peer", date:"2026-03-05", skillId:"work_in_teams", type:"positive", content:"Really appreciate how you always make time to help with data questions. Great team spirit!", visibility:"employee_manager" }
];

// ── SEED DEVELOPMENT PLANS ──────────────────────────────────────────────────
const SEED_IDPS = [
  {
    id: "idp_001", employeeId: "emp_001", targetRoleId: "research_fellow",
    createdDate: "2026-01-15", status: "active",
    actions: [
      { id:"act_001", skillId:"funding_income_generation", fromLevel:"L1", toLevel:"L2", type:"training", title:"Grant Writing Workshop", description:"Intensive 3-day workshop on identifying funding sources and writing successful grant proposals.", source:"library", deadline:"2026-06-30", status:"in_progress", managerApproved:true, completedDate:null, notes:"Enrolled in April session" },
      { id:"act_002", skillId:"disciplinary_expertise", fromLevel:"L2", toLevel:"L3", type:"mentoring", title:"Senior Researcher Mentoring", description:"6-month structured mentoring with Dr. Laurent.", source:"library", deadline:"2026-09-30", status:"not_started", managerApproved:true, completedDate:null, notes:"" }
    ],
    reviewDates: ["2026-04-01", "2026-07-01", "2026-10-01"],
    managerNotes: "Good trajectory. Focus on funding skills first.",
    lastReviewDate: "2026-01-15"
  },
  {
    id: "idp_002", employeeId: "emp_005", targetRoleId: "research_fellow",
    createdDate: "2026-02-01", status: "active",
    actions: [
      { id:"act_003", skillId:"writing", fromLevel:"L2", toLevel:"L3", type:"training", title:"Strategic Communication Writing", description:"Advanced course on adapting complex policy topics for different audiences.", source:"library", deadline:"2026-05-30", status:"completed", managerApproved:true, completedDate:"2026-03-15", notes:"Completed successfully" },
      { id:"act_004", skillId:"making_impact", fromLevel:"L2", toLevel:"L3", type:"stretch", title:"Present at External Event", description:"Present at the upcoming EU Energy Forum.", source:"library", deadline:"2026-07-15", status:"in_progress", managerApproved:true, completedDate:null, notes:"Accepted as panelist" }
    ],
    reviewDates: ["2026-05-01", "2026-08-01"],
    managerNotes: "Strong candidate for promotion. Writing skills improving fast.",
    lastReviewDate: "2026-02-01"
  }
];
