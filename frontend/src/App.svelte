<script lang="ts">
  import Router from "svelte-spa-router";
  import Home from "./pages/Home.svelte";
  import Login from "./pages/Login.svelte";
  import Register from "./pages/Register.svelte";
  import Dashboard from "./pages/Dashboard.svelte";
  import Routes from "./pages/Routes.svelte";
  import Profile from "./pages/Profile.svelte";
  import ProfileEdit from "./pages/ProfileEdit.svelte";
  import Friends from "./pages/Friends.svelte";
  import UserProfile from "./pages/UserProfile.svelte";
  import TelegramCallback from "./pages/TelegramCallback.svelte";

  const routes = {
    "/": Home,
    "/login": Login,
    "/register": Register,
    "/dashboard": Dashboard,
    "/routes": Routes,
    "/profile": Profile,
    "/profile/edit": ProfileEdit,
    "/friends": Friends,
    "/user/:id": UserProfile,
    "/telegram-callback": TelegramCallback,
  };
</script>

<Router {routes} />
