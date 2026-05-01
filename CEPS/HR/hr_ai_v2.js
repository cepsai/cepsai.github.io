// ── HR AI: LLM integration for development plan suggestions ─────────────────
// Default: Ollama with glm-4.7-flash running locally

const AIAdvisor = {
  async suggestActions(skillName, fromLevel, toLevel, skillDefinition, fromLevelDesc, toLevelDesc) {
    const settings = HRStore.getSettings();
    const endpoint = settings.aiEndpoint || 'http://localhost:11434/api/generate';
    const model = settings.aiModel || 'glm-4.7-flash';

    const prompt = `You are an HR development advisor for CEPS, a European policy research think tank based in Brussels.

An employee needs to develop the skill "${skillName}" from Level ${fromLevel} to Level ${toLevel}.

Skill definition: ${skillDefinition}

Current level (${fromLevel}) descriptors:
${fromLevelDesc}

Target level (${toLevel}) descriptors:
${toLevelDesc}

Suggest exactly 3 specific, actionable development activities. For each activity, respond with a JSON array where each object has these exact fields:
- "title": short title (under 60 chars)
- "type": one of "training", "mentoring", "stretch", "project", "self-study"
- "description": 2-3 sentences, specific to a think tank / policy research context
- "duration": estimated time (e.g. "3 months", "2 weeks")
- "outcome": expected measurable outcome

IMPORTANT: Respond with ONLY a valid JSON array, no other text. Example format:
[{"title":"...","type":"...","description":"...","duration":"...","outcome":"..."}]`;

    try {
      // Check if endpoint is Ollama-style (contains /api/generate)
      if (endpoint.includes('/api/generate')) {
        return await this._callOllama(endpoint, model, prompt);
      } else if (endpoint.includes('/v1/')) {
        return await this._callOpenAICompat(endpoint, model, prompt, settings.aiApiKey);
      } else {
        return await this._callOllama(endpoint, model, prompt);
      }
    } catch (e) {
      console.error('AIAdvisor error:', e);
      throw new Error('AI suggestion failed: ' + e.message);
    }
  },

  async _callOllama(endpoint, model, prompt) {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, prompt, stream: false })
    });

    if (!res.ok) throw new Error(`Ollama returned ${res.status}: ${res.statusText}`);

    const data = await res.json();
    const text = data.response || data.message?.content || '';
    return this._parseResponse(text);
  },

  async _callOpenAICompat(endpoint, model, prompt, apiKey) {
    const headers = { 'Content-Type': 'application/json' };
    if (apiKey) headers['Authorization'] = 'Bearer ' + apiKey;

    const res = await fetch(endpoint, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        model,
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.7
      })
    });

    if (!res.ok) throw new Error(`API returned ${res.status}: ${res.statusText}`);

    const data = await res.json();
    const text = data.choices?.[0]?.message?.content || '';
    return this._parseResponse(text);
  },

  _parseResponse(text) {
    // Try to extract JSON array from response
    let cleaned = text.trim();

    // Remove markdown code fences if present
    cleaned = cleaned.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '');

    // Find JSON array in the text
    const arrStart = cleaned.indexOf('[');
    const arrEnd = cleaned.lastIndexOf(']');
    if (arrStart === -1 || arrEnd === -1) {
      throw new Error('No JSON array found in AI response');
    }

    cleaned = cleaned.substring(arrStart, arrEnd + 1);

    try {
      const suggestions = JSON.parse(cleaned);
      if (!Array.isArray(suggestions) || suggestions.length === 0) {
        throw new Error('Invalid response format');
      }

      return suggestions.map(s => ({
        title: String(s.title || 'Untitled suggestion'),
        type: ['training', 'mentoring', 'stretch', 'project', 'self-study'].includes(s.type) ? s.type : 'training',
        description: String(s.description || ''),
        duration: String(s.duration || 'TBD'),
        outcome: String(s.outcome || '')
      }));
    } catch (e) {
      throw new Error('Failed to parse AI response as JSON: ' + e.message);
    }
  },

  // Cache management
  _cacheKey(skillId, fromLevel, toLevel) {
    return `ceps_hr_ai_cache_${skillId}_${fromLevel}_${toLevel}`;
  },

  getCached(skillId, fromLevel, toLevel) {
    try {
      const key = this._cacheKey(skillId, fromLevel, toLevel);
      const raw = sessionStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  },

  setCache(skillId, fromLevel, toLevel, suggestions) {
    try {
      const key = this._cacheKey(skillId, fromLevel, toLevel);
      sessionStorage.setItem(key, JSON.stringify(suggestions));
    } catch { /* ignore */ }
  },

  // Main entry point with caching
  async getSuggestions(skillId, fromLevel, toLevel) {
    // Check cache first
    const cached = this.getCached(skillId, fromLevel, toLevel);
    if (cached) return cached;

    // Get skill details
    const skill = SKILLS.find(s => s.id === skillId);
    if (!skill) throw new Error('Skill not found: ' + skillId);

    const fromDesc = skill.levels[fromLevel] || 'Not defined';
    const toDesc = skill.levels[toLevel] || 'Not defined';

    const suggestions = await this.suggestActions(
      skill.name, fromLevel, toLevel,
      skill.definition, fromDesc, toDesc
    );

    // Cache results
    this.setCache(skillId, fromLevel, toLevel, suggestions);

    return suggestions;
  },

  // Check if AI is available
  isConfigured() {
    const settings = HRStore.getSettings();
    return !!(settings.aiEndpoint && settings.aiModel);
  }
};
