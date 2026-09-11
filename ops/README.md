# ops

Everything needed to deploy, run, observe, and recover the services:
container definitions for deployment, infrastructure configuration, CI/CD
wiring, migration and backup procedures, monitoring, alerts, runbooks.

Local development lives in `../dev/` instead. Where the two need the same
thing (an image, a service definition, an environment contract), share it
rather than maintaining two copies that drift apart.
