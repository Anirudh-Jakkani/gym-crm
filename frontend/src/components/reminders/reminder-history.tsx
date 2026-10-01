"use client";

import { ChevronLeftIcon, ChevronRightIcon, MailIcon, MessageCircleIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useReminderHistory } from "@/lib/reminder-queries";
import { cn } from "@/lib/utils";

function offsetLabel(days: number) {
  if (days === 0) return "On end date";
  const n = Math.abs(days);
  return `${n} day${n === 1 ? "" : "s"} ${days > 0 ? "before" : "after"}`;
}

function formatWhen(iso: string) {
  return new Date(iso).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function ReminderHistory() {
  const [page, setPage] = useState(1);
  const history = useReminderHistory(page);

  if (history.isPending) return <Skeleton className="h-64 w-full rounded-xl" />;
  const data = history.data;
  if (!data?.total) {
    return (
      <p className="py-10 text-center text-sm text-muted-foreground">
        No reminders have been sent yet.
      </p>
    );
  }
  const pages = Math.ceil(data.total / data.page_size);

  return (
    <Card className="py-0">
      <Table className={cn(history.isPlaceholderData && "opacity-60")}>
        <TableHeader>
          <TableRow>
            <TableHead className="pl-4">Member</TableHead>
            <TableHead>Reminder</TableHead>
            <TableHead>Channel</TableHead>
            <TableHead className="hidden md:table-cell">Sent</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.items.map((h) => (
            <TableRow key={h.id}>
              <TableCell className="pl-4">
                <Link href={`/members/${h.member_id}`} className="font-medium hover:underline">
                  {h.member_name}
                </Link>
                <div className="text-xs text-muted-foreground">{h.plan_name}</div>
              </TableCell>
              <TableCell className="text-muted-foreground">{offsetLabel(h.offset_days)}</TableCell>
              <TableCell>
                <span className="flex items-center gap-1.5">
                  {h.channel === "email" ? (
                    <MailIcon className="size-3.5" />
                  ) : (
                    <MessageCircleIcon className="size-3.5" />
                  )}
                  {h.channel === "email" ? "Email" : "WhatsApp"}
                  {h.status === "failed" && (
                    <span className="text-xs text-destructive" title={h.error ?? undefined}>
                      failed
                    </span>
                  )}
                  {h.status === "pending" && (
                    <span className="text-xs text-muted-foreground">sending…</span>
                  )}
                </span>
                <div className="text-xs text-muted-foreground">
                  {h.sent_by_name ? `by ${h.sent_by_name}` : "automatic"}
                </div>
              </TableCell>
              <TableCell className="hidden text-muted-foreground md:table-cell">
                {formatWhen(h.sent_at)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <div className="flex items-center justify-between border-t px-4 py-2 text-sm text-muted-foreground">
        <span>{data.total} reminders</span>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Previous page"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            <ChevronLeftIcon />
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Next page"
            disabled={page >= pages}
            onClick={() => setPage(page + 1)}
          >
            <ChevronRightIcon />
          </Button>
        </div>
      </div>
    </Card>
  );
}
