// Member names for the video, from the single source notebooks/final/team.json (members[].name).
//   import { loadTeam, syncTeamNames, displayName } from './team.mjs';
// A placeholder name (empty, a single letter such as "A", "Member A", "<A>", anything with
// "TEAM TO FILL", or a bracketed "[...]") is shown as "[Name]". The letters A-D are never shown.
// syncTeamNames() writes video/data/team_names.json, which the scenes read in the browser
// (the preview server is rooted at video/ and cannot reach notebooks/).
import { readFileSync, writeFileSync, existsSync, statSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
export const VIDEO_ROOT = path.resolve(here, '..');
export const REPO_ROOT = path.resolve(VIDEO_ROOT, '..');
export const TEAM_JSON = path.join(REPO_ROOT, 'notebooks', 'final', 'team.json');
export const TEAM_NAMES_JSON = path.join(VIDEO_ROOT, 'data', 'team_names.json');
export const PLACEHOLDER = '[Name]';

/** True when a team.json name is not a real name yet. */
export function isPlaceholder(name) {
  const s = String(name == null ? '' : name).trim();
  if (!s) return true;
  if (/^[A-Za-z]$/.test(s)) return true;                       // "A"
  if (/^<\s*[A-Za-z]\s*>$/.test(s)) return true;                // "<A>"
  if (/^member\s+[A-Za-z0-9]$/i.test(s)) return true;           // "Member A"
  if (/team\s+to\s+fill/i.test(s)) return true;
  if (/^\[.*\]$/.test(s)) return true;                          // "[Name A]"
  return false;
}
export const displayName = (name) => (isPlaceholder(name) ? PLACEHOLDER : String(name).trim());

/** Group number for the title and closing cards: "[no.]" while it is a placeholder. */
export function displayGroup(g) {
  const s = String(g == null ? '' : g).trim();
  return !s || /team\s+to\s+fill/i.test(s) || /^\[.*\]$/.test(s) ? '[no.]' : s;
}

/** -> { group, members: [{ index, name, placeholder }] } (index = position in team.json). */
export function loadTeam(file = TEAM_JSON) {
  const raw = JSON.parse(readFileSync(file, 'utf8'));
  const members = (raw.members || []).map((m, index) => {
    const src = m.video_name || m.display_name || m.name;   // optional shorter on-screen name
    return { index, name: displayName(src), placeholder: isPlaceholder(src) };
  });
  return { group: displayGroup(raw.group_number), members };
}

/** Write video/data/team_names.json when team.json is newer (or force). Returns the team object. */
export function syncTeamNames({ force = false, quiet = false } = {}) {
  const team = loadTeam();
  const out = { _meta: { source: 'notebooks/final/team.json (members[].name)', written_by: 'video/render/team.mjs',
    rule: 'placeholder names (single letter, empty, "TEAM TO FILL", bracketed) render as [Name]; letters A-D are never rendered' },
  group: team.group, members: team.members };
  const text = JSON.stringify(out, null, 1) + '\n';
  const stale = force || !existsSync(TEAM_NAMES_JSON) || statSync(TEAM_JSON).mtimeMs > statSync(TEAM_NAMES_JSON).mtimeMs
    || readFileSync(TEAM_NAMES_JSON, 'utf8') !== text;
  if (stale) {
    mkdirSync(path.dirname(TEAM_NAMES_JSON), { recursive: true });
    writeFileSync(TEAM_NAMES_JSON, text);
    if (!quiet) console.log('team names -> ' + path.relative(process.cwd(), TEAM_NAMES_JSON) + ': ' + team.members.map((m) => m.name).join(', '));
  }
  return team;
}

/** Replace <Name> (the speaker) and <Name:i> (member i, 0-based) and {group} in a string. */
export function fillNames(str, team, speaker) {
  return String(str)
    .replace(/<Name(?::(\d))?>/g, (_, i) => {
      const m = team.members[i != null ? Number(i) : speaker];
      if (!m) throw new Error(`name token ${_} has no member (speaker ${speaker})`);
      return m.name;
    })
    .replace(/\{group\}/g, team.group);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const t = syncTeamNames({ force: true });
  console.log(JSON.stringify(t, null, 1));
}
