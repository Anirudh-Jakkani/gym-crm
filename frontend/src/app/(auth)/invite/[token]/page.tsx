"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { TextField } from "@/components/form-fields";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FieldGroup } from "@/components/ui/field";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { api, unwrap } from "@/lib/api/client";
import { keys, ROLE_LABELS, toMe } from "@/lib/queries";

const schema = z.object({
  name: z.string().trim().max(120).optional(),
  password: z.string().min(8, "Use at least 8 characters").max(128),
});

export default function AcceptInvitePage() {
  const { token } = useParams<{ token: string }>();
  const router = useRouter();
  const qc = useQueryClient();

  const invite = useQuery({
    queryKey: ["invite", token],
    queryFn: () =>
      unwrap(api.GET("/api/auth/invites/{token}", { params: { path: { token } } })),
  });
  const existing = invite.data?.existing_user ?? false;

  const form = useForm({
    resolver: zodResolver(
      schema.refine((v) => existing || (v.name?.length ?? 0) >= 2, {
        path: ["name"],
        message: "Enter your name",
      }),
    ),
    defaultValues: { name: "", password: "" },
  });

  const accept = useMutation({
    mutationFn: (v: z.infer<typeof schema>) =>
      unwrap(
        api.POST("/api/auth/invites/{token}/accept", {
          params: { path: { token } },
          body: { name: existing ? null : v.name, password: v.password },
        }),
      ),
    onSuccess: (auth) => {
      qc.clear();
      qc.setQueryData(keys.me, toMe(auth));
      router.replace("/");
    },
  });

  if (invite.isPending) {
    return <Skeleton className="h-80 w-full rounded-xl" />;
  }
  if (invite.isError) {
    return (
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-xl">Invite not valid</CardTitle>
          <CardDescription>{invite.error.message}</CardDescription>
        </CardHeader>
        <CardContent className="text-center text-sm">
          Ask your gym owner for a new link, or{" "}
          <Link href="/login" className="underline underline-offset-4">
            log in
          </Link>
          .
        </CardContent>
      </Card>
    );
  }

  const { errors } = form.formState;
  return (
    <Card>
      <CardHeader className="text-center">
        <CardTitle className="text-xl">Join {invite.data.gym_name}</CardTitle>
        <CardDescription>
          You&apos;ve been invited as {ROLE_LABELS[invite.data.role]} ({invite.data.email})
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit((v) => accept.mutate(v))} noValidate>
          <FieldGroup>
            {accept.error && (
              <Alert variant="destructive">
                <AlertDescription>{accept.error.message}</AlertDescription>
              </Alert>
            )}
            {!existing && (
              <TextField
                label="Your name"
                autoComplete="name"
                error={errors.name}
                {...form.register("name")}
              />
            )}
            <TextField
              label={existing ? "Your existing password" : "Choose a password"}
              type="password"
              autoComplete={existing ? "current-password" : "new-password"}
              error={errors.password}
              {...form.register("password")}
            />
            <Button type="submit" disabled={accept.isPending} className="w-full">
              {accept.isPending && <Spinner />}
              Accept invite
            </Button>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  );
}
