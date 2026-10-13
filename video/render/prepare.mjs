// Shared inputs every render needs, refreshed when their sources change:
//   video/data/team_names.json   <- notebooks/final/team.json        (names; "[Name]" placeholders)
//   video/subtitles/*.srt|ass|json <- video/timeline/timeline.json, subtitles/overrides.json, team names
// Called by render.mjs, render_all.mjs, snap.mjs and compose_block.mjs. Cheap when nothing changed.
import { existsSync, statSync } from 'node:fs';
import path from 'node:path';
import { syncTeamNames, TEAM_JSON, TEAM_NAMES_JSON, VIDEO_ROOT } from './team.mjs';
import { writeAll, DEFAULT_TIMELINE, DEFAULT_OVERRIDES } from '../subtitles/build_subs.mjs';

const mtime = (f) => (existsSync(f) ? statSync(f).mtimeMs : 0);

export function prepare({ quiet = false, force = false } = {}) {
  syncTeamNames({ quiet });
  const words = path.join(VIDEO_ROOT, 'subtitles', 'words.json');
  const builder = path.join(VIDEO_ROOT, 'subtitles', 'build_subs.mjs');
  const newest = Math.max(mtime(DEFAULT_TIMELINE), mtime(DEFAULT_OVERRIDES), mtime(TEAM_JSON), mtime(TEAM_NAMES_JSON), mtime(builder));
  if (force || mtime(words) < newest) {
    const r = writeAll();
    if (!quiet) console.log(`subtitles rebuilt: ${r.cues} captions, total ${r.tl.total} s${r.warnings.length ? ` (${r.warnings.length} reading-speed warning(s): node video/subtitles/build_subs.mjs)` : ''}`);
  }
}
