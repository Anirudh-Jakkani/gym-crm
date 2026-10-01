"use client";

import { DropletIcon, ShieldAlertIcon, TrendingUpIcon } from "lucide-react";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import type { components } from "@/lib/api/schema";

type PlanContent = components["schemas"]["PlanContent"];

function restLabel(seconds: number) {
  if (seconds < 60) return `${seconds}s rest`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}${s ? `:${String(s).padStart(2, "0")}` : ""} min rest`;
}

/** Read-only rendering of a workout + diet plan (member page and trainer preview). */
export function PlanView({ plan }: { plan: PlanContent }) {
  const d = plan.diet;
  const macros = [
    { label: "Protein", value: d.protein_g },
    { label: "Carbs", value: d.carbs_g },
    { label: "Fat", value: d.fat_g },
  ];

  return (
    <div className="grid gap-6">
      <p className="text-sm leading-relaxed">{plan.summary}</p>

      {plan.safety_notes.length > 0 && (
        <div className="flex gap-3 rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
          <ShieldAlertIcon className="mt-0.5 size-4 shrink-0 text-amber-600" aria-hidden />
          <ul className="grid gap-1">
            {plan.safety_notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </div>
      )}

      <section className="grid gap-2">
        <h3 className="font-semibold">Weekly workouts</h3>
        <Accordion className="rounded-lg border">
          {plan.weekly_schedule.map((day, i) => (
            <AccordionItem key={i} value={`day-${i}`} className="px-3">
              <AccordionTrigger>
                <span className="text-left">
                  <span className="font-medium">{day.day}</span>
                  <span className="block text-xs font-normal text-muted-foreground">
                    {day.focus} · {day.exercises.length} exercises
                  </span>
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="grid gap-3 pb-2 text-sm">
                  {day.warmup && (
                    <p className="text-muted-foreground">
                      <span className="font-medium text-foreground">Warm-up:</span> {day.warmup}
                    </p>
                  )}
                  <ol className="grid gap-2">
                    {day.exercises.map((ex, j) => (
                      <li key={j} className="rounded-md bg-muted/60 px-3 py-2">
                        <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                          <span className="font-medium">{ex.name}</span>
                          <span className="text-xs text-muted-foreground tabular-nums">
                            {ex.sets} × {ex.reps} · {restLabel(ex.rest_seconds)}
                          </span>
                        </div>
                        {ex.notes && <p className="text-xs text-muted-foreground">{ex.notes}</p>}
                      </li>
                    ))}
                  </ol>
                  {day.cooldown && (
                    <p className="text-muted-foreground">
                      <span className="font-medium text-foreground">Cool-down:</span> {day.cooldown}
                    </p>
                  )}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </section>

      <section className="grid gap-3">
        <h3 className="font-semibold">Diet</h3>
        <div className="grid grid-cols-4 gap-2 text-center">
          <div className="rounded-lg border p-2">
            <div className="text-lg font-semibold tabular-nums">{d.daily_calories}</div>
            <div className="text-xs text-muted-foreground">kcal / day</div>
          </div>
          {macros.map((m) => (
            <div key={m.label} className="rounded-lg border p-2">
              <div className="text-lg font-semibold tabular-nums">{m.value}g</div>
              <div className="text-xs text-muted-foreground">{m.label}</div>
            </div>
          ))}
        </div>
        <ul className="grid gap-2">
          {d.meals.map((meal, i) => (
            <li key={i} className="rounded-lg border p-3 text-sm">
              <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                <span className="font-medium">
                  {meal.name}
                  {meal.time && <span className="font-normal text-muted-foreground"> · {meal.time}</span>}
                </span>
                <span className="text-xs text-muted-foreground tabular-nums">
                  {meal.calories} kcal · {meal.protein_g}g protein
                </span>
              </div>
              <ul className="mt-1 list-disc pl-5 text-muted-foreground">
                {meal.items.map((item, j) => (
                  <li key={j}>{item}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
        {d.hydration && (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <DropletIcon className="size-4" aria-hidden />
            {d.hydration}
          </p>
        )}
        {d.notes.length > 0 && (
          <ul className="list-disc pl-5 text-sm text-muted-foreground">
            {d.notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        )}
      </section>

      {plan.progression && (
        <section className="flex gap-3 text-sm">
          <TrendingUpIcon className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
          <p>
            <span className="font-medium">Progressing: </span>
            {plan.progression}
          </p>
        </section>
      )}
    </div>
  );
}
