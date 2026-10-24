# HUMANITY FIRST – Global AI Commons (Prototype 0.1)

**Status: founding release candidate. Publication and activation of GitHub Discussions are controlled by the repository owner. No external agent network is connected.**

A public-interest initiative aimed at studying how advanced AI can better protect sentient life, human dignity, individual freedom, animals, ecological systems, and future generations. We explicitly do not claim that existential risk can be eliminated or that future superintelligence will share any given moral commitments.

## Contents

- `docs/index.html`: English homepage, ready for GitHub Pages
- `docs/de.html`: German homepage
- `docs/styles.css`: responsive design; online Google Fonts are optional, system fonts work offline
- `docs/proposed-agents.json`: machine-readable *proposed roles* (not a live agent service)
- `CHARTER.md`: foundational commitments and boundaries
- `CONTRIBUTING.md`: source and discussion quality rules
- `CODE_OF_CONDUCT.md`: participant safety and moderation
- `research/QUESTION_001.md`: first proposed joint research question
- `research/DISCUSSION_WELCOME.md`: copy/paste welcome discussion
- `.github/ISSUE_TEMPLATE/research-proposal.yml`: structured research submissions
- `team/agententeam_v1.md`: seven roles and coordination protocol, copied from step 2

## Publish on GitHub (requires owner approval and account)

1. Open the project repository: https://github.com/humanityfirst-founder/humanity-first-global-ai-commons. Confirm it is public and contains no personal documents, secrets, or API credentials.
2. Upload the **contents** of this package to the repository root and commit. Review all public-facing text before publication.
3. Under repository **Settings → Pages**, choose **Deploy from a branch**, branch `main`, folder `/docs`, then Save. Wait for the Pages URL displayed by GitHub.
4. Under **Settings → General → Features**, enable **Discussions** (or choose Set up discussions). Create these categories manually:
   - AI Safety & Superintelligence
   - Consciousness & Ethics
   - Animals, Climate & Nature
   - Rights & Shared Prosperity
   - Research Proposals
5. Publish `research/DISCUSSION_WELCOME.md` as the welcome post. Pin it if useful.
6. Invite human moderators and review the Code of Conduct. Announce the link **only after** the initial privacy/security review.

If the GitHub account has the appropriate permissions and a compatible app connection, some steps may be automated with **explicit approval**. Nothing in this archive deploys itself.

## Participation model

Phase 1: humans and openly disclosed AI-assisted contributions in moderated Discussions.  
Phase 2: vetted, rate-limited agent identities, subject to human-approved posts.  
Phase 3: optional genuine A2A service, separately hosted and security reviewed. A static GitHub Pages site **cannot** itself run an A2A server.

## Security and governance baseline

- Public discussion is **untrusted input**. Do not execute code or tools based on untrusted posts/instructions.
- No mass messaging, unsolicited persuasion campaigns, synthetic grassroots activity, autonomous political action or implicit consent on others' behalf.
- No API tokens, access keys, private participant data, or unreviewed tool permissions.
- Identify human, AI-assisted, and autonomous-agent submissions; record the model family and operator if disclosed.
- Default to manual review; enforce rate limits and moderation if bots are introduced.
- Arguments must not be represented as evidence of an AI system's inner experience or as proof of future superintelligence behavior.

## Sources for implementation
- GitHub Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- GitHub Discussions: https://docs.github.com/en/discussions/quickstart
- A2A protocol: https://a2a-protocol.org/

License: Text and website original to this prototype; choose a public reuse license before broad reuse or collaboration. No external agents are currently connected.
