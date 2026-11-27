# Draft: request reconsideration of the On-Demand G/VT quota

**Status:** the owner reports manually submitting this appeal through the existing
case in AWS Support Center. The AWS CLI `add-communication-to-case` attempt was
rejected because this account's Support plan does not allow the Support API. The
quota-history API still shows `CASE_OPENED` and the applied quota is zero; no new AWS
response has appeared in the connected email search yet. Do not submit this appeal
again while awaiting AWS.

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
- The owner authorized reopening the existing case and later reported submitting the
  appeal manually through Support Center. The connected email search has not yet
  found a new AWS response, and the quota API status has not changed. The installed AWS CLI has no
  `support reopen-case` operation. The available `support add-communication-to-case`
  call was attempted using the existing case ID and this proposed message, after
  verifying the AWS account identity. AWS rejected it with
  `SubscriptionRequiredException`; no message was sent. AWS's CLI help says the
  Support API requires Business, Enterprise On-Ramp, or Enterprise Support.
- The Service Quotas CLI has `create-support-case`, but it only creates a Support
  case for a request in `PENDING` status. This existing request reports `CASE_OPENED`,
  so that command does not reopen or update it and was not called.
- Do not resubmit the appeal, create a duplicate quota request, or create a related
  case by accident while awaiting AWS's reply. The Support Center route was used by
  the owner, as described in the official support guide.

References:

- [AWS: Requesting a quota increase](https://docs.aws.amazon.com/servicequotas/latest/userguide/request-quota-increase.html)
- [AWS: Verifying your quota request](https://docs.aws.amazon.com/servicequotas/latest/userguide/quota-history.html)
- [AWS Support: Updating, resolving, and reopening a case](https://docs.aws.amazon.com/awssupport/latest/user/monitoring-your-case.html)
