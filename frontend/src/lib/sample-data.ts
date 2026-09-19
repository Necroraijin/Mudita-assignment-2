export const SAMPLE_TRANSCRIPT = `Meeting: Q4 Product Planning
Date: October 15, 2024
Attendees: Sarah (PM), Mike (Engineering Lead), Lisa (Design), Tom (QA), Rachel (VP Product)

Rachel: Let's start with the Q4 priorities. We need to ship the new dashboard redesign by December 15th. This is non-negotiable — we promised it to enterprise clients.

Sarah: Agreed. Mike, can your team handle this alongside the API migration?

Mike: We can, but we'll need to push the mobile app update to Q1. I need at least 3 engineers on the dashboard full-time. Alex and Jordan can lead it, and I'd like to pull in Priya from the platform team.

Lisa: I'll need two weeks for the design handoff. I can have the final mockups ready by November 1st. But I'm concerned about the accessibility audit — we haven't budgeted time for that.

Rachel: Accessibility is required by our enterprise contracts. We must pass WCAG 2.1 AA compliance. Lisa, factor that into your timeline.

Lisa: That pushes my handoff to November 8th then.

Tom: For QA, I'll need at least 3 weeks of testing. That means code freeze by November 22nd. Is that realistic?

Mike: Tight but doable if we start sprint planning next week. One concern — the current API doesn't support the new filtering that the dashboard needs. We'll need to build a new endpoint.

Sarah: What's the effort on that?

Mike: About 2 weeks of backend work. Jordan can handle it parallel to the frontend work.

Rachel: Budget-wise, we have $50,000 for any external tools or contractors. Don't exceed that. Also, all new features need to go through the security review process before deployment.

Sarah: What about the data migration for existing dashboard users?

Mike: Good point. We need a migration plan. I'd estimate 1 week for the migration script and another week of validation. But we haven't decided whether it's a big-bang migration or gradual rollout.

Rachel: Let's do a gradual rollout — 10% of users first, then expand. I want to see metrics before we go full.

Tom: I'll set up monitoring dashboards for the rollout. We should track error rates, load times, and user engagement.

Sarah: One more thing — we need to update the API documentation for the new endpoints. Technical writing team should be involved.

Mike: Agreed. I'll coordinate with them after the API spec is finalized.

Rachel: Okay, let's summarize the key dates and move on. Any blockers?

Lisa: Just the accessibility guidelines. Can someone confirm which version of WCAG we're targeting?

Rachel: WCAG 2.1 AA, as I mentioned. It's in our enterprise contract requirements.

Mike: No other blockers from engineering, but I want to flag that if the API migration hits issues, it could impact the dashboard timeline.

Rachel: Noted. Let's set up a weekly sync to track progress. Meeting adjourned.`;

export const SAMPLE_RULES = `Company Development Rules & Policies

1. DEPLOYMENT POLICY
   - All production deployments require a security review sign-off
   - Code freeze must be at least 2 weeks before release date
   - Gradual rollout is mandatory for user-facing changes (minimum 10% initial rollout)

2. BUDGET POLICY
   - Project spending must not exceed approved budget
   - Any contractor engagement requires VP approval
   - Tool purchases over $5,000 need procurement review

3. COMPLIANCE
   - All user-facing features must meet WCAG 2.1 AA accessibility standards
   - Data migrations require a rollback plan
   - API changes require updated documentation before deployment

4. TEAM POLICY
   - Cross-team resource requests require both team leads' approval
   - Maximum 2 engineers can be pulled from any single team
   - All feature work requires QA sign-off before release

5. TIMELINE POLICY
   - Sprint planning must be completed at least 1 week before sprint start
   - Design handoffs must include accessibility annotations
   - QA testing period must be minimum 2 weeks for major releases

6. SECURITY
   - Security review is mandatory for all new endpoints
   - Sensitive data handling must follow data classification policy
   - External API integrations require security assessment`;
