import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import type { Match } from "../types";
import { MatchCard } from "./MatchCard";

const match: Match = {
  id: 1,
  provider_id: 10,
  stage: "GROUP_STAGE",
  group: "Grupo A",
  matchday: 1,
  kickoff_at: "2026-06-20T19:00:00Z",
  lock_at: "2026-06-20T18:45:00Z",
  is_locked: false,
  has_started: false,
  status: "TIMED",
  home_team: { id: 1, name: "Brasil", short_name: "Brasil", code: "BRA", crest_url: "" },
  away_team: { id: 2, name: "Japão", short_name: "Japão", code: "JPN", crest_url: "" },
  scoring_home: null,
  scoring_away: null,
  penalties_home: null,
  penalties_away: null,
  my_prediction: null,
  predictions: []
};

describe("MatchCard", () => {
  it("mostra que um jogo aberto aceita palpite", () => {
    render(<MemoryRouter><MatchCard match={match} /></MemoryRouter>);
    expect(screen.getByText("Toque para enviar seu palpite.")).toBeInTheDocument();
    expect(screen.getByText("Brasil")).toBeInTheDocument();
  });

  it("mostra quando a partida esta em andamento", () => {
    render(<MemoryRouter><MatchCard match={{ ...match, status: "IN_PLAY", is_locked: true }} /></MemoryRouter>);
    expect(screen.getByText("Em andamento")).toBeInTheDocument();
  });

  it("mostra quando a partida terminou e o usuario acertou na lata", () => {
    render(
      <MemoryRouter>
        <MatchCard
          match={{
            ...match,
            status: "FINISHED",
            is_locked: true,
            scoring_home: 2,
            scoring_away: 1,
            my_prediction: {
              id: 1,
              user: 1,
              user_name: "Fabio",
              home_score: 2,
              away_score: 1,
              points: 5,
              submitted_at: "2026-06-20T18:00:00Z",
              updated_at: "2026-06-20T18:00:00Z"
            }
          }}
        />
      </MemoryRouter>
    );
    expect(screen.getByText("Encerrado")).toBeInTheDocument();
    expect(screen.getByText("✓ LT")).toBeInTheDocument();
  });
});
