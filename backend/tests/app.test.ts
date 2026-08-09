import request from "supertest";
import { createApp } from "../src/app";

const app = createApp();

describe("GET /health", () => {
  it("returns 200 and ok status", async () => {
    const res = await request(app).get("/health");
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("ok");
  });
});

describe("Unknown route", () => {
  it("returns 404", async () => {
    const res = await request(app).get("/api/does-not-exist");
    expect(res.status).toBe(404);
  });
});
