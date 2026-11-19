import { onRequestPost as collect } from "../functions/api/collect.js";
import { onRequestGet as stats } from "../functions/api/stats.js";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/api/collect" && request.method === "POST") {
      return collect({ request, env, ctx, params: {} });
    }
    if (url.pathname === "/api/stats" && request.method === "GET") {
      return stats({ request, env, ctx, params: {} });
    }
    return env.ASSETS.fetch(request);
  },
};

