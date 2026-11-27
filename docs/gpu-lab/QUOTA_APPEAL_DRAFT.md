# Draft: request reconsideration of the On-Demand G/VT quota

**Status:** draft only. It has not been sent to AWS.

## Proposed message

Please reconsider the request for a 4-vCPU On-Demand G and VT instances quota in
`us-east-1`. The quota is needed for a short, controlled educational engineering lab
that will deploy one `g6.xlarge` instance at a time. This instance type uses four
vCPUs and one NVIDIA L4 GPU. The requested quota would not permit a second instance.

This is not a production service, customer workload, model-training job, or continuous
deployment. The experiment will use one small open-weight language model to validate
GPU drivers, CUDA, container access, inference, and monitoring. No customer prompts or
customer data will be processed.

The owner has set a hard total project spending ceiling of USD $25. The GPU instance
will run only in consolidated sessions, with a target maximum of 8–12 cumulative
instance-hours. Current pricing, storage, public IPv4, data transfer, state, taxes,
and all other charges will be reviewed before launch. If the full estimate does not
fit below the ceiling, the instance will not be launched.

The deployment is limited to one GPU instance in Terraform. It will have no public
inbound access and will be administered with AWS Systems Manager Session Manager.
Terraform will set an explicit expiry time; a host timer and a one-time AWS scheduled
termination provide independent shutdown safeguards. The instance and unnecessary
supporting resources will be removed after each execution batch, with resource absence
verified afterward.

Please enable a maximum quota of four vCPUs for On-Demand G and VT instances in
`us-east-1` to support this single-instance, short-duration experiment. No higher
quota is requested.

## Evidence and next steps

- AWS's email notification supplied by the account owner reports that the initial
  request was denied and asks for a detailed use case.
- The read-only Service Quotas history query still returned `CASE_OPENED` for the
  existing request, so the API and email status disagree. The applied quota remains
  zero.
- `us-east-2` and `us-west-2` also currently report zero applied On-Demand G/VT quota;
  `g6.xlarge` is listed as an offering in both regions. Switching regions alone does
  not currently remove the quota blocker.
- Reopening through the AWS Support API is unavailable to this account profile; the
  read-only call returned `SubscriptionRequiredException`. AWS documents reopening
  a resolved case through the Support Center console.
- Do not submit a duplicate Service Quotas request while the original record still
  exists. Confirm the final status and reopen the existing case through the console
  with the proposed use case if the owner decides to appeal.

References:

- [AWS: Requesting a quota increase](https://docs.aws.amazon.com/servicequotas/latest/userguide/request-quota-increase.html)
- [AWS: Verifying your quota request](https://docs.aws.amazon.com/servicequotas/latest/userguide/quota-history.html)
- [AWS Support: Updating, resolving, and reopening a case](https://docs.aws.amazon.com/awssupport/latest/user/monitoring-your-case.html)
