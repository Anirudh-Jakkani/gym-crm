"use client";

import {
  ArchiveIcon,
  ArchiveRestoreIcon,
  CheckIcon,
  ClipboardListIcon,
  MoreHorizontalIcon,
  PencilIcon,
  PlusIcon,
  SnowflakeIcon,
  Trash2Icon,
  UsersIcon,
} from "lucide-react";
import { useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { PageHeader } from "@/components/page-header";
import { PlanDialog } from "@/components/plans/plan-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { durationLabel, formatMoney } from "@/lib/format";
import { useDeletePlan, usePlans, useSavePlan, type Plan } from "@/lib/member-queries";
import { useCan, useCurrency } from "@/lib/queries";

function PlanCard({
  plan,
  canManage,
  onEdit,
  onDelete,
}: {
  plan: Plan;
  canManage: boolean;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const currency = useCurrency();
  const save = useSavePlan();
  const withTax = plan.price * (1 + plan.tax_pct / 100);

  return (
    <Card className={plan.is_active ? undefined : "opacity-60"}>
      <CardHeader>
        <CardDescription>{durationLabel(plan.duration_value, plan.duration_unit)}</CardDescription>
        <CardTitle className="text-base">{plan.name}</CardTitle>
        {canManage && (
          <CardAction>
            <DropdownMenu>
              <DropdownMenuTrigger
                render={<Button variant="ghost" size="icon-sm" aria-label="Plan actions" />}
              >
                <MoreHorizontalIcon />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={onEdit}>
                  <PencilIcon />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => save.mutate({ id: plan.id, is_active: !plan.is_active })}
                >
                  {plan.is_active ? <ArchiveIcon /> : <ArchiveRestoreIcon />}
                  {plan.is_active ? "Archive" : "Restore"}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem variant="destructive" onClick={onDelete}>
                  <Trash2Icon />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </CardAction>
        )}
      </CardHeader>
      <CardContent className="grid gap-3">
        <div>
          <span className="text-2xl font-semibold tracking-tight">
            {formatMoney(plan.price, currency)}
          </span>
          {plan.tax_pct > 0 && (
            <span className="text-xs text-muted-foreground">
              {" "}
              + {plan.tax_pct}% tax = {formatMoney(withTax, currency)}
            </span>
          )}
          {plan.joining_fee > 0 && (
            <div className="text-xs text-muted-foreground">
              + {formatMoney(plan.joining_fee, currency)} joining fee
            </div>
          )}
        </div>
        {plan.services.length > 0 && (
          <ul className="grid gap-1 text-sm">
            {plan.services.map((s) => (
              <li key={s} className="flex items-center gap-2">
                <CheckIcon className="size-3.5 text-muted-foreground" />
                {s}
              </li>
            ))}
          </ul>
        )}
        {plan.description && (
          <p className="text-xs text-muted-foreground">{plan.description}</p>
        )}
      </CardContent>
      <CardFooter className="mt-auto flex-wrap gap-2 border-t pt-3 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <UsersIcon className="size-3.5" />
          {plan.active_members} active
        </span>
        {plan.max_freeze_days > 0 && (
          <span className="flex items-center gap-1">
            <SnowflakeIcon className="size-3.5" />
            {plan.max_freeze_days} freeze days
          </span>
        )}
        {!plan.is_active && <Badge variant="outline">Archived</Badge>}
      </CardFooter>
    </Card>
  );
}

export default function PlansPage() {
  const can = useCan();
  const [showArchived, setShowArchived] = useState(false);
  const plans = usePlans(showArchived);
  const remove = useDeletePlan();
  const [editing, setEditing] = useState<Plan | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState<Plan | null>(null);

  const openDialog = (plan: Plan | null) => {
    setEditing(plan);
    setDialogOpen(true);
  };

  return (
    <>
      <PageHeader
        title="Plans"
        description="Membership plans your gym sells. Any duration, any price."
      >
        <div className="flex items-center gap-2">
          <Switch id="archived" checked={showArchived} onCheckedChange={setShowArchived} />
          <Label htmlFor="archived" className="text-sm font-normal">
            Show archived
          </Label>
        </div>
        {can.manage && (
          <Button onClick={() => openDialog(null)}>
            <PlusIcon />
            New plan
          </Button>
        )}
      </PageHeader>

      {plans.isPending ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-56 rounded-xl" />
          ))}
        </div>
      ) : plans.data?.length ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {plans.data.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              canManage={can.manage}
              onEdit={() => openDialog(plan)}
              onDelete={() => setDeleting(plan)}
            />
          ))}
        </div>
      ) : (
        <Empty className="border">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <ClipboardListIcon />
            </EmptyMedia>
            <EmptyTitle>No plans yet</EmptyTitle>
            <EmptyDescription>
              Create your first membership plan: monthly, quarterly, yearly or anything custom.
            </EmptyDescription>
          </EmptyHeader>
          {can.manage && (
            <EmptyContent>
              <Button onClick={() => openDialog(null)}>
                <PlusIcon />
                Create a plan
              </Button>
            </EmptyContent>
          )}
        </Empty>
      )}

      <PlanDialog plan={editing} open={dialogOpen} onOpenChange={setDialogOpen} />
      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(o) => !o && setDeleting(null)}
        title={`Delete ${deleting?.name}?`}
        description="Plans that have been sold can't be deleted, only archived."
        confirmLabel="Delete plan"
        pending={remove.isPending}
        onConfirm={() =>
          deleting &&
          remove.mutate(deleting.id, {
            onSuccess: () => setDeleting(null),
            onError: () => setDeleting(null),
          })
        }
      />
    </>
  );
}
