"""Shape of a workout + diet plan. Used as Claude's structured-output schema, for trainer
edits, and for the member preview page. Keep it simple: structured outputs support a
subset of JSON Schema, and every field here is something a trainer can edit in the UI."""

from pydantic import BaseModel


class Exercise(BaseModel):
    name: str
    sets: int
    reps: str  # "8-10", "12", "30 sec"
    rest_seconds: int
    notes: str  # form cues or substitutions; may be empty


class WorkoutDay(BaseModel):
    day: str  # "Day 1 – Monday"
    focus: str  # "Lower body strength"
    warmup: str
    exercises: list[Exercise]
    cooldown: str


class Meal(BaseModel):
    name: str  # "Breakfast"
    time: str  # "8:00 AM"
    items: list[str]
    calories: int
    protein_g: int


class DietPlan(BaseModel):
    daily_calories: int
    protein_g: int
    carbs_g: int
    fat_g: int
    meals: list[Meal]
    hydration: str
    notes: list[str]


class PlanContent(BaseModel):
    summary: str  # two or three sentences addressed to the member
    weekly_schedule: list[WorkoutDay]
    diet: DietPlan
    progression: str  # how to progress over the next 4 weeks
    safety_notes: list[str]
