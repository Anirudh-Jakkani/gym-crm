"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { PageHeader } from "@/components/page-header";
import { BranchesSettings } from "@/components/settings/branches-settings";
import { GeneralSettings } from "@/components/settings/general-settings";
import { StaffSettings } from "@/components/settings/staff-settings";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const TABS = ["general", "branches", "staff"] as const;

function SettingsTabs() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const requested = params.get("tab");
  const tab = TABS.includes(requested as (typeof TABS)[number]) ? requested! : "general";

  return (
    <Tabs
      value={tab}
      onValueChange={(v, details) => {
        // Base UI also reports automatic fallbacks while tabs mount; only follow user clicks.
        if (details.reason === "none") router.replace(`${pathname}?tab=${v}`, { scroll: false });
      }}
    >
      <TabsList>
        <TabsTrigger value="general">General</TabsTrigger>
        <TabsTrigger value="branches">Branches</TabsTrigger>
        <TabsTrigger value="staff">Staff</TabsTrigger>
      </TabsList>
      <TabsContent value="general" className="pt-4">
        <GeneralSettings />
      </TabsContent>
      <TabsContent value="branches" className="pt-4">
        <BranchesSettings />
      </TabsContent>
      <TabsContent value="staff" className="pt-4">
        <StaffSettings />
      </TabsContent>
    </Tabs>
  );
}

export default function SettingsPage() {
  return (
    <>
      <PageHeader title="Settings" description="Your gym's details, branches and team." />
      <Suspense>
        <SettingsTabs />
      </Suspense>
    </>
  );
}
