import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
	index("routes/home.tsx"),
	route("ai-matcher", "routes/ai-matcher.tsx"),
] satisfies RouteConfig;
