"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { api, unwrap, type Schemas } from "@/lib/api/client";

export type DueReminder = Schemas["DueReminderOut"];
export type ReminderSettings = Schemas["ReminderSettingsOut"];
export type ReminderKind = Schemas["Kind"];
export type ReminderTemplate = Schemas["Template"];
export type ReminderHistoryItem = Schemas["HistoryItem"];

const keys = {
  all: ["reminders"] as const,
  due: (day?: string) => ["reminders", "due", day ?? "today"] as const,
  history: (page: number) => ["reminders", "history", page] as const,
  settings: ["reminders", "settings"] as const,
  notifications: ["notifications"] as const,
};

function onError(error: Error) {
  toast.error(error.message);
}

export function useDueReminders(day?: string, enabled = true) {
  return useQuery({
    queryKey: keys.due(day),
    queryFn: () =>
      unwrap(api.GET("/api/reminders/due", { params: { query: day ? { day } : {} } })),
    placeholderData: keepPreviousData,
    enabled,
  });
}

export function useRunReminders() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => unwrap(api.POST("/api/reminders/run")),
    onSuccess: (s) => {
      qc.invalidateQueries({ queryKey: keys.all });
      qc.invalidateQueries({ queryKey: keys.notifications });
      if (s.due === 0) toast.info("No reminders due today");
      else if (s.emailed === 0 && s.failed === 0)
        toast.info(
          s.already_sent
            ? "All reminder emails for today were already sent"
            : "None of today's members have an email address",
        );
      else if (s.failed) toast.error(`${s.emailed} sent, ${s.failed} failed`);
      else toast.success(`${s.emailed} reminder email${s.emailed === 1 ? "" : "s"} sent`);
    },
    onError,
  });
}

export function useLogWhatsApp() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["WhatsAppLogIn"]) =>
      unwrap(api.POST("/api/reminders/whatsapp", { body })),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
    onError,
  });
}

export function useReminderHistory(page: number) {
  return useQuery({
    queryKey: keys.history(page),
    queryFn: () =>
      unwrap(api.GET("/api/reminders/history", { params: { query: { page, page_size: 25 } } })),
    placeholderData: keepPreviousData,
  });
}

export function useReminderSettings() {
  return useQuery({
    queryKey: keys.settings,
    queryFn: () => unwrap(api.GET("/api/reminders/settings")),
  });
}

export function useUpdateReminderSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["ReminderSettingsUpdate"]) =>
      unwrap(api.PATCH("/api/reminders/settings", { body })),
    onSuccess: (s) => {
      qc.setQueryData(keys.settings, s);
      qc.invalidateQueries({ queryKey: ["reminders", "due"] });
      toast.success("Reminder settings saved");
    },
    onError,
  });
}

export async function previewTemplate(kind: ReminderKind, template: ReminderTemplate) {
  return unwrap(api.POST("/api/reminders/preview", { body: { kind, template } }));
}

// --- Notifications ----------------------------------------------------------

export function useNotifications() {
  return useQuery({
    queryKey: keys.notifications,
    queryFn: () => unwrap(api.GET("/api/notifications")),
    refetchInterval: 60_000,
  });
}

export function useMarkNotificationRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.POST("/api/notifications/{notification_id}/read", {
          params: { path: { notification_id: id } },
        }),
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.notifications }),
  });
}

export function useMarkAllNotificationsRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => unwrap(api.POST("/api/notifications/read-all")),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.notifications }),
  });
}
