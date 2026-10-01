"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { api, unwrap, type Schemas } from "@/lib/api/client";

export type CheckUp = Schemas["CheckUpOut"];
export type CheckUpInput = Schemas["CheckUpIn"];
export type DueCheckUp = Schemas["DueCheckUp"];

const keys = {
  forMember: (memberId: string) => ["checkups", "member", memberId] as const,
  due: (scope: string, page: number) => ["checkups", "due", scope, page] as const,
  all: ["checkups"] as const,
};

function onError(error: Error) {
  toast.error(error.message);
}

export function useMemberCheckups(memberId: string) {
  return useQuery({
    queryKey: keys.forMember(memberId),
    queryFn: () =>
      unwrap(
        api.GET("/api/members/{member_id}/checkups", {
          params: { path: { member_id: memberId } },
        }),
      ),
  });
}

export function useDueCheckups(scope: "mine" | "all", page: number) {
  return useQuery({
    queryKey: keys.due(scope, page),
    queryFn: () =>
      unwrap(api.GET("/api/checkups/due", { params: { query: { scope, page, page_size: 25 } } })),
    placeholderData: keepPreviousData,
  });
}

/** Refresh check-up lists, the due list and the member (last check-up date, height). */
function useInvalidate() {
  const qc = useQueryClient();
  return (memberId: string) => {
    qc.invalidateQueries({ queryKey: keys.all });
    qc.invalidateQueries({ queryKey: ["members", "detail", memberId] });
  };
}

export function useSaveCheckup(memberId: string) {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({ id, ...body }: CheckUpInput & { id?: string }) =>
      id
        ? unwrap(api.PATCH("/api/checkups/{checkup_id}", { params: { path: { checkup_id: id } }, body }))
        : unwrap(
            api.POST("/api/members/{member_id}/checkups", {
              params: { path: { member_id: memberId } },
              body,
            }),
          ),
    onSuccess: (_, vars) => {
      invalidate(memberId);
      toast.success(vars.id ? "Check-up updated" : "Check-up saved");
    },
    onError,
  });
}

export function useDeleteCheckup(memberId: string) {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE("/api/checkups/{checkup_id}", { params: { path: { checkup_id: id } } })),
    onSuccess: () => {
      invalidate(memberId);
      toast.success("Check-up deleted");
    },
    onError,
  });
}

export function useUploadPhoto(memberId: string) {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({ checkupId, file }: { checkupId: string; file: File }) =>
      unwrap(
        api.POST("/api/checkups/{checkup_id}/photos", {
          params: { path: { checkup_id: checkupId } },
          body: { file: file as unknown as string },
          bodySerializer: (body) => {
            const form = new FormData();
            form.append("file", (body as unknown as { file: File }).file);
            return form;
          },
        }),
      ),
    onSuccess: () => {
      invalidate(memberId);
      toast.success("Photo added");
    },
    onError,
  });
}

export function useDeletePhoto(memberId: string) {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (photoId: string) =>
      unwrap(
        api.DELETE("/api/checkup-photos/{photo_id}", { params: { path: { photo_id: photoId } } }),
      ),
    onSuccess: () => invalidate(memberId),
    onError,
  });
}
