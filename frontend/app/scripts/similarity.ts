export const normalize = (s?: string) => (s || "").toLowerCase().replace(/[^a-z0-9\s]/g, "").trim();

export const getTrigrams = (s: string) => {
  const out = new Set<string>();
  const str = `  ${s}  `;
  for (let i = 0; i < str.length - 2; i++) out.add(str.slice(i, i + 3));
  return out;
};

export const jaccard = (a: Set<string>, b: Set<string>) => {
  let inter = 0;
  for (const item of a) if (b.has(item)) inter++;
  const union = a.size + b.size - inter;
  return union === 0 ? 0 : inter / union;
};

export const extractPostcodeArea = (s: string) => {
  const m = s.match(/\b([a-z]{1,2})\d/i);
  return m ? m[1].toLowerCase() : null;
};

export const computeSimilarity = (a?: string, b?: string) => {
  const A = normalize(a);
  const B = normalize(b);
  if (!A || !B) return 0;
  if (A === B) return 1;

  const areaA = extractPostcodeArea(A);
  const areaB = extractPostcodeArea(B);
  if (areaA && areaB && areaA === areaB) {
    return 0.95;
  }

  if (areaA && B.includes(areaA) && !areaB) return 0.8;
  if (areaB && A.includes(areaB) && !areaA) return 0.8;

  const ta = getTrigrams(A);
  const tb = getTrigrams(B);
  return jaccard(ta, tb);
};

export default {
  normalize,
  getTrigrams,
  jaccard,
  extractPostcodeArea,
  computeSimilarity,
};
