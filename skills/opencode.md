# portbroker integration
# managed by portbroker install-skill

Before starting any service that binds to a network port, request a port reservation from portbroker instead of hardcoding a port:

    PORT="$(portbroker get --name <project-name> 2>/dev/null \
            || portbroker alloc --name <project-name> --persistent)"

Use the returned port for the service. Never hardcode well-known ports (3000, 8000, 8080) -- they will collide with other concurrent sessions on the same machine.

To see all reservations, run `portbroker list` or open the dashboard with `portbroker web`.
