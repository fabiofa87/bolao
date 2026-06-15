import { expect, test } from "@playwright/test";

test("exibe a entrada privada do bolão", async ({ page }) => {
  await page.goto("/entrar");
  await expect(page.getByRole("heading", { name: "Entrar" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Entrar no bolão" })).toBeVisible();
});

