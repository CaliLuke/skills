---
name: monolith-extraction
description: Extract a cluster of endpoints out of a monolith into a separate service, contract-first, and delete the original code. Use when the user says "extract a service", "carve out", "split the monolith", "strangler fig", "pull these endpoints into their own service", or is running a decomposition proof of concept. Covers picking the cluster, generating from the published contract, owning the data, deleting the original, and proving nothing broke.
---

# Monolith extraction, contract-first

Take a cluster of endpoints out of a monolith, stand them up as a separate service generated from
the API contract, delete the original code, and prove nothing broke.

This skill exists because the same mistakes recur. Every rule below cost something real the first
time. Read the whole file before starting: several of the expensive errors happen in the first
hour, when picking the cluster.

## The one-line version

**Pick by data ownership. Generate from the published contract. Delete the original. Measure
against the incumbent, not against your expectations.**

---

## Stop hedging

A proof of concept exists to answer a question. **Everyone involved already knows it will not
ship.** Saying so, in any form, wastes the reader's time and the operator's patience.

Stop writing these:

- "This would need review before production."
- "In a real deployment you would want to..."
- "Note that this endpoint has a ticket in flight, so this may change."
- "This is not deployed and no traffic points at it."
- "A production version would need to handle..."
- Any sentence whose job is to lower expectations rather than convey a fact.

Nobody asked. The branch is named after a throwaway ticket. There is no reviewer to reassure.

### What to do instead

**Serve the goal of the proof of concept.** Work out what question it answers, then make every
choice serve that question:

| The question | So do this |
|---|---|
| Can this domain be extracted at all? | Push through the hard endpoint rather than picking an easier one |
| Is the method faster than the current approach? | Measure both, on the same work |
| What does the sequence of operations look like? | Record every step and its cost, including wrong turns |
| What blocks us at scale? | Try it at scale, on nine services rather than one |

### Do the hard part

The instinct to shrink when something is not easy is the main way a proof of concept produces
nothing useful. A domain that is genuinely clean does not exist in a real monolith. Chatter between
the new service and the old one is acceptable; more code can move later. The interesting finding is
usually on the far side of the thing that looked too hard.

If a constraint appears to block you, read the code before believing it. See Rule 5.

### Stop applying enterprise procurement thinking

A separate reflex, same cost. Judging tools and choices by criteria nobody in the room holds.

Real examples from one session, all wrong:

- Flagging that an alpha framework requires a Go release candidate. It is an alpha, built by one
  person, being tried by one team. Nobody cares.
- Warning that a change would need review before production, on a branch nobody will merge.
- Raising a ticket in flight that touches an endpoint, in a prototype that will never ship.
- Noting that a tool is "unproven" when the operator is the person who wrote it.

Before writing a concern, ask who holds it. If the answer is a compliance function, a procurement
process, or a hypothetical reviewer, delete the sentence. If it is the person you are talking to,
say it.

The operator knows their own constraints better than you do. They chose the alpha tool. They
named the branch after a throwaway ticket. Repeating their own context back at them as a risk is
noise.

### Two caveats worth keeping

Not all hedging is hedging. Keep these:

1. **What the evidence does not support.** One cluster and one person is not proof, and saying so
   protects the reader from over-reading a real result.
2. **What you did not do that a reader would otherwise assume you did.** An unported behaviour, a
   delegated endpoint, a check you skipped. Say it plainly and move on.

The test: does the sentence tell the reader something they would otherwise get wrong? Keep it. Does
it exist to manage how they feel about the work? Cut it.

---

## Write plainly. This is not optional.

Applies to everything: chat replies, documents, commit messages, tickets, Slack. The operator reads
these to make decisions. A sentence they have to parse twice has failed.

Real feedback from a real session, after two warnings:

> stop speaking in riddles and bullshit consultant speak, it's exhausting and incomprehensible
> without a heavy cognitive load and I'm not paying to be stressed by you

### The rules

- **One idea per sentence.** Under 20 words.
- **Answer first, evidence second.** Never build up to the point.
- **Bad news first, plainly.** "The ticket is closed but the bug is still there."
- **No em-dash asides stacked in a sentence.** Use two sentences.
- **Tables and lists** for anything with more than two facts.
- **Do not explain why a fact matters** unless asked. They work it out faster than you can say it.

### Phrases to delete on sight

These announce importance instead of stating a fact:

Written with a brace so the linter below does not flag this list as its own violation.

```text
The thing that matters is...        -> say the thing
Worth saying plainly...             -> then say it plainly
That is the wh{o}le argument        -> the reader decides that
Here is the interesting part        -> show it
It is worth noting that...          -> note it
This is not hypothetical            -> give the example instead
That is not noth{i}ng               -> say what it is
```

Also cut any sentence describing the shape of your own reasoning. The reader wants the conclusion,
not a tour of how you got there.

Also cut: leverage, utilize, ensure, robust, comprehensive, seamless, streamline, facilitate,
delve, under the hood, out of the box.

### Check before delivering

```bash
node ~/Documents/code/cliche/cliche.mjs FILE.md      # exits 1 on a hit
grep -noE "\b(should|would|may|might|could)\b" FILE.md
```

Use `must` or `can` instead of `should`. In agent-facing text, `should` reads as optional.

For long documents, the `simple-english` skill has the full rule set: 20 words for instructions,
25 for explanations, conditions before commands, one word per concept.

---

## Phase 0 — Before you touch anything

Do these four in parallel. Each one has ended an investigation early.

### 0.1 Find the published contract and fetch it

Almost every Spring service serves OpenAPI at `/v3/api-docs` or similar, often behind a header
whose value is committed in `application.properties`. **Look for it before assuming you need a
local stack.** A `curl` against staging unblocks the whole parity workflow.

```bash
grep -rn "api-docs\|springdoc\|documentation.header" src/main/resources/config/
```

Check what fraction of the service it describes. `documentation.show-internal-endpoints=false` is
common, and it means the document covers the public subset only. Count it:

```bash
# operations in the document
python3 -c "import json;d=json.load(open('spec.json'));print(sum(1 for p,v in d['paths'].items() for m in v if m in ('get','post','put','delete','patch')))"
# endpoint mappings in the code
grep -rho "RequestMethod\.\(GET\|POST\|PUT\|DELETE\|PATCH\)" src/main/java | wc -l
```

If the ratio is bad, say so early. Every contract-first method is blind to the difference.

### 0.2 Search the wiki, not only the repo

The repo says what the code does. The wiki says why, where it is going, and how somebody already
solved it. Search for: an architecture strategy, ADRs, a migration plan, prior extraction memos,
and any in-flight ticket touching your endpoints.

Two things this finds that reading code never will: a service that **already owns** the domain you
are about to extract, and a prescribed extraction sequence the team has agreed to.

### 0.3 Get a working local environment, cheaply

If the repo's test harness starts many containers under one global timeout, do not use it for
development. Write a compose file with the services the application actually needs. A harness
tuned for CI is usually the wrong shape for an inner loop.

Check whether Testcontainers can find the Docker socket. Under Colima or OrbStack it cannot,
without:

```bash
export DOCKER_HOST="unix://$HOME/.colima/default/docker.sock"
export TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE=/var/run/docker.sock
```

The failure message names neither. It costs ten test errors that look like ten broken tests.

### 0.4 Record the known-bad baseline, by running it

Run the suite on the untouched main branch and write down what already fails. Do not skip this and
do not take a stale note for it. Later you will need to prove your change added no failure, and
the only convincing form is the same test names at the same line numbers on a clean worktree.

```bash
git worktree add /tmp/baseline main
cd /tmp/baseline && mvn test -Dtest='TheFailingOnes'
```

---

## Phase 1 — Pick the cluster

This is where the largest mistakes happen, and they are cheap to avoid.

### Rule 1: Extract along data ownership, never a URL prefix

A prefix is an *audience* grouping. Endpoints behind one prefix routinely reach into five
subsystems and five stores. List the collections or tables each candidate endpoint touches. If
the list has more than one or two entries, the cluster is wrong.

### Rule 2: Data ownership has a direction. Check the writes.

"Which endpoints touch this collection, and does anything outside the set write it?" is the
obvious question and it is not sufficient. Ask the second one: **what else does the writer
write?**

An endpoint that writes your collection may also update a second aggregate, call an external
service, and compute something that changes its own response shape. A cluster whose reads are
clean and whose writes span aggregates is a read extraction, not a service extraction. Both are
useful. They are different plans.

### Rule 3: The default is that it moves. Price what you leave behind.

The instinct to leave shared code in the monolith is the main way this exercise produces nothing.
A service with many consumers is not immovable. It means the consumers change, or they call the
new service. Both are work, and work is not a blocker.

Only one thing genuinely keeps code in place: moving it would drag in another whole domain. When
that happens, **write down what moving it would take.** "It has 23 consumers" is not a finding.
"Moving it costs 23 call sites and puts a network hop in the scoring path, so it is a second cut"
is a finding, and it is the one the architecture owner can act on.

The first run called a 23-consumer service immovable without pricing it. That was timid, and the
estimate was the more useful output.

### Rule 4: Writes delete cleanly. Reads leave a stump.

A write endpoint is usually the only thing performing its write, so its service has one caller and
deletes whole. A read is a projection, and projections get reused by whatever else renders the
same data.

Count callers before committing:

```bash
grep -rn "theService\.[a-zA-Z]*(" src/main/java | sed 's|src/main/java/||'
```

If a read service has many callers, extracting the endpoint **forks** the projection rather than
moving it. Either extract every consumer in the same cut, or make the monolith call the new
service and delete the local implementation. Do not leave two copies.

### Rule 5: A rule that ends an investigation has been misapplied

Repo rules bound what you may change. They do not bound what you may investigate. If a constraint
appears to make an endpoint unextractable, read the actual code path before accepting it. The
constraint often does not apply.

---

## Phase 2 — Generate the contract, do not transcribe it

**Never hand-write the design from source.** A careful transcription of a real DTO set will differ
from the running service in dozens of ways, and you will find them one at a time.

1. Slice the published document to your endpoints, with the transitive schema closure. Redocly CLI
   `split`, or a script.
2. Import it into whatever design format your generator uses.
3. Add by hand only what the importer refuses, and write down each one.
4. **Diff the generated document against the incumbent immediately**, before the design feels
   finished. That first diff is where transcription errors surface.

### Rule 6: Diff against a baseline to catch regressions; diff against the incumbent to classify

Zero differences is the right target against a **fixed baseline**, where any change is a
regression. It is the wrong target against the **incumbent**, where some differences mean your
document is more correct.

Driving the number to zero against the incumbent means reproducing its faults. Classify instead:
for each difference, record whether the incumbent or the new document is right, and why. Keep a
waivers file.

---

## Phase 3 — Read the code you are porting

### Rule 7: Names are claims. Verify them.

Confirmed liars are common. Before trusting a name, scan for the pattern:

```bash
# read-named methods that write, Readonly classes that write, findAll that filters
python3 migration_tools/namescan.py src/main/java
```

Then encode the checks as **frozen ArchUnit rules**, not a document. `FreezingArchRule` records
today's violations and fails only on new ones, so the list can only shrink. Store violations,
never approvals: an approvals list rots the moment a body changes under an approved name.

The triage output is not always a rename. A read that writes an audit event is non-idempotent and
uncacheable, so moving the write to the caller may be the honest fix. A rule cannot make that call.
It forces the question.

### Rule 8: Port the layer below the one you are reading

Open every method that returns a collection, however plain its name. A finder that filters is
invisible from its call site.

### Rule 9: Wire names are not field names

Hand-written getters override the field name Jackson serializes. A class can declare `mAdminArea`
and serialize `getmAdminArea`. **No file contains the string that goes on the wire.** Verify field
names against a generated document or a recorded response, never against the DTO alone.

### Rule 10: Two endpoints over one store are not one behaviour with two shapes

Diff their read paths explicitly: sort order, filters, masking, error semantics, pagination. A
list and a single read of the same rows commonly differ in sort direction alone.

---

## Phase 4 — Own the data

Reads first. They are safe, they prove the data access, and they hold the projection quirks. Then
writes.

**Reproduce partial updates as partial updates.** If the original does a targeted field update,
do the same. Converting it to a read-modify-write changes concurrency semantics and can drop
concurrent writes. Write a test that seeds unrelated fields and proves they survive.

**Check which replica a read uses.** A read-before-write must come from the primary. Using the
ordinary finder introduces a replication-lag race that appears under load and never in a test.

---

## Phase 5 — Delete the original

The extraction is not done until the original code is gone. This is the step that proves it.

1. **Find every declaration.** An endpoint often lives in three places: an API interface, a
   controller, and a shared base class other controllers extend. Deleting only the interface method
   compiles fine and leaves dead code.
2. **Check callers one level at a time** before deleting anything. Classes that look like part of
   your cluster frequently are not.
3. **Remove config entries** naming the endpoint: security path lists, feature flags, route
   tables.
4. **Grep for the class names after the build is green.** The compiler does not check comments, and
   a comment pointing at a deleted class is worse than none.
5. **Delete the tests** that covered the deleted code.

---

## Phase 6 — Prove it

### Rule 11: Verify before asserting, every time

The recurring failure mode is stating a cause that sounds right. Examples that were wrong:

- "The framework renders this incorrectly." It did not. A hand-written customizer did, and its
  name said so.
- "This service accepts either credential." True, but not verified until reading the filter's
  fallback three files later.

Before writing a causal claim in a document, message or commit, open the file that proves it. If
you cannot, write what you observed rather than why.

### Rule 12: Say which mechanism found each defect

When reporting, attribute every bug to the thing that caught it: the generated document, a test,
the compiler, or a person reading. This is the difference between a claim and evidence, and it
also shows which mechanisms are earning their place.

### Rule 13: Name the numbers you did not measure

An estimate and a measurement look identical in a table. Mark them. A regex scan and a bytecode
analysis of the same rule disagreed by 20% in both directions, and only one of them is worth
quoting.

---

## Working rules that keep costing time

### Never run two builds against one output directory

Two Maven runs sharing `target/` corrupt each other, and neither failure names the cause. One
produced a NUL-padded XML file and a parse error pointing nowhere. Another deleted `target/classes`
under a running architecture test, which then reported a missing class that exists.

Write a lock rather than a rule:

```bash
scripts/mvn-serial.sh clean verify      # refuses if another build holds target/
```

A rule in a playbook does not stop this. A script that exits 1 does.

### Commit serially, and never skip hooks

If commit hooks run a linter, two concurrent commits hit the same problem as two builds.

### Batch your questions

Rather than discovering facts one at a time, write the list of everything you need to know, then
search for all of it. Reactive discovery is how a two-hour task becomes a day.

---

## What to write down as you go

Keep three files. Write them **during** the work; reconstructing them afterwards loses the
friction that is worth sharing.

| File | Contents |
|---|---|
| `DECISIONS.md` | Chronological. Every attempt, what broke, what it cost. Including wrong turns. |
| `PLAYBOOK.md` | The distilled rules, each tagged with what it cost |
| `WAIVERS.md` | Every classified difference between the new document and the incumbent |

**Journal why a bug happened, not only that it did.** "Oversight" and "the tool hid it from me"
call for different fixes. A grep that filtered out the line you needed is a tooling fix. A name you
believed is an ArchUnit rule.

---

## Reporting

The audience is engineering leads deciding whether to continue. Four things, in this order:

1. **It finishes.** The original code is deleted and the suite is no worse. Show the before and
   after on the same tests.
2. **It is faster.** Time and difference counts, hand-written against generated.
3. **It catches defects reading does not.** The table from Rule 11.
4. **It leaves tools behind.** The second extraction is cheaper because of what the first built.

Then state what it does not prove: one cluster, one person, no control group. What would make it
proof is a second extraction by somebody else.

**Cut the caveats that are obvious.** "Nothing is deployed" adds nothing to a proof of concept
nobody could deploy. Keep the caveats a reader would otherwise get wrong.

### Language

Short sentences, one idea each. Put the answer first and the evidence after. Cut phrases that
announce importance instead of stating a fact. Run the text through a cliché checker before
delivering.

---

## Anti-patterns

| Do not | Instead |
|---|---|
| Pick a cluster by URL prefix | Pick by data ownership, checking the writes |
| Hand-write the design from source | Generate it from the published contract |
| Drive incumbent differences to zero | Classify them and keep the ones where you are right |
| Trust a method name | Verify it, then freeze an ArchUnit rule |
| Leave a forked projection in both languages | Make the monolith call the new service |
| Leave code behind because it has many consumers | Default to moving. If it stays, price the move. |
| Write a rule in a document and rely on it | Write the check that fails the build |
| Add a constraint the incumbent lacks | It rejects traffic the incumbent accepts |
| Assert a cause you have not read | Open the file, or write only what you observed |
| Flag a risk nobody in the room holds | Ask who holds it. If it is procurement, delete it. |
| Report a scanner estimate as a count | Mark estimates, quote measurements |
