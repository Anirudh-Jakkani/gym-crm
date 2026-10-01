"use client";

import { useParams } from "next/navigation";

import { MemberForm } from "@/components/members/member-form";
import { PageHeader } from "@/components/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { useMember } from "@/lib/member-queries";

export default function EditMemberPage() {
  const { id } = useParams<{ id: string }>();
  const member = useMember(id);

  if (member.isPending) return <Skeleton className="h-[600px] w-full rounded-xl" />;
  if (member.isError) return <p className="text-sm text-destructive">{member.error.message}</p>;

  return (
    <>
      <PageHeader title={`Edit ${member.data.name}`} />
      <MemberForm member={member.data} />
    </>
  );
}
