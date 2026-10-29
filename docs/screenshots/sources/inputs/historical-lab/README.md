# Historical public-lab integration

This fixture imports three **previously published** reports from Carlos Alvarado's [Network Lab Factory v0.1.1](https://github.com/carlosalpo/network-lab-factory/releases/tag/v0.1.1), commit `137a2cb89460b080253fdce07f7e6ba397962347`. The evidence files are copied byte for byte; [provenance.json](provenance.json) records their exact source URLs and hashes.

The original laboratory used synthetic addressing and reported 20/20 checks at baseline, 18/20 during the controlled fault, and 20/20 after recovery. Those are historical observations from the source project. This kit performs **no new lab access, device commands, packet tests or independent validation of those observations**.

The input declares source run timestamps derived from the reports' `run_id` fields and fixes `as_of` at 2026-10-29 18:00 UTC. Each `exit_code: 0` represents successful local import of an existing report, not the result of the tests inside that report. Therefore all three evidence requirements can be **collected**, including the fault report containing two failed checks. This is intentional: collection coverage is not device health.

The observation about the controlled fault is a manually authored finding with references to the retained source reports. Its correctness is not inferred by the kit. No convergence-time or production SLA claim is made.

```sh
iek build --input examples/historical-lab/assessment.json \
  --evidence-root examples/historical-lab/evidence --output historical-demo
iek verify --bundle historical-demo
```

The source project and this project are MIT licensed. Documentation/synthetic-lab addresses in these files are not the user's private management addresses.
