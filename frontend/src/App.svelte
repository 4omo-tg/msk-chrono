<script lang="ts">
  import Router from "svelte-spa-router";
  import Home from "./pages/Home.svelte";
  import Login from "./pages/Login.svelte";
  import Register from "./pages/Register.svelte";
  import Dashboard from "./pages/Dashboard.svelte";
  import Routes from "./pages/Routes.svelte";
  import Profile from "./pages/Profile.svelte";

  const routes = {
    "/": Home,
    "/login": Login,
    "/register": Register,
    "/dashboard": Dashboard,
    "/routes": Routes,
    "/profile": Profile,
  };
</script>

<Router {routes} />
