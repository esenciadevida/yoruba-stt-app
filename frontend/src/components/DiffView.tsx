"use client";

interface DiffViewProps {
  original: string;
  corrected: string;
}

function computeDiff(original: string, corrected: string) {
  const origWords = original.split(/(\s+)/);
  const corrWords = corrected.split(/(\s+)/);
  const maxLen = Math.max(origWords.length, corrWords.length);
  const result: Array<{ orig: string; corr: string; type: "same" | "changed" | "added" | "removed" }> = [];

  let i = 0, j = 0;
  while (i < origWords.length || j < corrWords.length) {
    const ow = origWords[i] || "";
    const cw = corrWords[j] || "";

    if (ow === cw) {
      result.push({ orig: ow, corr: cw, type: "same" });
      i++; j++;
    } else if (ow.trim() === "" || cw.trim() === "") {
      result.push({ orig: ow, corr: cw, type: ow.trim() === "" ? "added" : "removed" });
      if (ow.trim() === "") j++;
      else i++;
    } else {
      result.push({ orig: ow, corr: cw, type: "changed" });
      i++; j++;
    }
  }

  return result;
}

export function DiffView({ original, corrected }: DiffViewProps) {
  const diff = computeDiff(original, corrected);

  return (
    <div className="grid grid-cols-2 gap-3">
      {/* Original */}
      <div className="p-3 rounded-xl bg-red-50/50 dark:bg-red-500/5 border border-red-200/40 dark:border-red-400/10">
        <p className="text-[10px] text-red-600 dark:text-red-400 uppercase tracking-wider font-semibold mb-2">Original</p>
        <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
          {diff.map((d, i) => (
            <span
              key={i}
              className={d.type === "changed" || d.type === "removed"
                ? "bg-red-200 dark:bg-red-500/20 text-red-700 dark:text-red-400 line-through px-0.5 rounded"
                : ""}
            >
              {d.orig}
            </span>
          ))}
        </p>
      </div>

      {/* Corrected */}
      <div className="p-3 rounded-xl bg-green-50/50 dark:bg-green-500/5 border border-green-200/40 dark:border-green-400/10">
        <p className="text-[10px] text-green-600 dark:text-green-400 uppercase tracking-wider font-semibold mb-2">Corrected</p>
        <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
          {diff.map((d, i) => (
            <span
              key={i}
              className={d.type === "changed" || d.type === "added"
                ? "bg-green-200 dark:bg-green-500/20 text-green-700 dark:text-green-400 font-medium px-0.5 rounded"
                : ""}
            >
              {d.corr}
            </span>
          ))}
        </p>
      </div>
    </div>
  );
}
