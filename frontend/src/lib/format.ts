const stageNames: Record<string, string> = {
  GROUP_STAGE: "Fase de grupos",
  LAST_32: "16 avos",
  LAST_16: "Oitavas de final",
  QUARTER_FINALS: "Quartas de final",
  SEMI_FINALS: "Semifinais",
  THIRD_PLACE: "Terceiro lugar",
  FINAL: "Final"
};

export const formatStage = (stage: string) =>
  stageNames[stage] ?? stage.replaceAll("_", " ");

export const formatDate = (date: string) =>
  new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    weekday: "short",
    day: "2-digit",
    month: "short"
  }).format(new Date(date));

export const formatTime = (date: string) =>
  new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(date));

