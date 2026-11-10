// Golden generator for tests/fixtures/golden.json. Run from the cv-tailor (TS) repo:
//   ./node_modules/.bin/tsx ../cv-tailor-py/tests/fixtures/golden.ts ../cv-tailor-py
// render body copied verbatim from cv-tailor/src/agent.ts (minus span logging);
// ATS uses the real cv-tailor/src/ats.ts.
import { readFileSync, writeFileSync } from "node:fs";
import { runAtsChecks } from "../../../cv-tailor/src/ats";
import type { ParsedJD, Profile, Role } from "../../../cv-tailor/src/types";

interface Rewritten { summary: string; bullets: Record<string, string> }
const root = process.argv[2];

function render(profile: Profile, roles: Role[], text: Rewritten, jd: ParsedJD): string {
    const required = new Set(jd.requiredSkills.map((s) => s.toLowerCase()));
    const skills = [...profile.skills].sort(
      (a, b) => Number(required.has(b.toLowerCase())) - Number(required.has(a.toLowerCase())),
    );
    const lines = [
      `# ${profile.name}`,
      `${profile.email} | ${profile.location}`,
      "",
      "## Summary",
      text.summary,
      "",
      "## Experience",
    ];
    for (const r of roles) {
      lines.push(`### ${r.title}, ${r.company} (${r.start} - ${r.end})`);
      for (const a of r.achievements) lines.push(`- ${text.bullets[a.id] ?? a.text}`);
      lines.push("");
    }
    lines.push("## Skills", skills.join(", "), "", "## Education");
    for (const e of profile.education) lines.push(`${e.degree}, ${e.school}${e.year ? ` (${e.year})` : ""}`);
    return lines.join("\n");
}

const profile: Profile = JSON.parse(readFileSync(`${root}/data/profile.example.json`, "utf8"));
const renderCases = JSON.parse(readFileSync(`${root}/tests/fixtures/render_cases.json`, "utf8"));
const atsCases = JSON.parse(readFileSync(`${root}/tests/fixtures/ats_cases.json`, "utf8"));

const out = {
  _source: "Generated from cv-tailor (TypeScript) render + runAtsChecks. Do not edit by hand.",
  render: Object.fromEntries(renderCases.map((c: any) => {
    const cv = render(profile, profile.roles, c.rewritten, c.jd);
    return [c.id, { cv, bullets: cv.split("\n").filter((l) => l.startsWith("- ")).length, cvChars: cv.length, ats: runAtsChecks(cv, c.jd) }];
  })),
  ats: Object.fromEntries(atsCases.map((c: any) => [c.id, runAtsChecks(c.cv, { role: "", seniority: "", requiredSkills: c.requiredSkills, niceToHave: [] })])),
};
writeFileSync(`${root}/tests/fixtures/golden.json`, JSON.stringify(out, null, 2) + "\n");
