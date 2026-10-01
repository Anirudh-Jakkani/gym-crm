"use client";

import { MemberForm } from "@/components/members/member-form";
import { PageHeader } from "@/components/page-header";

export default function NewMemberPage() {
  return (
    <>
      <PageHeader title="Add member" description="Onboard a new member and sell their first plan." />
      <MemberForm />
    </>
  );
}
