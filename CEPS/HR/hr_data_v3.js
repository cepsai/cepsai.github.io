// ── HR Data v2: Employees, Action Library, Feedback, IDPs ───────────────────
// Enhanced with: gender, demographics, training dates/costs, richer seed data

const SKILL_NAME_MAP = {
  "Making an impact": "making_impact",
  "Knowing oneself": "knowing_oneself",
  "Working in teams": "work_in_teams"
};

// ── EMPLOYEES (v2: added gender, phone, contractType, fte) ──────────────────
const SEED_EMPLOYEES = [
  {
    id: "emp_001", name: "John Doe", email: "john.doe@ceps.eu",
    gender: "male", phone: "+32 2 229 3901", contractType: "permanent", fte: 1.0,
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
      knowing_oneself:          { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L3", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" }
    },
    targetRoleId: "research_fellow", targetRoleValidated: false
  },
  {
    id: "emp_002", name: "Clara Santa", email: "clara.santa@ceps.eu",
    gender: "female", phone: "+32 2 229 3902", contractType: "permanent", fte: 1.0,
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
      knowing_oneself:          { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L2", assessedBy: "emp_003", assessedDate: "2025-12-01", evidence: "" }
    },
    targetRoleId: "research_fellow", targetRoleValidated: false
  },
  {
    id: "emp_003", name: "Josey Dorsey", email: "josey.dorsey@ceps.eu",
    gender: "female", phone: "+32 2 229 3903", contractType: "permanent", fte: 1.0,
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
      knowing_oneself:          { level: "L3", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" },
      team_leadership:           { level: "L2", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" },
      work_in_teams:             { level: "L3", assessedBy: "emp_006", assessedDate: "2025-12-01", evidence: "" }
    },
    targetRoleId: "head_of_program", targetRoleValidated: true
  },
  {
    id: "emp_004", name: "Anna Bergström", email: "anna.bergstrom@ceps.eu",
    gender: "female", phone: "+32 2 229 3904", contractType: "fixed-term", fte: 1.0,
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
      knowing_oneself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L1", assessedBy: "emp_003", assessedDate: "2025-06-01", evidence: "" }
    },
    targetRoleId: "researcher", targetRoleValidated: true
  },
  {
    id: "emp_005", name: "Marco Rossi", email: "marco.rossi@ceps.eu",
    gender: "male", phone: "+32 2 229 3905", contractType: "permanent", fte: 1.0,
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
      knowing_oneself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L2", assessedBy: "emp_007", assessedDate: "2025-10-01", evidence: "" }
    },
    targetRoleId: "research_fellow", targetRoleValidated: true
  },
  {
    id: "emp_006", name: "Sophie Laurent", email: "sophie.laurent@ceps.eu",
    gender: "female", phone: "+32 2 229 3906", contractType: "permanent", fte: 1.0,
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
      knowing_oneself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: "L3", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      work_in_teams:             { level: "L4", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" }
    },
    targetRoleId: "head_of_unit", targetRoleValidated: true
  },
  {
    id: "emp_007", name: "Peter Müller", email: "peter.mueller@ceps.eu",
    gender: "male", phone: "+32 2 229 3907", contractType: "permanent", fte: 1.0,
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
      knowing_oneself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: "L2", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" },
      work_in_teams:             { level: "L2", assessedBy: "emp_008", assessedDate: "2025-09-01", evidence: "" }
    },
    targetRoleId: "senior_research_fellow", targetRoleValidated: false
  },
  {
    id: "emp_008", name: "Elena Vasquez", email: "elena.vasquez@ceps.eu",
    gender: "female", phone: "+32 2 229 3908", contractType: "permanent", fte: 1.0,
    currentRoleId: "head_of_unit", managerId: null, unit: "All Units",
    startDate: "2010-01-15",
    skills: {
      funding_income_generation: { level: "L4", assessedBy: "system", assessedDate: "2025-06-01", evidence: "" },
      project_management:        { level: "L4", assessedBy: "system", assessedDate: "2025-06-01", evidence: "" },
      disciplinary_expertise:    { level: "L4", assessedBy: "system", assessedDate: "2025-06-01", evidence: "" },
      research_methodology:      { level: "L4", assessedBy: "system", assessedDate: "2025-06-01", evidence: "" },
      writing:                   { level: "L4", assessedBy: "system", assessedDate: "2025-06-01", evidence: "" },
      making_impact:             { level: "L4", assessedBy: "system", assessedDate: "2025-06-01", evidence: "" },
      cognitive_thinking:        { level: "L4", assessedBy: "system", assessedDate: "2025-06-01", evidence: "" },
      developing_oneself:        { level: "L4", assessedBy: "system", assessedDate: "2025-06-01", evidence: "" },
      knowing_oneself:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: "L4", assessedBy: "system", assessedDate: "2025-06-01", evidence: "" },
      work_in_teams:             { level: "L4", assessedBy: "system", assessedDate: "2025-06-01", evidence: "" }
    },
    targetRoleId: null, targetRoleValidated: true
  },
  {
    id: "emp_009", name: "Lukas Andersen", email: "lukas.andersen@ceps.eu",
    gender: "male", phone: "+32 2 229 3909", contractType: "fixed-term", fte: 0.8,
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
      knowing_oneself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" }
    },
    targetRoleId: "researcher", targetRoleValidated: false
  },
  {
    id: "emp_010", name: "Marie Dubois", email: "marie.dubois@ceps.eu",
    gender: "female", phone: "+32 2 229 3910", contractType: "permanent", fte: 0.9,
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
      knowing_oneself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L2", assessedBy: "emp_006", assessedDate: "2025-10-01", evidence: "" }
    },
    targetRoleId: "research_fellow", targetRoleValidated: false
  },
  {
    id: "emp_011", name: "Thomas Weber", email: "thomas.weber@ceps.eu",
    gender: "male", phone: "+32 2 229 3911", contractType: "permanent", fte: 1.0,
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
      knowing_oneself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: "L2", assessedBy: "emp_006", assessedDate: "2025-09-01", evidence: "" },
      work_in_teams:             { level: "L3", assessedBy: "emp_006", assessedDate: "2025-09-01", evidence: "" }
    },
    targetRoleId: "head_of_program", targetRoleValidated: true
  },
  {
    id: "emp_012", name: "Katarina Novak", email: "katarina.novak@ceps.eu",
    gender: "female", phone: "+32 2 229 3912", contractType: "fixed-term", fte: 1.0,
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
      knowing_oneself:          { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      team_leadership:           { level: null, assessedBy: null, assessedDate: null, evidence: "" },
      work_in_teams:             { level: "L1", assessedBy: "emp_007", assessedDate: "2025-11-01", evidence: "" }
    },
    targetRoleId: "research_fellow", targetRoleValidated: false
  }
];

// ── ACTION LIBRARY (v2: added nextDate, cost, maxParticipants, enrolled) ────
const ACTION_LIBRARY = [
  // Funding & income generation
  { id:"lib_001", skillId:"funding_income_generation", fromLevel:"L1", toLevel:"L2", type:"training", title:"Grant Writing Workshop", description:"Intensive 3-day workshop on identifying funding sources and writing successful grant proposals for EU research programmes.", duration:"3 days", provider:"internal", cost:0, nextDate:"2026-05-12", maxParticipants:15, enrolled:8 },
  { id:"lib_002", skillId:"funding_income_generation", fromLevel:"L1", toLevel:"L2", type:"mentoring", title:"Funding Mentor Pairing", description:"6-month mentoring relationship with a senior researcher experienced in securing Horizon Europe and national grants.", duration:"6 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_003", skillId:"funding_income_generation", fromLevel:"L2", toLevel:"L3", type:"project", title:"Lead a Grant Application", description:"Take the lead on a medium-scale grant application (€200K-500K) with guidance from a senior colleague.", duration:"3 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_004", skillId:"funding_income_generation", fromLevel:"L2", toLevel:"L3", type:"training", title:"Budget Planning & Financial Management", description:"Training on research budget planning, financial reporting, and resource management for project leads.", duration:"2 days", provider:"external", cost:850, nextDate:"2026-06-03", maxParticipants:20, enrolled:12 },
  { id:"lib_005", skillId:"funding_income_generation", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Strategic Funding Portfolio Development", description:"Develop a multi-year funding strategy for your unit including diversification of funding sources.", duration:"6 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_006", skillId:"funding_income_generation", fromLevel:"L3", toLevel:"L4", type:"project", title:"Lead a Consortium Application", description:"Lead a large-scale international consortium grant application (€1M+).", duration:"6 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },

  // Project Management
  { id:"lib_007", skillId:"project_management", fromLevel:"L1", toLevel:"L2", type:"training", title:"Project Management Fundamentals", description:"Introduction to project management tools, timelines, deliverables, and risk management for research projects.", duration:"2 days", provider:"external", cost:1200, nextDate:"2026-04-22", maxParticipants:25, enrolled:18 },
  { id:"lib_008", skillId:"project_management", fromLevel:"L1", toLevel:"L2", type:"stretch", title:"Co-lead a Research Project", description:"Take co-leadership responsibility for a small research project, managing timelines and deliverables.", duration:"4 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_009", skillId:"project_management", fromLevel:"L2", toLevel:"L3", type:"training", title:"Advanced Project Management", description:"Advanced techniques for managing multiple projects, stakeholder management, and strategic alignment.", duration:"3 days", provider:"external", cost:1800, nextDate:"2026-09-15", maxParticipants:20, enrolled:5 },
  { id:"lib_010", skillId:"project_management", fromLevel:"L2", toLevel:"L3", type:"project", title:"Manage a Cross-Unit Project", description:"Lead a project that involves collaboration across two or more CEPS units.", duration:"6 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_011", skillId:"project_management", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Design Project Governance Framework", description:"Design and implement a project governance structure for large interdisciplinary initiatives.", duration:"3 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },

  // Disciplinary expertise
  { id:"lib_012", skillId:"disciplinary_expertise", fromLevel:"L1", toLevel:"L2", type:"training", title:"EU Policy Research Methods Course", description:"Deep-dive course covering EU institutional landscape, policy analysis, and evidence-based research techniques.", duration:"1 week", provider:"external", cost:2500, nextDate:"2026-06-16", maxParticipants:30, enrolled:22 },
  { id:"lib_013", skillId:"disciplinary_expertise", fromLevel:"L1", toLevel:"L2", type:"self-study", title:"Literature Review Deep Dive", description:"Conduct a comprehensive literature review in your specific policy area and present findings to the team.", duration:"2 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_014", skillId:"disciplinary_expertise", fromLevel:"L2", toLevel:"L3", type:"mentoring", title:"Senior Researcher Mentoring", description:"6-month structured mentoring with a Senior Research Fellow to deepen domain expertise.", duration:"6 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_015", skillId:"disciplinary_expertise", fromLevel:"L2", toLevel:"L3", type:"project", title:"Lead a Policy Paper", description:"Author a major CEPS policy paper demonstrating original contributions to the field.", duration:"3 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_016", skillId:"disciplinary_expertise", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Establish New Research Stream", description:"Identify and establish a new research area or programme at CEPS, positioning yourself as a thought leader.", duration:"12 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },

  // Research methodology
  { id:"lib_017", skillId:"research_methodology", fromLevel:"L1", toLevel:"L2", type:"training", title:"Applied Research Methods", description:"Hands-on training in quantitative and qualitative research methods for policy analysis.", duration:"5 days", provider:"external", cost:1950, nextDate:"2026-05-05", maxParticipants:20, enrolled:14 },
  { id:"lib_018", skillId:"research_methodology", fromLevel:"L1", toLevel:"L2", type:"self-study", title:"Data Analysis Skills Development", description:"Self-paced learning in statistical analysis tools (R, Stata, or Python) with weekly check-ins.", duration:"3 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_019", skillId:"research_methodology", fromLevel:"L2", toLevel:"L3", type:"training", title:"Advanced Econometrics & Policy Evaluation", description:"Summer school on causal inference, impact evaluation, and advanced econometric techniques.", duration:"2 weeks", provider:"external", cost:3200, nextDate:"2026-07-07", maxParticipants:25, enrolled:9 },
  { id:"lib_020", skillId:"research_methodology", fromLevel:"L2", toLevel:"L3", type:"project", title:"Design and Lead a Research Study", description:"Independently design and execute a research study with novel methodological approach.", duration:"6 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_021", skillId:"research_methodology", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Develop Methodological Innovation", description:"Create or adapt a new research framework or methodology that can be adopted by the team.", duration:"6 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },

  // Writing
  { id:"lib_022", skillId:"writing", fromLevel:"L1", toLevel:"L2", type:"training", title:"Academic Writing for Policy", description:"Workshop on structuring research reports, policy briefs, and academic publications for different audiences.", duration:"3 days", provider:"internal", cost:0, nextDate:"2026-04-14", maxParticipants:12, enrolled:10 },
  { id:"lib_023", skillId:"writing", fromLevel:"L1", toLevel:"L2", type:"mentoring", title:"Writing Mentor Programme", description:"Paired with a senior writer who reviews and provides feedback on your drafts over 4 months.", duration:"4 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_024", skillId:"writing", fromLevel:"L2", toLevel:"L3", type:"project", title:"Lead Author on Major Report", description:"Serve as lead author on a comprehensive CEPS report, managing the editorial process.", duration:"4 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_025", skillId:"writing", fromLevel:"L2", toLevel:"L3", type:"training", title:"Strategic Communication Writing", description:"Advanced course on adapting complex policy topics for media, policymakers, and public audiences.", duration:"2 days", provider:"external", cost:750, nextDate:"2026-05-28", maxParticipants:15, enrolled:6 },
  { id:"lib_026", skillId:"writing", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Editorial Leadership", description:"Take editorial responsibility for CEPS publication standards, mentoring junior writers.", duration:"ongoing", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },

  // Making impact
  { id:"lib_027", skillId:"making_impact", fromLevel:"L1", toLevel:"L2", type:"training", title:"Policy Communication & Engagement", description:"Workshop on effective presentation at policy events, stakeholder engagement, and media interactions.", duration:"2 days", provider:"internal", cost:0, nextDate:"2026-04-07", maxParticipants:20, enrolled:16 },
  { id:"lib_028", skillId:"making_impact", fromLevel:"L1", toLevel:"L2", type:"stretch", title:"Present at External Event", description:"Present research findings at an external policy event or conference.", duration:"1 month prep", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_029", skillId:"making_impact", fromLevel:"L2", toLevel:"L3", type:"project", title:"Build a Stakeholder Network", description:"Develop and maintain relationships with 5+ key policymakers or organisations in your research area.", duration:"6 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_030", skillId:"making_impact", fromLevel:"L2", toLevel:"L3", type:"training", title:"Media Training", description:"Professional media training covering interviews, op-eds, and social media for research dissemination.", duration:"1 day", provider:"external", cost:600, nextDate:"2026-06-20", maxParticipants:10, enrolled:3 },
  { id:"lib_031", skillId:"making_impact", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Strategic Engagement Leadership", description:"Lead CEPS engagement strategy for a major policy dossier, coordinating with EU institutions.", duration:"12 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },

  // Cognitive thinking
  { id:"lib_032", skillId:"cognitive_thinking", fromLevel:"L1", toLevel:"L2", type:"training", title:"Critical Thinking & Analysis", description:"Workshop developing skills in logical reasoning, evidence evaluation, and creative problem-solving.", duration:"2 days", provider:"external", cost:950, nextDate:"2026-05-19", maxParticipants:20, enrolled:11 },
  { id:"lib_033", skillId:"cognitive_thinking", fromLevel:"L1", toLevel:"L2", type:"self-study", title:"Cross-Disciplinary Reading Programme", description:"Structured reading programme covering adjacent policy fields to broaden analytical perspective.", duration:"3 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_034", skillId:"cognitive_thinking", fromLevel:"L2", toLevel:"L3", type:"stretch", title:"Lead an Interdisciplinary Analysis", description:"Design and lead a research initiative that integrates perspectives from multiple disciplines.", duration:"6 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_035", skillId:"cognitive_thinking", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Strategic Foresight Exercise", description:"Lead a strategic foresight exercise identifying emerging trends and their policy implications.", duration:"3 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },

  // Developing oneself
  { id:"lib_036", skillId:"developing_oneself", fromLevel:"L1", toLevel:"L2", type:"mentoring", title:"Career Development Mentoring", description:"Structured mentoring focused on career goals, professional network building, and skill planning.", duration:"6 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_037", skillId:"developing_oneself", fromLevel:"L1", toLevel:"L2", type:"self-study", title:"Professional Development Plan", description:"Create and execute a personal development plan with quarterly milestones and self-assessment.", duration:"12 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_038", skillId:"developing_oneself", fromLevel:"L2", toLevel:"L3", type:"stretch", title:"Become a Mentor", description:"Mentor a junior colleague, developing coaching skills while supporting others' growth.", duration:"6 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_039", skillId:"developing_oneself", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Innovation Champion", description:"Challenge and improve existing processes within your unit, driving constructive change.", duration:"ongoing", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },

  // Team leadership
  { id:"lib_040", skillId:"team_leadership", fromLevel:"L1", toLevel:"L2", type:"training", title:"Leadership Fundamentals", description:"Training on delegation, goal-setting, conflict resolution, and motivating team members.", duration:"3 days", provider:"external", cost:1500, nextDate:"2026-04-28", maxParticipants:15, enrolled:7 },
  { id:"lib_041", skillId:"team_leadership", fromLevel:"L1", toLevel:"L2", type:"stretch", title:"Lead a Small Project Team", description:"Take leadership of a 2-3 person project team with full responsibility for coordination and delivery.", duration:"4 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_042", skillId:"team_leadership", fromLevel:"L2", toLevel:"L3", type:"training", title:"Advanced Leadership & Team Dynamics", description:"Workshop on situational leadership, team performance management, and coaching techniques.", duration:"2 days", provider:"external", cost:1100, nextDate:"2026-10-06", maxParticipants:12, enrolled:2 },
  { id:"lib_043", skillId:"team_leadership", fromLevel:"L2", toLevel:"L3", type:"project", title:"Lead a Cross-Functional Research Team", description:"Lead a research team of 4+ people across different specialisations.", duration:"6 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_044", skillId:"team_leadership", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Organisational Leadership", description:"Take responsibility for unit-level strategic decisions, staff development, and performance management.", duration:"12 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },

  // Work in teams
  { id:"lib_045", skillId:"work_in_teams", fromLevel:"L1", toLevel:"L2", type:"training", title:"Effective Collaboration Workshop", description:"Skills for productive teamwork: communication, feedback, time management, and conflict resolution.", duration:"1 day", provider:"internal", cost:0, nextDate:"2026-04-03", maxParticipants:25, enrolled:20 },
  { id:"lib_046", skillId:"work_in_teams", fromLevel:"L1", toLevel:"L2", type:"stretch", title:"Cross-Unit Collaboration", description:"Participate actively in a project with a different CEPS unit to broaden teamwork experience.", duration:"3 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_047", skillId:"work_in_teams", fromLevel:"L2", toLevel:"L3", type:"stretch", title:"Team Culture Initiative", description:"Lead an initiative to improve team dynamics, inclusion, or collaboration practices within your unit.", duration:"3 months", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null },
  { id:"lib_048", skillId:"work_in_teams", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Organisational Culture Ambassador", description:"Drive organisation-wide culture improvement initiatives and model exemplary collaborative behaviour.", duration:"ongoing", provider:"internal", cost:0, nextDate:null, maxParticipants:null, enrolled:null }
];

// ── SEED FEEDBACK (v2: expanded from 7 to 22 entries) ───────────────────────
const SEED_FEEDBACK = [
  // John Doe (emp_001) — 4 entries
  { id:"fb_001", employeeId:"emp_001", authorId:"emp_003", authorRole:"manager", date:"2026-02-15", skillId:"making_impact", type:"positive", content:"Excellent presentation at the EU Digital Policy Forum. Your ability to translate complex research into actionable policy recommendations was very well received by the audience.", visibility:"employee_manager" },
  { id:"fb_002", employeeId:"emp_001", authorId:"emp_003", authorRole:"manager", date:"2026-01-20", skillId:"writing", type:"developmental", content:"The latest policy brief needs more structured argumentation. Consider using the CEPS template for better flow. Happy to review your next draft together.", visibility:"employee_manager" },
  { id:"fb_007", employeeId:"emp_001", authorId:"emp_002", authorRole:"peer", date:"2026-03-05", skillId:"work_in_teams", type:"positive", content:"Really appreciate how you always make time to help with data questions. Great team spirit!", visibility:"employee_manager" },
  { id:"fb_008", employeeId:"emp_001", authorId:"emp_001", authorRole:"self", date:"2026-03-10", skillId:"funding_income_generation", type:"observation", content:"Attended the Horizon Europe info session. Found it useful but still feel uncertain about budget templates. Will follow up with Sophie.", visibility:"employee_manager" },

  // Clara Santa (emp_002) — 3 entries
  { id:"fb_003", employeeId:"emp_002", authorId:"emp_003", authorRole:"manager", date:"2026-03-01", skillId:"disciplinary_expertise", type:"developmental", content:"To progress from L1 to L2 in disciplinary expertise, I'd recommend deepening your knowledge of EU competition policy frameworks. The upcoming CEPS workshop would be a good start.", visibility:"employee_manager" },
  { id:"fb_009", employeeId:"emp_002", authorId:"emp_003", authorRole:"manager", date:"2026-02-10", skillId:"research_methodology", type:"positive", content:"Solid quantitative analysis in the latest report. Your R skills are clearly improving. Keep it up.", visibility:"employee_manager" },
  { id:"fb_010", employeeId:"emp_002", authorId:"emp_001", authorRole:"peer", date:"2026-03-12", skillId:null, type:"positive", content:"Clara's thorough approach to literature reviews has been really helpful for our joint paper. She's very reliable.", visibility:"employee_manager" },

  // Josey Dorsey (emp_003) — 3 entries
  { id:"fb_005", employeeId:"emp_003", authorId:"emp_006", authorRole:"manager", date:"2026-01-10", skillId:"project_management", type:"developmental", content:"Your project management skills need attention — the last two deliverables were submitted late. Let's work on a structured project plan with clear milestones.", visibility:"employee_manager" },
  { id:"fb_011", employeeId:"emp_003", authorId:"emp_006", authorRole:"manager", date:"2026-03-15", skillId:"funding_income_generation", type:"positive", content:"The Horizon Europe proposal you led was shortlisted. Excellent work coordinating the consortium partners.", visibility:"employee_manager" },
  { id:"fb_012", employeeId:"emp_003", authorId:"emp_001", authorRole:"peer", date:"2026-02-20", skillId:"team_leadership", type:"positive", content:"Josey is a great mentor. She always makes time for one-on-ones and gives constructive, specific feedback.", visibility:"employee_manager" },

  // Anna Bergström (emp_004) — 2 entries
  { id:"fb_006", employeeId:"emp_004", authorId:"emp_003", authorRole:"manager", date:"2026-03-10", skillId:"research_methodology", type:"positive", content:"Good progress on learning quantitative methods. Your data analysis in the latest report shows clear improvement.", visibility:"employee_manager" },
  { id:"fb_013", employeeId:"emp_004", authorId:"emp_003", authorRole:"manager", date:"2026-01-25", skillId:"writing", type:"developmental", content:"Your writing is improving but policy briefs still need tighter executive summaries. Let's do a writing session together next week.", visibility:"employee_manager" },

  // Marco Rossi (emp_005) — 3 entries
  { id:"fb_004", employeeId:"emp_005", authorId:"emp_007", authorRole:"manager", date:"2026-02-28", skillId:null, type:"positive", content:"Great teamwork on the energy transition report. You coordinated well with the external partners and kept the project on track.", visibility:"employee_manager" },
  { id:"fb_014", employeeId:"emp_005", authorId:"emp_007", authorRole:"manager", date:"2026-01-15", skillId:"making_impact", type:"positive", content:"Your presentation at the Brussels Energy Forum was well-received. Several stakeholders asked for follow-up meetings.", visibility:"employee_manager" },
  { id:"fb_015", employeeId:"emp_005", authorId:"emp_012", authorRole:"peer", date:"2026-03-08", skillId:"cognitive_thinking", type:"positive", content:"Marco has a great ability to connect dots between different policy domains. His cross-disciplinary insights on the latest paper were invaluable.", visibility:"employee_manager" },

  // Peter Müller (emp_007) — 2 entries
  { id:"fb_016", employeeId:"emp_007", authorId:"emp_008", authorRole:"manager", date:"2026-02-05", skillId:"writing", type:"developmental", content:"Peter, your analytical depth is excellent but the writing needs to be more accessible for non-specialist audiences. Consider the media training course.", visibility:"employee_manager" },
  { id:"fb_017", employeeId:"emp_007", authorId:"emp_008", authorRole:"manager", date:"2026-03-20", skillId:"disciplinary_expertise", type:"positive", content:"Your energy markets expertise is becoming a real asset for CEPS. The DG Energy consultation response was top-notch.", visibility:"employee_manager" },

  // Thomas Weber (emp_011) — 3 entries
  { id:"fb_018", employeeId:"emp_011", authorId:"emp_006", authorRole:"manager", date:"2026-01-30", skillId:"project_management", type:"positive", content:"Thomas managed the fiscal policy project exceptionally well. Delivered on time, under budget, and the client was very satisfied.", visibility:"employee_manager" },
  { id:"fb_019", employeeId:"emp_011", authorId:"emp_006", authorRole:"manager", date:"2026-03-05", skillId:"team_leadership", type:"developmental", content:"As you prepare for Head of Program, you'll need to invest more in people management. Consider the advanced leadership workshop.", visibility:"employee_manager" },
  { id:"fb_020", employeeId:"emp_011", authorId:"emp_003", authorRole:"peer", date:"2026-02-25", skillId:null, type:"positive", content:"Thomas is always willing to share his economic modelling expertise. He helped me debug a complex DSGE model last week.", visibility:"employee_manager" },

  // Katarina Novak (emp_012) — 1 entry
  { id:"fb_021", employeeId:"emp_012", authorId:"emp_007", authorRole:"manager", date:"2026-03-18", skillId:"research_methodology", type:"positive", content:"Katarina has shown impressive growth in quantitative methods. Her econometric analysis of energy pricing data was methodologically sound.", visibility:"employee_manager" },

  // Marie Dubois (emp_010) — 1 entry
  { id:"fb_022", employeeId:"emp_010", authorId:"emp_006", authorRole:"manager", date:"2026-02-12", skillId:"disciplinary_expertise", type:"observation", content:"Marie is progressing well but needs to take more initiative in choosing research topics. Encourage her to propose her own policy brief subject next quarter.", visibility:"employee_manager" }
];

// ── SEED DEVELOPMENT PLANS (v2: expanded from 2 to 7 active IDPs) ───────────
const SEED_IDPS = [
  {
    id: "idp_001", employeeId: "emp_001", targetRoleId: "research_fellow",
    createdDate: "2026-01-15", status: "active",
    actions: [
      { id:"act_001", skillId:"funding_income_generation", fromLevel:"L1", toLevel:"L2", type:"training", title:"Grant Writing Workshop", description:"Intensive 3-day workshop on identifying funding sources and writing successful grant proposals.", source:"library", deadline:"2026-06-30", status:"in_progress", managerApproved:true, completedDate:null, notes:"Enrolled in May session" },
      { id:"act_002", skillId:"disciplinary_expertise", fromLevel:"L2", toLevel:"L3", type:"mentoring", title:"Senior Researcher Mentoring", description:"6-month structured mentoring with Dr. Laurent.", source:"library", deadline:"2026-09-30", status:"not_started", managerApproved:true, completedDate:null, notes:"" },
      { id:"act_010", skillId:"writing", fromLevel:"L2", toLevel:"L3", type:"training", title:"Strategic Communication Writing", description:"Advanced writing course for policy audiences.", source:"library", deadline:"2026-05-28", status:"in_progress", managerApproved:true, completedDate:null, notes:"Registered for May session" }
    ],
    reviewDates: ["2026-04-01", "2026-07-01", "2026-10-01"],
    managerNotes: "Good trajectory. Focus on funding skills first.",
    lastReviewDate: "2026-01-15"
  },
  {
    id: "idp_002", employeeId: "emp_005", targetRoleId: "research_fellow",
    createdDate: "2026-02-01", status: "active",
    actions: [
      { id:"act_003", skillId:"writing", fromLevel:"L2", toLevel:"L3", type:"training", title:"Strategic Communication Writing", description:"Advanced course on adapting complex policy topics for different audiences.", source:"library", deadline:"2026-05-30", status:"completed", managerApproved:true, completedDate:"2026-03-15", notes:"Completed successfully — writing quality noticeably improved" },
      { id:"act_004", skillId:"making_impact", fromLevel:"L2", toLevel:"L3", type:"stretch", title:"Present at External Event", description:"Present at the upcoming EU Energy Forum.", source:"library", deadline:"2026-07-15", status:"in_progress", managerApproved:true, completedDate:null, notes:"Accepted as panelist" },
      { id:"act_011", skillId:"cognitive_thinking", fromLevel:"L2", toLevel:"L3", type:"stretch", title:"Lead an Interdisciplinary Analysis", description:"Lead the energy-economics cross-unit research initiative.", source:"library", deadline:"2026-10-01", status:"not_started", managerApproved:true, completedDate:null, notes:"" }
    ],
    reviewDates: ["2026-05-01", "2026-08-01"],
    managerNotes: "Strong candidate for promotion. Writing skills improving fast.",
    lastReviewDate: "2026-02-01"
  },
  {
    id: "idp_003", employeeId: "emp_003", targetRoleId: "head_of_program",
    createdDate: "2025-10-01", status: "active",
    actions: [
      { id:"act_005", skillId:"project_management", fromLevel:"L1", toLevel:"L2", type:"training", title:"Project Management Fundamentals", description:"Introduction to PM tools, timelines, and risk management.", source:"library", deadline:"2026-04-30", status:"completed", managerApproved:true, completedDate:"2026-02-20", notes:"Completed. Very useful for structuring the Horizon project." },
      { id:"act_006", skillId:"project_management", fromLevel:"L2", toLevel:"L3", type:"project", title:"Manage a Cross-Unit Project", description:"Co-lead the Economic Policy-Digital Policy joint research stream.", source:"manual", deadline:"2026-09-01", status:"in_progress", managerApproved:true, completedDate:null, notes:"Ongoing — 3 of 5 milestones delivered" },
      { id:"act_012", skillId:"funding_income_generation", fromLevel:"L2", toLevel:"L3", type:"project", title:"Lead a Grant Application", description:"Lead the upcoming ERC Consolidator Grant application.", source:"library", deadline:"2026-08-15", status:"in_progress", managerApproved:true, completedDate:null, notes:"Draft in progress" },
      { id:"act_013", skillId:"research_methodology", fromLevel:"L2", toLevel:"L3", type:"training", title:"Advanced Econometrics & Policy Evaluation", description:"CEPR Summer School on causal inference.", source:"library", deadline:"2026-07-07", status:"not_started", managerApproved:true, completedDate:null, notes:"Registered" }
    ],
    reviewDates: ["2026-01-15", "2026-04-15", "2026-07-15", "2026-10-15"],
    managerNotes: "Josey is on track for Head of Program. Project management was the main gap — now actively closing it.",
    lastReviewDate: "2026-01-15"
  },
  {
    id: "idp_004", employeeId: "emp_004", targetRoleId: "researcher",
    createdDate: "2026-02-15", status: "active",
    actions: [
      { id:"act_007", skillId:"research_methodology", fromLevel:"L1", toLevel:"L2", type:"training", title:"Applied Research Methods", description:"Hands-on training in quantitative and qualitative methods.", source:"library", deadline:"2026-05-05", status:"in_progress", managerApproved:true, completedDate:null, notes:"Enrolled in May session" },
      { id:"act_008", skillId:"writing", fromLevel:"L1", toLevel:"L2", type:"mentoring", title:"Writing Mentor Programme", description:"Paired with Josey Dorsey for writing feedback over 4 months.", source:"library", deadline:"2026-06-30", status:"in_progress", managerApproved:true, completedDate:null, notes:"Bi-weekly sessions ongoing" },
      { id:"act_014", skillId:"disciplinary_expertise", fromLevel:"L1", toLevel:"L2", type:"training", title:"EU Policy Research Methods Course", description:"Deep-dive into EU institutions and policy analysis.", source:"library", deadline:"2026-06-16", status:"not_started", managerApproved:true, completedDate:null, notes:"Registered" }
    ],
    reviewDates: ["2026-05-15", "2026-08-15"],
    managerNotes: "Anna is making excellent progress for a new starter. Keep up the mentoring sessions.",
    lastReviewDate: "2026-02-15"
  },
  {
    id: "idp_005", employeeId: "emp_011", targetRoleId: "head_of_program",
    createdDate: "2025-11-01", status: "active",
    actions: [
      { id:"act_015", skillId:"funding_income_generation", fromLevel:"L2", toLevel:"L3", type:"training", title:"Budget Planning & Financial Management", description:"Research budget planning and financial reporting.", source:"library", deadline:"2026-06-03", status:"not_started", managerApproved:true, completedDate:null, notes:"Registered for June session" },
      { id:"act_016", skillId:"team_leadership", fromLevel:"L2", toLevel:"L3", type:"training", title:"Advanced Leadership & Team Dynamics", description:"Situational leadership and team performance management.", source:"library", deadline:"2026-10-06", status:"not_started", managerApproved:true, completedDate:null, notes:"" },
      { id:"act_017", skillId:"making_impact", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Strategic Engagement Leadership", description:"Lead CEPS engagement for the EU fiscal governance dossier.", source:"ai", deadline:"2026-12-31", status:"in_progress", managerApproved:true, completedDate:null, notes:"Already engaged with DG ECFIN contacts" },
      { id:"act_018", skillId:"developing_oneself", fromLevel:"L3", toLevel:"L4", type:"stretch", title:"Innovation Champion", description:"Propose and lead one process improvement initiative at CEPS.", source:"library", deadline:"2026-09-01", status:"not_started", managerApproved:false, completedDate:null, notes:"Awaiting manager review" }
    ],
    reviewDates: ["2026-03-01", "2026-06-01", "2026-09-01", "2026-12-01"],
    managerNotes: "Thomas is very close to promotion. Main focus areas: leadership development and strategic engagement.",
    lastReviewDate: "2026-03-01"
  },
  {
    id: "idp_006", employeeId: "emp_012", targetRoleId: "research_fellow",
    createdDate: "2026-03-01", status: "active",
    actions: [
      { id:"act_019", skillId:"writing", fromLevel:"L1", toLevel:"L2", type:"training", title:"Academic Writing for Policy", description:"Structuring reports, policy briefs, and publications.", source:"library", deadline:"2026-04-14", status:"in_progress", managerApproved:true, completedDate:null, notes:"Registered for April session" },
      { id:"act_020", skillId:"making_impact", fromLevel:"L1", toLevel:"L2", type:"training", title:"Policy Communication & Engagement", description:"Workshop on presenting at policy events.", source:"library", deadline:"2026-04-07", status:"completed", managerApproved:true, completedDate:"2026-04-07", notes:"Completed — very helpful for upcoming conference" }
    ],
    reviewDates: ["2026-06-01", "2026-09-01"],
    managerNotes: "Katarina has potential but needs to build writing and impact skills to match her strong methodology.",
    lastReviewDate: "2026-03-01"
  },
  {
    id: "idp_007", employeeId: "emp_010", targetRoleId: "research_fellow",
    createdDate: "2026-01-10", status: "active",
    actions: [
      { id:"act_021", skillId:"research_methodology", fromLevel:"L1", toLevel:"L2", type:"self-study", title:"Data Analysis Skills Development", description:"Self-paced R and Stata learning with weekly check-ins.", source:"library", deadline:"2026-06-30", status:"in_progress", managerApproved:true, completedDate:null, notes:"Completed R intro module, starting Stata" },
      { id:"act_022", skillId:"funding_income_generation", fromLevel:"L1", toLevel:"L2", type:"mentoring", title:"Funding Mentor Pairing", description:"Paired with Sophie Laurent to learn about grant applications.", source:"library", deadline:"2026-07-15", status:"in_progress", managerApproved:true, completedDate:null, notes:"Monthly sessions ongoing" },
      { id:"act_023", skillId:"making_impact", fromLevel:"L1", toLevel:"L2", type:"stretch", title:"Present at External Event", description:"Present at the ECFIN Annual Research Conference.", source:"manual", deadline:"2026-09-20", status:"not_started", managerApproved:false, completedDate:null, notes:"Abstract submitted, awaiting acceptance" }
    ],
    reviewDates: ["2026-04-10", "2026-07-10", "2026-10-10"],
    managerNotes: "Marie is progressing steadily. Focus on methodology and funding as priority skills.",
    lastReviewDate: "2026-01-10"
  }
];

// ── SEED GOALS (v3) ─────────────────────────────────────────────────────────
const SEED_GOALS = [
  { id:"goal_001", employeeId:"emp_001", title:"Secure first independent grant", description:"Submit a successful grant application as lead PI for a project worth at least €100K, demonstrating ability to independently secure research funding.", deadline:"2026-09-30", status:"in_progress", linkedSkillId:"funding_income_generation", createdDate:"2026-01-20", managerApproved:true, managerNotes:"Good ambition. Start with smaller national grants." },
  { id:"goal_002", employeeId:"emp_001", title:"Publish peer-reviewed article", description:"Author a peer-reviewed publication in a top-tier policy journal based on original research conducted at CEPS.", deadline:"2026-12-31", status:"approved", linkedSkillId:"disciplinary_expertise", createdDate:"2026-01-20", managerApproved:true, managerNotes:"" },
  { id:"goal_003", employeeId:"emp_003", title:"Deliver Horizon project on time", description:"Successfully manage and deliver the current Horizon Europe project (Digital Markets) within scope, timeline, and budget.", deadline:"2026-08-31", status:"in_progress", linkedSkillId:"project_management", createdDate:"2025-11-01", managerApproved:true, managerNotes:"Critical for Head of Program readiness." },
  { id:"goal_004", employeeId:"emp_005", title:"Present at 3 external policy events", description:"Represent CEPS at three major external events (EU Energy Forum, Florence School, CERRE) to build stakeholder network and visibility.", deadline:"2026-10-31", status:"in_progress", linkedSkillId:"making_impact", createdDate:"2026-02-05", managerApproved:true, managerNotes:"Already confirmed for 1 event. Keep it up." },
  { id:"goal_005", employeeId:"emp_011", title:"Mentor two junior researchers", description:"Provide structured mentoring to two junior colleagues over 6 months, including bi-weekly sessions and written feedback.", deadline:"2026-08-31", status:"pending_approval", linkedSkillId:"developing_oneself", createdDate:"2026-03-10", managerApproved:false, managerNotes:"" },
  { id:"goal_006", employeeId:"emp_004", title:"Complete quantitative methods certification", description:"Finish the Applied Research Methods training and demonstrate proficiency by independently conducting a quantitative analysis.", deadline:"2026-06-30", status:"in_progress", linkedSkillId:"research_methodology", createdDate:"2026-02-20", managerApproved:true, managerNotes:"Great initiative. Focus on the R component." },
  { id:"goal_007", employeeId:"emp_012", title:"Write first solo policy brief", description:"Author a policy brief independently, from topic selection through research to publication, without co-authors.", deadline:"2026-07-31", status:"draft", linkedSkillId:"writing", createdDate:"2026-03-15", managerApproved:false, managerNotes:"" }
];

// ── SEED TRAINING REQUESTS (v3) ─────────────────────────────────────────────
const SEED_TRAINING_REQUESTS = [
  { id:"treq_001", employeeId:"emp_002", title:"Python for Policy Analysis", description:"Online course on Python for data analysis and visualisation, specifically tailored to policy research applications.", type:"training", estimatedCost:450, estimatedDuration:"4 weeks", linkedSkillId:"research_methodology", status:"pending", requestDate:"2026-03-15", managerComment:"", resolvedBy:null, resolvedDate:null },
  { id:"treq_002", employeeId:"emp_009", title:"EU Institutions Crash Course", description:"Intensive 2-day introduction to EU institutions, decision-making processes, and key policy frameworks.", type:"training", estimatedCost:800, estimatedDuration:"2 days", linkedSkillId:"disciplinary_expertise", status:"approved", requestDate:"2026-02-28", managerComment:"Approved — essential for your role.", resolvedBy:"emp_007", resolvedDate:"2026-03-05" },
  { id:"treq_003", employeeId:"emp_010", title:"Brussels Climate Conference 2026", description:"Attend the annual Brussels Climate Conference as participant, with opportunity to present a poster on our latest findings.", type:"conference", estimatedCost:350, estimatedDuration:"2 days", linkedSkillId:"making_impact", status:"pending", requestDate:"2026-03-20", managerComment:"", resolvedBy:null, resolvedDate:null }
];
