# Adversarial review: how this project gets hurt

**Status: hostile by construction.** This document argues against
`initial-thinking.md` on purpose. It is written from the point of view of
people who want this project to fail, be silenced, or be expensive — a
plaintiff's lawyer looking for a cause of action, a political operator
looking for a weapon, and a regulator looking for a file to open.

**Not legal advice.** Statutes are cited from general knowledge of Colombian
law and every one of them must be confirmed by a Colombian abogado before it
is relied on. Getting this wrong in the optimistic direction is the expensive
failure mode.

Read it as a threat model, not a verdict. Most of what follows is
survivable; the point is to decide which risks are accepted deliberately
rather than discovered in a lawsuit.

---

## 0. The summary, if nothing else is read

The three things most likely to actually hurt this project, in order:

1. **Publishing the 2016 text as if it were current law.** The agreement was
   modified by constitutional amendment, statutory law and Constitutional
   Court rulings. A tool that answers "what the agreement says" will be read
   by every user as answering "what the law is". That gap is the most
   defensible-sounding and most dangerous thing in the design.
2. **Storing questions about politics, tied to IP addresses.** Under
   Colombian habeas data law, political orientation is sensitive personal
   data. The conversation log is a database of political opinions of
   identifiable Colombians, held by a private individual, processed abroad.
3. **Becoming a misinformation source with better production values.** One
   screenshot of a correctly-quoted clause without its exception, circulating
   with the project's name on it, destroys the only asset the project has.

Everything below elaborates. The mitigation list is §9.

---

## 1. The attack on the central claim

The project's defense, everywhere in `README.md` and `AGENTS.md`, is *"we do
not interpret; we quote."* A competent opposing lawyer dismantles that in
about ten minutes, and the dismantling is not sophistry — it is correct.

### 1.1 Retrieval is editorial

Someone asks whether the agreement grants impunity. The system retrieves six
units out of ~1,500 and shows them. Six were chosen; 1,494 were not. The
ranking function made an editorial judgment, and "a cosine similarity decided"
is not a defense — it is an admission that the editorial judgment is
unexamined.

**The line an adversary uses:** *"The defendant selected which portions of a
310-page document the public would see, in response to politically charged
questions, using criteria he wrote himself and never published."*

The honest answer is that GroundSource is a publisher with an unusual
editorial process, not a neutral pipe. Every design decision should be made
on that assumption.

### 1.2 Chunking is interpretation

Splitting at 500–800 tokens means clause boundaries get cut. A legal
provision whose exception lives in the following paragraph, retrieved without
that paragraph, is a *materially misleading true statement*. That is the
classic shape of a defamation or misrepresentation claim: nothing false, and
the impression is wrong.

The agreement is especially bad for this. It is dense with internal
cross-references — a clause that says *"conforme a lo establecido en el punto
3.2"* is not self-contained, and returning it alone is not quoting, it is
excerpting. Excerpting is editorial.

**Design consequence:** retrieving a fragment is not enough. The unit must
come with its parent, its exceptions, and its referenced units, or the
grounding claim is false in exactly the cases that matter most.

### 1.3 The connective prose is where liability lives

Quotations are sliced from the source and are safe. The sentences *between*
the quotations are model-generated, and those are the ones that say things
like "the agreement establishes that…". That text is authored by the system.
No amount of verbatim quoting insulates it.

### 1.4 The citation validator does not do what it seems to do

The plan's highest-value guardrail checks that every section reference the
model emits appears in the retrieved set. That catches invented section
numbers. It does **not** check that the cited section supports the claim
attached to it.

So the failure mode it leaves open is: a real citation, correctly formatted,
deep-linked, attached to an assertion the clause does not support. That
output is *more* credible than a hallucinated one, and the validator will
pass it. A guardrail that raises the credibility of its own failures is worse
than no guardrail unless the residual risk is understood.

### 1.5 Abstention will be read as a position

"The document does not address this" is a claim about a 310-page text. When
the question is *"does the agreement guarantee the victims' right to truth?"*
and the tool declines, the screenshot says: **the peace agreement bot says
the agreement does not guarantee victims' rights.** Abstention is not neutral
ground; it is an answer with a different grammar.

---

## 2. The legal-currency problem

This deserves its own section because it is the strongest claim an adversary
has, and because the current design walks straight into it.

The agreement signed on 24 Nov 2016 is not the operative legal reality. It
was followed by constitutional amendments, implementing statutes, and
Constitutional Court decisions that conditioned, struck, or reinterpreted
parts of it. *(Verify the specific instruments with counsel — the point
stands regardless of which ones.)*

A user asks what sanctions the JEP can impose. The tool quotes the 2016 text,
accurately, with a page link. The user takes it as current law. It may not
be.

**The plaintiff's framing:** *"A public-facing service presented superseded
provisions as the content of a legal instrument, without disclosing that the
provisions had been modified, and was consulted by X thousand people."*

Three aggravating factors:

- The project's entire pitch is accuracy and verification. A tool marketed as
  the antidote to misinformation is held to the standard it advertises.
- The `#page=N` citation makes the output look authoritative — more
  authoritative than a news article making the same error.
- The "we only say what the text says" distinction is a lawyer's distinction.
  It will not survive contact with a normal user, and a court asks how a
  reasonable user understood the output, not how the developer intended it.

**This is not solvable by a footer disclaimer.** It is solvable by making
legal status part of the answer: which units were modified, by what, and a
standing banner that the text is as-signed, not as-in-force. That is a
content problem requiring legal research per unit — expensive, and the
project does not currently budget for it.

The cheaper alternative is to pick a first document that has no such problem
and delay the agreement until this is funded. The document ladder already
points that way for engineering reasons; this is a second, stronger reason.

---

## 3. Colombian legal exposure

*All statute references to be confirmed by counsel.*

### 3.1 Habeas data — the most concrete exposure

Ley 1581 de 2012 and Decreto 1377 de 2013 govern personal data. Two facts
combine badly:

- **Political orientation is sensitive data** (Ley 1581, art. 5). Processing
  it is prohibited except under narrow exceptions, generally requiring
  explicit, informed, documented consent.
- **A conversation log is a record of political opinions.** "¿El acuerdo da
  impunidad a los guerrilleros?" typed from an identifiable IP, stored with a
  timestamp, is a data point about that person's politics.

Consequences to work through with counsel:

- Whether the planned storage constitutes processing of sensitive data, and
  what consent flow that requires. A checkbox will probably not be enough.
- **International transfer** (art. 26): prompts go to a model provider
  abroad. Whether the destination is on the SIC's adequacy list, and what
  contractual instrument is required otherwise.
- **RNBD registration** with the SIC, and whether the operator's legal form
  and size trigger it.
- Rights of access, rectification and deletion for stored conversations —
  which requires identifying whose conversation is whose, which requires more
  identification than the product otherwise needs. Data minimization fights
  compliance here, and that tension needs a decision, not a default.
- Sanctions under art. 23 reach thousands of monthly minimum wages. For an
  individual, that is ruinous.

**The trap:** the plan's rate limiting "per IP" and its `Conversation` model
are the two features that create this exposure, and both were adopted for
unrelated reasons.

### 3.2 Injuria and calumnia — criminal, not just civil

Defamation is criminal in Colombia (Código Penal arts. 220–221), and private
prosecution is a routine political tactic. The bot does not need to name
anyone: an answer about a party to the agreement, or about a group, can
generate a claim from an individual who considers himself identified.

Realistically, the risk is not conviction. The risk is being a private
individual with no legal budget defending a criminal complaint filed by
someone with both. **The process is the punishment**, and an adversary who
understands that does not need to win.

### 3.3 Tutela and the right to rectification

Constitution art. 20 grants a right to rectification "en condiciones de
equidad"; the tutela (art. 86) resolves in **ten days**. Anyone who believes
the tool misrepresented them can file, cheaply, without a lawyer.

Operational consequences, which are design requirements and not paperwork:

- A published, monitored contact channel for rectification requests.
- The ability to correct or suppress a specific answer **fast** — which means
  the semantic cache needs an audit trail and a kill switch per entry.
- Records showing what the system output on a given date, or there is no way
  to demonstrate what was actually said. This directly contradicts a minimal
  retention policy, and the contradiction must be resolved deliberately.

### 3.4 Copyright and redistribution

Official texts are generally reproducible (Ley 23 de 1982 — confirm scope),
but "generally" is doing real work:

- A government-published **PDF** carries typography, layout, and sometimes
  imagery that may be protected independently of the text.
- The *Universal Declaration of Human Rights* is a United Nations
  publication with its own reproduction terms — "public domain" is an
  assumption, not a fact, and it sits in the fixture rung where it would be
  committed to a public repository.
- Any third-party edition, annotated compilation, or scraped HTML rendition
  may carry rights the original text does not.

The mirroring plan in the custody section converts a linking question into a
redistribution question. Linking is nearly always safe; hosting is not.

### 3.5 Looking official

Using government emblems, the agreement's visual identity, an official-sounding
name, or a domain that suggests state affiliation invites a cease-and-desist
at best. The bot answering in an institutional register makes it worse: users
will believe it is official unless the interface works actively against that
belief.

### 3.6 Electoral periods

If the tool is live during a campaign or a consultation, expect scrutiny over
whether its outputs constitute political propaganda, and complaints to the
CNE regardless of the merits. A complaint does not need to succeed to consume
months.

---

## 4. The political attack playbook

Assume a competent operator with a motive. Here is what they do, roughly in
order of cost.

### 4.1 Screenshot farming

The cheapest and most effective attack. Ask questions engineered to produce a
true, correctly-cited, devastatingly decontextualized quote. Screenshot it.
Circulate it with the project's name attached.

The project's own credibility markers — the citation, the page number, the
official-looking link — make the screenshot *more* persuasive than an
ordinary lie. **The tool is optimized to make quotes look verified, which is
exactly what a decontextualizer wants.**

This is the single highest-probability harm in this document, it requires no
legal process, and the current design has no defense against it.

### 4.2 The both-flanks squeeze

- **From one flank:** making the agreement legible is itself a pro-agreement
  act. Expect "propaganda dressed as a search engine", and scrutiny of who
  built it and who paid.
- **From the other:** reducing a political settlement to quotable clauses,
  stripped of the process and the victims behind it, is its own kind of
  distortion. Expect "legalese laundering".

Both critiques are partly right, which is what makes them effective. There is
no configuration of this product that is read as neutral by everyone, and
planning as though there is guarantees being blindsided.

### 4.3 Weaponizing the refusal

The refusal to answer "what has been implemented since 2016" is defensible
engineering and terrible politics. To one side it hides the government's
failures; to the other it hides the FARC's. Both will claim the omission is
deliberate.

Worse, the boundary is fuzzy in practice. Many questions look textual and are
really about implementation. Every judgment call at that boundary is
evidence, to someone, of an agenda.

### 4.4 Attacking the corpus of decisions

Every artifact the project publishes for transparency becomes an attack
surface: the golden set (*"who chose these 40 questions?"*), the reviewed
cache answers (*"a human wrote these — which human?"*), the prompts
(*"look at the instruction telling it to avoid the word X"*), the git history
(*"here is the commit where he changed the answer about the JEP"*).

Open source is the right call for credibility and it hands adversaries a
perfectly indexed archive. Both are true; only the second one tends to be a
surprise.

### 4.5 Provider complaints and deplatforming

A coordinated report campaign to the model provider, the static host, or the
domain registrar costs the attacker nothing. Model providers restrict
political use in their acceptable-use policies; a peace-agreement Q&A bot is
in the grey zone of most of them. A suspension needs no court and has no
appeal worth the name.

**Single point of failure:** one provider account. Losing it takes the
service down and looks, publicly, like a guilty verdict.

### 4.6 Going after the person

The maintainer is a private individual in Colombia working on the peace
agreement. That is not an abstract risk category.

Currently exposed: real name and email in every commit, and likely in domain
registration and provider accounts. The repository will be public. Anyone can
reconstruct who built it, where they work, and when they were awake.

**Concrete, do this before going public:** decide whether the project is
operated by a legal entity rather than a person; use a role address rather
than a personal one; enable registrar privacy; consider a GitHub noreply
commit address; and think about whether being the sole public face is
acceptable — including for the people around you.

---

## 5. Where the current plan is weakest

Gaps between the risks above and what `initial-thinking.md` actually
provides.

| Risk | Current plan | Gap |
|---|---|---|
| Decontextualized quoting | Chunk at 500–800 tokens; return top 6 | Nothing forces the parent clause, exceptions, or cross-referenced units to accompany a fragment |
| Superseded provisions | Version guard on the *file* | No modelling of legal status per unit; the guard proves the right PDF, not the right law |
| Unsupported claims on real citations | Validate references against the retrieved set | No check that the cited unit supports the claim |
| Screenshot decontextualization | — | No mitigation at all |
| Sensitive personal data | `Conversation` model, per-IP rate limiting | No consent flow, retention policy, or transfer analysis |
| Rectification within ten days | — | No contact channel, no per-answer audit trail, no cache kill switch |
| Provider suspension | Single provider, fallback tier | Both tiers are the same vendor; no second provider, no read-only fallback |
| Looking official | Neutral register | Register reads as institutional, which increases the confusion it should prevent |
| Maintainer exposure | — | Personal identity attached to a public political artifact |

---

## 6. Three scenarios that end the project

**A. The viral screenshot.** A correctly-cited, context-stripped answer about
amnesty circulates to hundreds of thousands. Corrections reach a fraction of
that. The project becomes a cautionary example of the problem it set out to
solve, and every future citation of it carries that story.

**B. The ten-day tutela.** A public figure files for rectification over an
answer that characterizes their party's commitments. There is no process, no
log of what was output, and no counsel on retainer. Ten days to respond,
during an ordinary work week.

**C. The quiet regulatory file.** A complaint to the SIC about political-opinion
data held by a private individual and shipped to a foreign processor without
a lawful transfer basis. No headlines; months of proceedings and the
possibility of a sanction that dwarfs the hosting budget.

None of these require the software to malfunction. All three assume it works
exactly as designed.

---

## 7. Where the adversary is wrong

The case against is not total, and conceding everything is its own failure.

- **The alternative is worse.** The status quo is the same public arguing
  from the same summaries with no primary source in reach. Perfect neutrality
  is unavailable; better-than-current is achievable.
- **Editorial judgment is unavoidable, and can be disclosed.** Published
  retrieval rules, published prompts, and a published methodology put this
  project ahead of every media summary it competes with.
- **Quoting with anchors is genuinely falsifiable.** Anyone can check. That is
  a real epistemic property, not a marketing claim, and almost nothing else in
  the information environment has it.
- **Most attacks here cost the attacker effort.** Screenshot farming is cheap;
  criminal complaints and regulatory filings are not, and they require someone
  to decide this project is worth their time. Being small is a real defense
  for a long while.

The correct conclusion is not "do not build this". It is "do not launch it in
the shape currently written down".

---

## 8. Questions for a Colombian abogado

Bring these, not a general "is this legal?":

1. Does storing questions like these, with IP addresses, constitute
   processing of sensitive data under Ley 1581 art. 5, and what consent
   mechanism satisfies it for an anonymous public service?
2. Is RNBD registration required for this operator and this database?
3. Is the destination jurisdiction of the model provider on the SIC adequacy
   list, and if not, what instrument authorizes the transfer?
4. What is the minimum viable rectification procedure that survives a tutela,
   and what must be logged to demonstrate what was published on a given date?
5. What legal form (persona natural, SAS, fundación) best limits personal
   liability for a free public service with no revenue, and what does it cost
   to maintain?
6. Does reproducing the official PDF — the file, not the text — raise any
   right distinct from the text itself?
7. What disclaimer language actually limits liability in Colombia for a free
   service, and what does it not limit?
8. What exposure exists for criminal defamation arising from model-generated
   text, and what mitigates it?

---

## 9. Mitigations, ranked by value per unit of effort

### Do before any public deployment

1. **Answer with whole units, never bare fragments.** Return the clause plus
   its parent heading, any exception in the same unit, and the units it
   cross-references. Expensive in tokens, and it removes the single most
   common route to a true-but-misleading answer.
2. **Ship legal-status metadata or do not ship the agreement.** Either mark,
   per unit, "modified by / conditioned by / as signed", or make the first
   public document one without a modification history. The ladder already
   suggests the second; treat it as a legal requirement rather than a
   convenience.
3. **Do not store conversations by default.** Rate limit on a salted hash of
   the IP with a short window; retain no free-text question tied to an
   identifier without an explicit, documented consent flow. If research value
   requires retention, retain aggregates, and decide it deliberately.
4. **A rectification channel that works.** A published address, a documented
   procedure, a per-answer audit record, and a kill switch on any cached
   answer, all reachable within ten days from a bad Monday.
5. **Separate the person from the project.** Legal entity, role email,
   registrar privacy, noreply commit address. Cheap now, impossible later.
6. **Spend cap and rate limits** before the endpoint is reachable — already
   in the plan, repeated here because it is the only item that is both
   financial and adversarial.

### Do before it gets attention

7. **Make every answer carry its own audit trail.** A short verification URL
   in the rendered output, so a screenshot points back to the full context.
   It will not stop decontextualization, but it changes the argument from
   "prove it" to "open the link".
8. **Second model provider, and a degraded read-only mode.** Deplatforming
   should cost credibility, not availability.
9. **Publish the methodology**: retrieval rules, prompts, golden set, and who
   reviewed cached answers. It will be used against the project; being
   forced to disclose it later is worse.
10. **External review of the golden set** by people who disagree with each
    other politically. The set is the project's evidence of good faith, and
    a set authored by one person is evidence of nothing.
11. **Interface that fights the authority it borrows.** Explicit "not an
    official service", "text as signed, not law as in force", and an answer
    layout where the quotation is visually dominant and the generated prose
    is visibly secondary.
12. **A claim-support check** beyond the reference check: verify the cited
    unit actually contains the terms the claim depends on, and degrade to
    "here is the relevant text, read it" when it does not. Weaker than a
    guarantee; much stronger than what is planned.

### Decide deliberately, either way

13. Retention versus defensibility — minimal logs protect users and leave the
    project unable to prove what it said.
14. Open source versus attack surface — the transparency is worth it, the
    indexed archive is real.
15. Whether the agreement is the right first public document at all, or the
    right *second* one, after the pipeline has been proven on a document
    nobody is fighting about.

---

## 10. The uncomfortable question

If the project succeeds, it becomes a trusted source on a contested political
document, operated by one person, with no editorial board, no legal budget,
and no institutional cover. Trust accumulates faster than the capacity to
handle what trust attracts.

Worth answering before launch, not after: **at what level of traffic does
this stop being a side project, and what happens on the day it crosses that
line?** A pre-committed answer — hand it to an institution, add a board,
throttle it, or take it down — is a plan. Deciding in the middle of the first
crisis is not.
