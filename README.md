# Hi, I'm Mateusz <img src="./assets/cat.gif" alt="exploding cat" height="36" />

<p align="center">
  <img src="./banner.gif" alt="Mateusz Korniak, whoami banner" width="100%" />
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=20&pause=1200&color=A78BFA&center=true&vCenter=true&width=700&lines=Full-stack+%2B+mobile+developer;Self-hosting+everything+I+can;Clean+code%2C+clear+problems%2C+a+bit+of+chaos" alt="Typing intro" />
</p>

<p align="center">
  <a href="https://github.com/ZiQu-dev">
    <img src="https://img.shields.io/badge/GitHub-09090b?style=for-the-badge&logo=github&logoColor=white" alt="GitHub badge" />
  </a>
  <img src="https://komarev.com/ghpvc/?username=ZiQu-dev&style=for-the-badge&color=a78bfa" alt="Profile views" />
</p>

## Portfolio

My portfolio lives at [mateuszkorniak.pl](https://mateuszkorniak.pl).

## About me

- 📍 Skawina / Kraków, studying Applied Computer Science at UKEN (Uniwersytet Komisji Edukacji Narodowej w Krakowie)
- 💼 Full-Stack Engineer focused on Go backend and Flutter apps, currently at Holiday Polen (remote)
- 🗣️ Polish (native), English (B2/C1)
- 🔭 Working on: a few self-hosted projects, a Flutter client for the USOS API, and the BitFlip student club site
- 🧪 Into: homelab, Docker, Polish-language docs, and easter eggs hidden in UIs

## Projects

- **[Portfolio-Website](https://github.com/ZiQu-dev/Portfolio-Website)**: this portfolio, Astro + React islands + Tailwind 4, with a small private debt-splitting app behind `/dlugi`.
- **UkenMate**: unofficial Flutter client for the USOS API at UKEN. Read-only by design, Polish UI, a cat walks along the nav bar on purpose. *(Private Forgejo repo.)*
- **[BitFlip club site](https://bitflip.mateuszkorniak.pl/)**: website for a student science club at UKEN. Astro 5 with React, Postgres for event sign-ups, voting and a member panel, deployed with Docker behind Caddy.
- **[MBM Electronics](https://www.mbm.krakow.pl/)**: new company site for a Kraków AV and IT firm (in business since 1993), built from scratch in Astro to replace WordPress. Includes SEO, 301 redirects and a contact form with its own mailer.
- **Prawko Plus**: driving-theory learning platform. Go API with video streaming and FFmpeg transcoding, a Flutter app, and Docker Compose behind Caddy. [Demo](https://pp.mateuszkorniak.pl/)
- **Holiday Polen**: booking system for hotels and holiday cottages, a private alternative to booking.com on the client's own domain. Go REST API with PostgreSQL. [Client site](https://holidaypolen.de/)
- **EMPE**: Qt desktop app that visualises and records live data from two lidar devices over COM ports.

## Experience

- **MBM Electronics**, Web Developer and IT administration, Kraków (09.2026 – now)
- **Holiday Polen**, Full-Stack Engineer, remote (12.2025 – now)
- **Aegis Consulting**, Mobile / Full-Stack, hybrid (06.2025 – 03.2026): Prawko Plus
- **Komputrex**, IT administrator / service desk (06.2024 – 10.2024, 03.2026)
- **ManufaqturaHR**, Front-End Developer, WordPress (04.2024 – 10.2024)

## Tech stack

<p>
  <img src="https://skillicons.dev/icons?i=ts,js,react,astro,tailwind,flutter,dart,python,php,go,postgres,docker,linux,bun,git,vscode&perline=8" alt="Tech stack icons" />
</p>

<!-- Icons taken from the repos I actually work in. Check which ids exist at https://skillicons.dev -->


## Stats

<p align="center">
  <img src="https://stats.mateuszkorniak.pl/stats-card.svg" alt="Activity and languages" width="100%" />
</p>

## Contributions: GitHub + Forgejo

<p align="center">
  <img src="https://stats.mateuszkorniak.pl/contributions-3d.svg" alt="3D contribution calendar, GitHub and Forgejo combined" width="100%" />
</p>

<p align="center">
  <img src="https://stats.mateuszkorniak.pl/contributions-2d.svg" alt="2D contribution calendar, GitHub and Forgejo combined" width="100%" />
</p>

Both calendars count GitHub contributions plus commits from my self-hosted Forgejo, including org repos. Teal = a day where Forgejo led. Repos migrated or mirrored from GitHub are left out, so the import history doesn't inflate the numbers.

## How this profile is built

This repo lives on GitHub, but the build runs on my own Forgejo:

- **Forgejo** is the source of truth. It runs `.forgejo/workflows/forgejo-stats.yml` on my local runner every 6 hours. The job calls the Forgejo API and GitHub, renders the calendars and the stats card with [`scripts/forgejo_stats.py`](scripts/forgejo_stats.py) (stdlib Python, no dependencies), and commits the SVGs.
- **Images** are served from my own server (three SVG files behind Caddy), so the numbers stay fresh without pushing to GitHub.
- **Banner** is an animated GIF, generated once locally by [`scripts/make_banner.py`](scripts/make_banner.py) and committed. It doesn't change on each run.

---

## Contact

<p align="center">
  <a href="https://www.linkedin.com/in/mateusz-korniak-0387572a2/"><img src="https://img.shields.io/badge/LinkedIn-09090b?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
  <a href="https://signal.me/#eu/IH9hcc39At923TmqyWF5y16GU5_tOLbLShx58WVY9CZjA27yEdlDOY03ePadOR39"><img src="https://img.shields.io/badge/Signal-09090b?style=for-the-badge&logo=signal&logoColor=white" alt="Signal" /></a>
  <img src="https://img.shields.io/badge/Discord-ZiQu-09090b?style=for-the-badge&logo=discord&logoColor=white" alt="Discord: ZiQu" />
</p>
