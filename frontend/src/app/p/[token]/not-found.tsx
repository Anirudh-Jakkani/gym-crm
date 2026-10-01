export default function PreviewNotFound() {
  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-2 p-6 text-center">
      <h1 className="text-lg font-semibold">This link isn&apos;t valid anymore</h1>
      <p className="max-w-sm text-sm text-muted-foreground">
        Ask your gym for a new link to see your membership and plan.
      </p>
    </main>
  );
}
