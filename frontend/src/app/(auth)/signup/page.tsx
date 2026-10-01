"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { TextField } from "@/components/form-fields";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FieldGroup } from "@/components/ui/field";
import { Spinner } from "@/components/ui/spinner";
import { api, unwrap } from "@/lib/api/client";
import { keys, toMe } from "@/lib/queries";

const schema = z.object({
  gym_name: z.string().trim().min(2, "Enter your gym's name").max(120),
  name: z.string().trim().min(2, "Enter your name").max(120),
  email: z.email("Enter a valid email"),
  phone: z.string().trim().max(30).optional(),
  password: z.string().min(8, "Use at least 8 characters").max(128),
});

export default function SignupPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: { gym_name: "", name: "", email: "", phone: "", password: "" },
  });

  const signup = useMutation({
    mutationFn: ({ phone, ...rest }: z.infer<typeof schema>) =>
      unwrap(api.POST("/api/auth/signup", { body: { ...rest, phone: phone || null } })),
    onSuccess: (auth) => {
      qc.clear();
      qc.setQueryData(keys.me, toMe(auth));
      router.replace("/");
    },
  });

  const { errors } = form.formState;
  return (
    <Card>
      <CardHeader className="text-center">
        <CardTitle className="text-xl">Set up your gym</CardTitle>
        <CardDescription>Create your account to start managing members</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit((v) => signup.mutate(v))} noValidate>
          <FieldGroup>
            {signup.error && (
              <Alert variant="destructive">
                <AlertDescription>{signup.error.message}</AlertDescription>
              </Alert>
            )}
            <TextField
              label="Gym name"
              placeholder="Iron Temple Fitness"
              error={errors.gym_name}
              {...form.register("gym_name")}
            />
            <TextField
              label="Your name"
              autoComplete="name"
              error={errors.name}
              {...form.register("name")}
            />
            <TextField
              label="Email"
              type="email"
              autoComplete="email"
              error={errors.email}
              {...form.register("email")}
            />
            <TextField
              label="Phone (optional)"
              type="tel"
              autoComplete="tel"
              error={errors.phone}
              {...form.register("phone")}
            />
            <TextField
              label="Password"
              type="password"
              autoComplete="new-password"
              description="At least 8 characters"
              error={errors.password}
              {...form.register("password")}
            />
            <Button type="submit" disabled={signup.isPending} className="w-full">
              {signup.isPending && <Spinner />}
              Create gym
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link href="/login" className="text-foreground underline underline-offset-4">
                Log in
              </Link>
            </p>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  );
}
