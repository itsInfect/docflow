import { useQuery } from "@tanstack/react-query";

import { listAuditEvents } from "../lib/api";

export function useAuditEvents() {
  return useQuery({
    queryKey: ["audit-events"],
    queryFn: listAuditEvents,
  });
}
