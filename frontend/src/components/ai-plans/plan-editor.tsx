"use client";

import { PlusIcon, Trash2Icon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import type { PlanContent } from "@/lib/ai-plan-queries";

type Day = PlanContent["weekly_schedule"][number];
type Meal = PlanContent["diet"]["meals"][number];

const lines = (s: string) => s.split("\n").map((l) => l.trim()).filter(Boolean);
const toInt = (s: string) => (s === "" ? 0 : Math.max(0, Math.round(Number(s) || 0)));

/** Edits a plan in place: every change produces a new PlanContent via onChange. */
export function PlanEditor({
  value,
  onChange,
}: {
  value: PlanContent;
  onChange: (value: PlanContent) => void;
}) {
  const edit = (fn: (draft: PlanContent) => void) => {
    const next = structuredClone(value);
    fn(next);
    onChange(next);
  };

  const mealCalories = value.diet.meals.reduce((sum, m) => sum + m.calories, 0);

  return (
    <Tabs defaultValue="workout">
      <TabsList>
        <TabsTrigger value="workout">Workouts</TabsTrigger>
        <TabsTrigger value="diet">Diet</TabsTrigger>
        <TabsTrigger value="notes">Summary & notes</TabsTrigger>
      </TabsList>

      <TabsContent value="workout" className="grid gap-4 pt-4">
        {value.weekly_schedule.map((day, d) => (
          <Card key={d} size="sm">
            <CardHeader>
              <CardTitle className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                <Input
                  aria-label="Day name"
                  value={day.day}
                  onChange={(e) => edit((p) => void (p.weekly_schedule[d].day = e.target.value))}
                />
                <Input
                  aria-label="Focus"
                  value={day.focus}
                  onChange={(e) => edit((p) => void (p.weekly_schedule[d].focus = e.target.value))}
                />
              </CardTitle>
              <CardAction>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  aria-label={`Remove ${day.day}`}
                  onClick={() => edit((p) => void p.weekly_schedule.splice(d, 1))}
                >
                  <Trash2Icon />
                </Button>
              </CardAction>
            </CardHeader>
            <CardContent className="grid gap-3">
              <Field>
                <FieldLabel>Warm-up</FieldLabel>
                <Input
                  value={day.warmup}
                  onChange={(e) => edit((p) => void (p.weekly_schedule[d].warmup = e.target.value))}
                />
              </Field>
              <div className="grid gap-2">
                <div className="hidden grid-cols-[1fr_4rem_5rem_5rem_2rem] gap-2 text-xs text-muted-foreground sm:grid">
                  <span>Exercise</span>
                  <span>Sets</span>
                  <span>Reps</span>
                  <span>Rest (s)</span>
                </div>
                {day.exercises.map((ex, e) => (
                  <div key={e} className="grid gap-1 rounded-md border p-2 sm:border-0 sm:p-0">
                    <div className="grid grid-cols-[1fr_4rem_5rem_5rem_2rem] gap-2">
                      <Input
                        aria-label="Exercise"
                        value={ex.name}
                        onChange={(ev) => edit((p) => void (p.weekly_schedule[d].exercises[e].name = ev.target.value))}
                      />
                      <Input
                        aria-label="Sets"
                        type="number"
                        min={1}
                        value={ex.sets}
                        onChange={(ev) => edit((p) => void (p.weekly_schedule[d].exercises[e].sets = toInt(ev.target.value)))}
                      />
                      <Input
                        aria-label="Reps"
                        value={ex.reps}
                        onChange={(ev) => edit((p) => void (p.weekly_schedule[d].exercises[e].reps = ev.target.value))}
                      />
                      <Input
                        aria-label="Rest in seconds"
                        type="number"
                        min={0}
                        step={15}
                        value={ex.rest_seconds}
                        onChange={(ev) =>
                          edit((p) => void (p.weekly_schedule[d].exercises[e].rest_seconds = toInt(ev.target.value)))
                        }
                      />
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        aria-label={`Remove ${ex.name}`}
                        onClick={() => edit((p) => void p.weekly_schedule[d].exercises.splice(e, 1))}
                      >
                        <Trash2Icon />
                      </Button>
                    </div>
                    <Input
                      aria-label="Exercise notes"
                      placeholder="Notes / form cues (optional)"
                      className="h-7 text-xs"
                      value={ex.notes}
                      onChange={(ev) => edit((p) => void (p.weekly_schedule[d].exercises[e].notes = ev.target.value))}
                    />
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  className="w-fit"
                  onClick={() =>
                    edit((p) =>
                      p.weekly_schedule[d].exercises.push({ name: "", sets: 3, reps: "10", rest_seconds: 60, notes: "" }),
                    )
                  }
                >
                  <PlusIcon />
                  Add exercise
                </Button>
              </div>
              <Field>
                <FieldLabel>Cool-down</FieldLabel>
                <Input
                  value={day.cooldown}
                  onChange={(e) => edit((p) => void (p.weekly_schedule[d].cooldown = e.target.value))}
                />
              </Field>
            </CardContent>
          </Card>
        ))}
        <Button
          variant="outline"
          className="w-fit"
          onClick={() =>
            edit((p) =>
              p.weekly_schedule.push({
                day: `Day ${p.weekly_schedule.length + 1}`,
                focus: "",
                warmup: "",
                exercises: [],
                cooldown: "",
              } satisfies Day),
            )
          }
        >
          <PlusIcon />
          Add workout day
        </Button>
      </TabsContent>

      <TabsContent value="diet" className="grid gap-4 pt-4">
        <Card size="sm">
          <CardContent>
            <FieldGroup>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {(
                  [
                    ["daily_calories", "Calories / day"],
                    ["protein_g", "Protein (g)"],
                    ["carbs_g", "Carbs (g)"],
                    ["fat_g", "Fat (g)"],
                  ] as const
                ).map(([key, label]) => (
                  <Field key={key}>
                    <FieldLabel htmlFor={`diet-${key}`}>{label}</FieldLabel>
                    <Input
                      id={`diet-${key}`}
                      type="number"
                      min={0}
                      value={value.diet[key]}
                      onChange={(e) => edit((p) => void (p.diet[key] = toInt(e.target.value)))}
                    />
                  </Field>
                ))}
              </div>
              {mealCalories !== value.diet.daily_calories && (
                <FieldDescription>
                  Meals add up to {mealCalories} kcal ({mealCalories > value.diet.daily_calories ? "over" : "under"} the
                  daily target by {Math.abs(mealCalories - value.diet.daily_calories)}).
                </FieldDescription>
              )}
              <Field>
                <FieldLabel htmlFor="diet-hydration">Hydration</FieldLabel>
                <Input
                  id="diet-hydration"
                  value={value.diet.hydration}
                  onChange={(e) => edit((p) => void (p.diet.hydration = e.target.value))}
                />
              </Field>
            </FieldGroup>
          </CardContent>
        </Card>

        {value.diet.meals.map((meal, m) => (
          <Card key={m} size="sm">
            <CardHeader>
              <CardTitle className="grid grid-cols-2 gap-2">
                <Input
                  aria-label="Meal name"
                  value={meal.name}
                  onChange={(e) => edit((p) => void (p.diet.meals[m].name = e.target.value))}
                />
                <Input
                  aria-label="Time"
                  value={meal.time}
                  onChange={(e) => edit((p) => void (p.diet.meals[m].time = e.target.value))}
                />
              </CardTitle>
              <CardAction>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  aria-label={`Remove ${meal.name}`}
                  onClick={() => edit((p) => void p.diet.meals.splice(m, 1))}
                >
                  <Trash2Icon />
                </Button>
              </CardAction>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-[1fr_8rem]">
              <Field>
                <FieldLabel>Foods (one per line)</FieldLabel>
                <Textarea
                  rows={3}
                  value={meal.items.join("\n")}
                  onChange={(e) => edit((p) => void (p.diet.meals[m].items = e.target.value.split("\n")))}
                  onBlur={() => edit((p) => void (p.diet.meals[m].items = lines(meal.items.join("\n"))))}
                />
              </Field>
              <div className="grid content-start gap-3">
                <Field>
                  <FieldLabel>kcal</FieldLabel>
                  <Input
                    type="number"
                    min={0}
                    value={meal.calories}
                    onChange={(e) => edit((p) => void (p.diet.meals[m].calories = toInt(e.target.value)))}
                  />
                </Field>
                <Field>
                  <FieldLabel>Protein (g)</FieldLabel>
                  <Input
                    type="number"
                    min={0}
                    value={meal.protein_g}
                    onChange={(e) => edit((p) => void (p.diet.meals[m].protein_g = toInt(e.target.value)))}
                  />
                </Field>
              </div>
            </CardContent>
          </Card>
        ))}
        <Button
          variant="outline"
          className="w-fit"
          onClick={() =>
            edit((p) =>
              p.diet.meals.push({ name: "Snack", time: "", items: [], calories: 0, protein_g: 0 } satisfies Meal),
            )
          }
        >
          <PlusIcon />
          Add meal
        </Button>
      </TabsContent>

      <TabsContent value="notes" className="pt-4">
        <Card size="sm">
          <CardContent>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="plan-summary">Summary for the member</FieldLabel>
                <Textarea
                  id="plan-summary"
                  rows={3}
                  value={value.summary}
                  onChange={(e) => edit((p) => void (p.summary = e.target.value))}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="plan-safety">Safety notes (one per line)</FieldLabel>
                <Textarea
                  id="plan-safety"
                  rows={3}
                  value={value.safety_notes.join("\n")}
                  onChange={(e) => edit((p) => void (p.safety_notes = e.target.value.split("\n")))}
                  onBlur={() => edit((p) => void (p.safety_notes = lines(value.safety_notes.join("\n"))))}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="plan-diet-notes">Diet notes (one per line)</FieldLabel>
                <Textarea
                  id="plan-diet-notes"
                  rows={3}
                  value={value.diet.notes.join("\n")}
                  onChange={(e) => edit((p) => void (p.diet.notes = e.target.value.split("\n")))}
                  onBlur={() => edit((p) => void (p.diet.notes = lines(value.diet.notes.join("\n"))))}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="plan-progression">How to progress</FieldLabel>
                <Textarea
                  id="plan-progression"
                  rows={2}
                  value={value.progression}
                  onChange={(e) => edit((p) => void (p.progression = e.target.value))}
                />
              </Field>
            </FieldGroup>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}

/** Problems that should block saving. */
export function planProblems(plan: PlanContent): string[] {
  const problems: string[] = [];
  if (!plan.summary.trim()) problems.push("Add a short summary for the member.");
  if (!plan.weekly_schedule.length) problems.push("Add at least one workout day.");
  plan.weekly_schedule.forEach((d) => {
    if (d.exercises.some((e) => !e.name.trim())) problems.push(`${d.day}: every exercise needs a name.`);
  });
  if (plan.diet.meals.some((m) => !m.name.trim())) problems.push("Every meal needs a name.");
  return problems;
}
