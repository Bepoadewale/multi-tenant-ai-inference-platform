# Flagship GitOps Contract

This Argo CD `Application` is a static delivery contract. It is not connected to an
Argo CD installation and has not reconciled a cloud cluster.

The future bootstrap must replace each `REPLACE_WITH_*` value with an immutable ECR
reference and the Terraform-created gateway IRSA role. A protected desired-state PR,
not the API process, should be the authority that changes these values.

The chart defaults to no ingress. If a later pilot enables ALB ingress, it must route
only browser Console/API/identity paths; data stores and observability remain private.
