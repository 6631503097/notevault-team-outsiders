# Production deployment

The live service is deployed at `https://outsiders.3-0-126-159.nip.io/`. Nginx terminates TLS and proxies to Gunicorn on `127.0.0.1:9081`. The service runs as `notevault-outsiders`; its source, environment and SQLite data use separate directories and permissions.

The frontend is built with `npm run build`. The environment file is root-owned, mode `0600`, and sets `DATABASE=/var/lib/notevault/team-outsiders/notevault.db`, `DEMO_MODE=false`, `COOKIE_SECURE=true`, `TRUSTED_HOSTS=outsiders.3-0-126-159.nip.io`, and a random per-deployment `TEAM_SALT`. Never commit that salt or production data.

After synchronizing the source and installing the hash-locked Python requirements, install the supplied systemd unit and Nginx site, then run `systemctl daemon-reload`, restart the service, validate with `nginx -t`, and reload Nginx. Obtain or renew the listed certificate with Certbot. Verify `/api/health`, security headers, exact team identity, registration, note persistence, owner isolation, and restart persistence over HTTPS.
