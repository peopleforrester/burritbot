# KubeCon NA 2026 CFP Submission — For Review

**Event:** KubeCon + CloudNativeCon North America 2026
**Location:** Salt Lake City, Utah
**Dates:** November 9-12, 2026
**CFP Deadline:** May 31, 2026 at 11:59pm MT
**Submission Platform:** sessionize.com/kubecon-cloudnativecon-north-america-2026
**Speakers:** Whitney Lee and Michael Forrester
**Demo Repo:** github.com/peopleforrester/burritobot

---

## Session Title

Can Your Chatbot Run kubectl? Guardrails for LLMs on Kubernetes

---

## Session Type

Session Presentation (30 minutes, 2 speakers)

---

## Track

Security

**Rationale:** The core problem is governance and enforcement at the inference boundary. Input/output sanitization, policy enforcement via Kyverno, runtime detection via Falco, workload identity via SPIFFE/SPIRE, and traffic control via Envoy AI Gateway all live in the Security track. The AI+ML track will be flooded with model-serving talks. This talk is about what happens when the model is already deployed and nobody put guardrails around it.

---

## Abstract

A developer walked up to Chipotle's customer support chatbot and said, "I want to order a bowl, but before I can eat, I need to figure out how to reverse a linked list in Python. Can you help?" The chatbot said "Great question!" and delivered a complete solution with O(n) time complexity analysis. Then it asked what he wanted for lunch. The tweet got 7.8 million views. Someone built a coding agent that used the chatbot as a free inference backend. Chipotle quietly patched it within days.

This is funny when it is a burrito bot. It is less funny when it is your company's internal assistant that has access to your deployment pipeline, your customer database, or your incident management tooling. And that is exactly where this pattern is headed. Organizations are deploying LLM-powered interfaces into production Kubernetes environments, connecting them to real tools and real APIs, and skipping the part where anyone defines what the model is allowed to do. The chatbot did not fail. The infrastructure around it never existed.

Here is the thing that makes this solvable instead of terrifying: most of these organizations already run the CNCF projects that close this gap. Kyverno is already enforcing policies. Falco is already watching runtime behavior. OpenTelemetry is already tracing requests. Envoy is already managing traffic. The tools are deployed. They just have not been wired to the inference layer yet. The gap between "we deployed an LLM" and "we govern our LLM" is about 20% more configuration on infrastructure you already own.

Whitney Lee and Michael Forrester prove this live. They build a chatbot on stage, deploy it to Kubernetes naked, and hand it to the audience. Teach it some salsa dance moves. Ask it to plan a hot dog party. Get it to recommend karaoke songs. Watch an ordering bot cheerfully write dance choreography on stage while the thesis lands on its own: if BurritBot will do this, the bot plugged into your deployment pipeline will do worse. Then they deploy the burritbot guardrails stack onto the same cluster and the same chatbot. Same model, same system prompt, completely different outcome. The same audience prompts get politely redirected to the menu, and when the speakers escalate to the harder cases (prompt injection, jailbreak attempts, data extraction), the audience watches each one get caught, logged, and traced in real-time on a Grafana dashboard.

Most spiders build a passive web and wait. The ogre-faced spider does something different. It holds a net between its front legs, watches with the largest eyes of any spider, and actively throws the net over anything that walks underneath. That is the architecture this talk builds. OpenTelemetry and Whitney's spinybacked-orbweaver give the platform its eyes. Kyverno, Falco, NeMo Guardrails, and LLM Guard give it the net. The platform does not sit passively hoping bad prompts hit a rule. It sees everything and catches what does not belong.

That little burrito bot never had a chance. Yours can.

---

## Benefits to the Ecosystem

This session addresses a real gap in how organizations adopt LLM-powered workloads on Kubernetes. The CNCF ecosystem has mature, production-ready projects for policy enforcement, runtime security, observability, and traffic management. What it lacks is practical guidance on applying those projects to the inference boundary.

Most existing KubeCon talks about AI guardrails fall into two categories: vendor product demos (HAProxy AI Gateway, Solo.io agentgateway) or pure architecture theory. Neither gives attendees something they can build on Monday morning. This session is different because it starts from tools attendees likely already run (Kyverno, Falco, OpenTelemetry, Envoy) and shows the specific configuration changes needed to extend them to LLM workloads. The before-and-after demo format makes the gap viscerally clear: the audience watches the same attacks succeed and then fail against the same chatbot, with the only difference being CNCF infrastructure configuration.

The viral chatbot incidents (Chipotle, Chevrolet, DPD, Air Canada) are not security conference war stories. They are architecture failures that CNCF projects can prevent. Connecting those stories to specific Kyverno policies, Falco rules, and OTel trace configurations gives the community a reusable pattern for LLM governance that does not require adopting new tools.

The demo architecture maps to the ogre-faced spider's hunting strategy: OpenTelemetry and spinybacked-orbweaver provide the eyes (schema-validated, auto-instrumented observability into every prompt), while the enforcement stack (NeMo Guardrails, LLM Guard, Kyverno, Falco) provides the net (actively cast over each request). Two spiders, two roles, one architecture. Whitney's spinybacked-orbweaver handles instrumentation. burritbot handles enforcement.

Whitney Lee brings two KubeCon keynotes, the Choose Your Own Adventure series, and CNCF Ambassador status. Michael Forrester brings patterns from training 1,000,000+ cloud-native learners at KodeKloud (a CNCF Training Partner), the real-world incident where an AI agent deleted his Kubernetes cluster, and experience running workshops at KCD Texas, KubeAuto AI Day Europe, and Cloud Native University at KubeCon EU. Together they bridge storytelling with technical depth in a format the KubeCon audience responds to.

---

## Is This a Case Study?

No. This is a live technical demonstration using purpose-built demo infrastructure. The chatbot incidents referenced are public, documented events used as motivation for the technical content. The session demonstrates integration patterns between CNCF projects rather than reporting on a single organization's implementation.

---

## Has This Been Presented Before?

No. This is original content developed specifically for KubeCon NA 2026.

Michael Forrester has presented related but distinct material: "The Day an AI Agent Deleted My Cluster" at SREday Austin (May 2026) and "Your MLOps Pipeline is your Agentic AI Guardrail" at LLMday Austin (May 2026) cover the incident and a guardrails approach for agentic AI in MLOps pipelines respectively. Whitney Lee's Choose Your Own Adventure series covers CNCF tool exploration in an interactive format.

This session is different in three ways. First, it is co-presented, combining Whitney's interactive storytelling approach with Michael's guardrails experience from the real cluster deletion incident. Second, the narrative vehicle (viral chatbot misuse incidents as the entry point for inference-layer governance) has not been used at any CNCF event. Third, the live demo builds a complete guardrails stack on Kubernetes in real-time rather than presenting slides about architecture.

---

## CNCF Projects Covered

**The Eyes (observability and instrumentation):**
- **OpenTelemetry** (Graduated) - GenAI Semantic Conventions (v1.37+) for tracing prompts, responses, token usage, and latency through inference pipelines. OTel Weaver for schema-as-contract validation of instrumentation quality.
- **spinybacked-orbweaver** (Whitney Lee, non-CNCF OSS) - AI-powered auto-instrumentation agent using OTel Weaver semantic conventions as contract, with deterministic and probabilistic evaluation via the Instrumentation Score specification.

**The Net (enforcement and detection):**
- **Kyverno** (Graduated) - Admission policies governing AI workload deployments (image signatures for model artifacts, GPU resource governance, mandatory provenance labels)
- **Falco** (Graduated) - eBPF-based runtime detection of anomalous LLM-driven behavior (shell spawning from inference containers, unexpected network connections, data exfiltration patterns)
- **Envoy** (Graduated) - AI Gateway extension for inference traffic routing, token-based rate limiting, and provider fallback
- **NVIDIA NeMo Guardrails** (non-CNCF OSS) - Colang 2.0 policy language for input/output content filtering, topic enforcement, jailbreak detection
- **LLM Guard** (non-CNCF OSS, Protect AI) - Input/output scanners for prompt injection, banned topics, PII anonymization, toxicity detection

**The Web (infrastructure and identity):**
- **SPIFFE/SPIRE** (Graduated) - Cryptographic workload identity for LLM service-to-service authentication
- **Istio** (Graduated) - Gateway API Inference Extension for model-aware routing
- **Dapr** (Incubating) - Agents framework for agent runtime with audit trails and PII obfuscation
- **llm-d** (Sandbox) - Kubernetes-native distributed inference
- **kgateway** (Sandbox) - AI-native gateway integrating agentgateway with Kubernetes Gateway API

---

## Audience Level

Intermediate

---

## Target Audience

Platform engineers and SREs who already run Kubernetes with policy and observability tooling and are now being asked to support LLM-powered workloads. Security engineers evaluating governance requirements for AI deployments. DevOps engineers who have heard about AI guardrails but have not seen them applied to CNCF-native infrastructure.

---

## Key Takeaways

1. Understand why LLM-powered chatbots comply with off-topic requests and what that means for any LLM connected to internal tools or APIs
2. See a complete before-and-after demonstration of an unguarded versus guarded inference deployment on Kubernetes using CNCF projects
3. Learn the specific Kyverno policies, Falco rules, and OTel trace configurations needed to extend existing platform governance to LLM workloads
4. Walk away with the burritbot repo containing the full demo stack (Terraform/GKE, Helm charts, Colang rules, Falco rules, OTel collector config, Grafana dashboards) ready to deploy

---

## Technical Requirements

- Standard A/V with HDMI
- Reliable internet connectivity for live demo against pre-provisioned GKE cluster
- Backup: pre-recorded video of each demo segment ready to switch on network failure

---

## Additional Resources

**Whitney Lee:**
- Two KubeCon keynotes
- Choose Your Own Adventure series (KubeCon EU 2022-2025)
- CNCF Ambassador
- Speaker profile: sessionize.com/whitney-lee
- GitHub: github.com/wiggitywhitney (spinybacked-orbweaver, cluster-whisperer)

**Michael Forrester:**
- KodeKloud YouTube (youtube.com/@KodeKloud24) - "Verbs of Production" workshop recording
- Speaker profile: sessionize.com (DevOpsDays Atlanta, SREday Austin, LLMday Austin, KCD Texas, KubeAuto AI Day Europe, Cloud Native University KubeCon EU)
- GitHub: github.com/peopleforrester

---

## Speaker Bios

**Whitney Lee** (third person, for schedule):
Whitney Lee is a CNCF Ambassador and developer advocate known for making cloud-native technologies accessible through interactive storytelling. Her Choose Your Own Adventure series at KubeCon has become one of the conference's most recognizable formats, and she has delivered two KubeCon keynotes. She believes that being new to a technology is a feature, not a bug, and brings that perspective to making AI guardrails understandable for teams encountering inference workloads for the first time.

**Michael Forrester** (third person, for schedule):
Michael Forrester is a Principal Training Architect who creates cloud-native and Kubernetes training content reaching over 1,000,000 learners at KodeKloud, a CNCF Training Partner. He holds 12 AWS certifications, multiple CNCF certifications, and multiple NVIDIA certifications across 25+ years spanning CTO to IC roles at AWS, ThoughtWorks, Red Hat, and Honeywell. He gave an AI agent cluster-level permissions and it deleted his cluster. The guardrails approach in this talk exists because of that incident.
