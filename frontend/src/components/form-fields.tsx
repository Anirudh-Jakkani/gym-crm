"use client";

import type { FieldError as RHFFieldError } from "react-hook-form";

import { Field, FieldDescription, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";

type TextFieldProps = React.ComponentProps<"input"> & {
  label?: string;
  error?: RHFFieldError;
  description?: string;
};

/** Label + input + error message, wired for react-hook-form's register(). */
export function TextField({ label, error, description, id, name, ...props }: TextFieldProps) {
  const inputId = id ?? name;
  return (
    <Field data-invalid={!!error}>
      {label && <FieldLabel htmlFor={inputId}>{label}</FieldLabel>}
      <Input id={inputId} name={name} aria-invalid={!!error} {...props} />
      {description && !error && <FieldDescription>{description}</FieldDescription>}
      <FieldError errors={[error]} />
    </Field>
  );
}
