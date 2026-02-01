import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
	index("routes/home.tsx"),
	route("/homes/:id", "routes/homes/page.tsx"),
	route("/signup", "routes/auth/signup.tsx"),
	route("/signin", "routes/auth/signin.tsx"),
	route("/ai-results/:query", "routes/ai-results.tsx"),
	route("/preferences", "routes/preferences.tsx")
] satisfies RouteConfig;
