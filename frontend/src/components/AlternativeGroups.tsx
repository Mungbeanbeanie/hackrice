import type { Group as GroupId, Product } from "@/api/client";
import ResultCard from "@/components/ResultCard";

interface GroupDef {
  id: GroupId;
  title: string;
  description: string;
}

// Order and copy come straight from the Organic design handoff — groups are
// ordered by equivalence, not by value; ranking within a group is the
// backend's job (already sorted by value_score before this ever gets here).
const GROUPS: GroupDef[] = [
  {
    id: "same_spec",
    title: "Same spec, no logo",
    description: "Matches the original's materials and construction. Different label, different price.",
  },
  {
    id: "same_job",
    title: "Different build, same job",
    description: "Another way of reaching the same outcome — worth it when the alternative route is better.",
  },
  {
    id: "clears_floor",
    title: "Cheapest that clears quality",
    description: "Lowest price still above the quality floor. Spec match drops; we say so rather than hide it.",
  },
];

export const GROUP_ORDER: GroupId[] = GROUPS.map((g) => g.id);

interface Props {
  groups: Record<GroupId, Product[]>;
  baselinePrice: number | null;
  baselineLabel: string;
  selectedId: string | null;
  onCompare: (product: Product) => void;
  onSelect: (product: Product) => void;
}

export default function AlternativeGroups({
  groups,
  baselinePrice,
  baselineLabel,
  selectedId,
  onCompare,
  onSelect,
}: Props) {
  return (
    <div className="flex flex-col" style={{ gap: "30px" }}>
      {GROUPS.map((g) => {
        const products = groups[g.id];
        if (!products.length) return null;
        return (
          <section key={g.id}>
            <div style={{ marginBottom: "var(--space-3)" }}>
              <h3 className="flex items-center gap-2 flex-wrap" style={{ fontSize: "17px", lineHeight: 1.25 }}>
                <span className="w-[9px] h-[9px] rounded-full bg-accent flex-shrink-0" />
                {g.title}
                <span
                  className="bg-surface text-neutral-700 rounded-full font-bold"
                  style={{ fontFamily: "var(--font-body)", fontSize: "12px", padding: "2px var(--space-2)" }}
                >
                  {products.length} {products.length === 1 ? "result" : "results"}
                </span>
              </h3>
              <p
                className="text-neutral-700"
                style={{ marginTop: "var(--space-1)", marginLeft: "var(--space-4)", fontSize: "13.5px" }}
              >
                {g.description}
              </p>
            </div>
            <div className="flex flex-col gap-3">
              {products.map((p) => (
                <ResultCard
                  key={p.id}
                  product={p}
                  baselinePrice={baselinePrice}
                  baselineLabel={baselineLabel}
                  selected={p.id === selectedId}
                  onCompare={onCompare}
                  onSelect={onSelect}
                />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
