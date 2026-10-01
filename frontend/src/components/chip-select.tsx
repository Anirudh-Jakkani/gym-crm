"use client";

import type { Option } from "@/components/simple-select";
import { cn } from "@/lib/utils";

/** Single-choice chips; clicking the selected chip clears it. "" means none. */
export function ChipSelect({
  options,
  value,
  onChange,
  id,
}: {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  id?: string;
}) {
  return (
    <div id={id} role="radiogroup" className="flex flex-wrap gap-1.5">
      {options.map((o) => {
        const on = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={on}
            onClick={() => onChange(on ? "" : o.value)}
            className={cn(
              "rounded-full border px-3 py-1 text-sm transition-colors",
              on ? "border-primary bg-primary text-primary-foreground" : "hover:bg-muted",
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
