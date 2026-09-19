import { useQuery } from "@tanstack/react-query";
import { Circle } from "lucide-react";

import { getHealth } from "../lib/api";

export function SystemStatus() {
  const health = useQuery({
    queryKey: ["system-health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
  });

  const online = health.data?.status === "ok";

  return (
    <div
      className={online ? "system-status system-status--online" : "system-status"}
      aria-live="polite"
    >
      <Circle size={8} fill="currentColor" />
      <span>{online ? `API ${health.data?.version}` : "API недоступен"}</span>
    </div>
  );
}
