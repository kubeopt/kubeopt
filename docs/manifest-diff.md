# Manifest Resource Preview

Compare requested resources between two Git commits without a running server,
cloud credentials, or a collector connection.

```sh
python cli.py diff --base origin/main --head HEAD
python cli.py diff --base origin/main --head HEAD --format markdown
python cli.py diff --repo /path/to/repo --base BASE_SHA --head HEAD_SHA
```

Installing the Python package with `pip install .` also provides `kubeopt diff`.
This command is not yet exposed by the separately maintained npm CLI.

## Output Contract

JSON is the default. It includes resolved commit SHAs, typed workload changes,
container requests and limits before and after, aggregate and per-pod deltas,
pricing availability, and a rendered `markdown` field. Use `--format markdown`
to print only the comment body. Diagnostics go to stderr and failures return
exit code 1 without a partial report.

Quantities are normalized decimal strings: CPU in millicores, memory in bytes,
and GPU counts by vendor. Unknown values are JSON `null`, not zero. Requests
default from explicitly specified limits where Kubernetes applies that default;
namespace admission defaults are not inferred.

Only changed `.yaml` and `.yml` files are read, from the committed base and head
trees. Uncommitted files are ignored. Comparisons use both supplied snapshots
directly, rather than `HEAD~1`. For PRs supply the intended base/head commit SHAs
and ensure those objects are present in the checkout. Renames do not create
false changes when workload identity and resources are unchanged.

## Supported Manifests

- Plain `apps/v1` Deployment, StatefulSet, and DaemonSet manifests.
- Multiple YAML documents and Kubernetes `List` documents.
- CPU, memory, `nvidia.com/gpu`, and `amd.com/gpu` requests and limits.
- Added, removed, and modified workloads, keyed by kind, namespace, and name.
- Declared replicas for Deployments and StatefulSets, defaulting to one.

DaemonSets report per-pod resource differences; workload totals are unavailable
because eligible node counts are not known. Workloads containing init containers
retain container specifications but report aggregate resources as unavailable;
init-container and restartable sidecar scheduling are not modeled.

Malformed manifests, duplicate YAML keys, ambiguous duplicate workload identities,
invalid quantities, missing refs, symlink manifests, and oversized manifests fail
with diagnostics. Unrelated YAML objects are ignored. Templates must be rendered
outside this command; it never executes repository code, Helm, or plugins.
Pod-level resource declarations also fail explicitly, because silently ignoring
them would produce incorrect container-based totals.

## Pricing Boundary

`--node-monthly-cost N` accepts an explicit non-negative monthly USD node price.
The input is recorded and displayed only when supplied. A node price alone does
not establish a per-workload rate, node requirement, or billing change. Both
`monthly_allocation_delta` and `billing_delta` remain `null` in this release,
even when a node price is supplied.

Resource changes describe declared requested capacity, not observed usage.
Scheduling, node selectors, admission defaults, pod overhead, runtime autoscaling,
capacity modeling, and billing prediction are outside this release.

## Delivery Scope

Acceptance criteria for the task:

1. Both source and installed Python CLI paths work offline.
2. Resource arithmetic preserves Kubernetes units and explicit unknowns.
3. Additions, removals, replica changes, container changes, and moves are covered.
4. JSON and markdown communicate missing pricing and capacity information.
5. Invalid input returns an actionable error instead of a partial estimate.
6. No GitHub Action workflow changes, PR posting, Helm rendering, placement
   analysis, or billing prediction are included.

Future Action integration should run this command and consume its JSON or markdown.
It should use actual PR base/head SHAs and update a single comment. This release
does not create or update GitHub comments.

Resource semantics follow the Kubernetes documentation for
[container requests and limits](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
and [GPU scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/).
