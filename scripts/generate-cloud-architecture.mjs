#!/usr/bin/env node

/**
 * Generate the checked-in, self-contained cloud-pilot topology.
 *
 * This is intentionally an intended architecture diagram, not cloud execution
 * evidence. Keeping the source in the repository makes the visual reviewable and
 * avoids dependence on a remote diagram service.
 */
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const output = resolve(root, 'docs/assets/flagship-cloud-architecture.svg');

const card = (x, y, w, h, icon, title, detail, tone = 'blue') => {
  const colors = {
    aws: ['#fff7ed', '#c2410c'], blue: ['#eff6ff', '#1d4ed8'],
    green: ['#f0fdf4', '#15803d'], purple: ['#faf5ff', '#7e22ce'],
    slate: ['#f8fafc', '#475569'],
  };
  const [fill, stroke] = colors[tone];
  return `<g><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="12" fill="${fill}" stroke="${stroke}" stroke-width="1.4"/>
    <circle cx="${x + 31}" cy="${y + h / 2}" r="19" fill="#fff" stroke="${stroke}" stroke-width="1.2"/>
    <text x="${x + 31}" y="${y + h / 2 + 6}" class="icon" text-anchor="middle">${icon}</text>
    <text x="${x + 60}" y="${y + 31}" class="card-title">${title}</text>
    <text x="${x + 60}" y="${y + 53}" class="card-detail">${detail}</text></g>`;
};
const arrow = (x1, y1, x2, y2, label = '') => `<g><path d="M ${x1} ${y1} L ${x2} ${y2}" class="arrow" marker-end="url(#arrowhead)"/>${label ? `<text x="${(x1+x2)/2}" y="${(y1+y2)/2-8}" class="edge" text-anchor="middle">${label}</text>` : ''}</g>`;

const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1170" viewBox="0 0 1600 1170" role="img" aria-labelledby="title desc">
 <title id="title">Multi-Tenant AI Platform — intended AWS cloud-pilot architecture</title>
 <desc id="desc">An icon-based intended AWS architecture for the flagship: narrow browser ingress, private EKS services, Redis, PostgreSQL, model artifacts, GitOps, delivery, and observability. It has not been deployed.</desc>
 <defs><marker id="arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#64748b"/></marker><style>
 text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#0f172a}.title{font-size:30px;font-weight:700}.subtitle{font-size:16px;fill:#475569}.group{font-size:16px;font-weight:700}.sub{font-size:13px;fill:#475569}.card-title{font-size:14px;font-weight:700}.card-detail{font-size:12px;fill:#475569}.icon{font-size:17px;font-weight:700}.arrow{fill:none;stroke:#64748b;stroke-width:1.6}.edge{font-size:12px;fill:#475569}.note{font-size:13px;fill:#475569}.legend{font-size:12px;fill:#475569}
 </style></defs>
 <rect width="1600" height="1170" fill="#fff"/>
 <text x="60" y="58" class="title">Multi-Tenant AI Platform — intended AWS cloud-pilot architecture</text>
 <text x="60" y="86" class="subtitle">Design and static-validation target only — no AWS resource or cloud runtime has been executed from this repository.</text>
 <rect x="60" y="118" width="1480" height="142" rx="18" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.4"/>
 <text x="84" y="149" class="group">People, control, and delivery boundary</text>
 ${card(90,171,190,66,'U','Applications / agents','signed tenant requests','green')}
 ${card(305,171,190,66,'UI','Operator Console','narrow browser surface','green')}
 ${card(545,171,205,66,'GH','GitHub Actions','OIDC; no stored keys','purple')}
 ${card(780,171,205,66,'PR','Protected desired state','review before reconcile','purple')}
 ${card(1015,171,220,66,'TF','Terraform','only provision / destroy','aws')}
 ${card(1265,171,245,66,'AUD','Audit + evidence','plans, actions, outcomes','slate')}
 ${arrow(280,204,305,204)}${arrow(750,204,780,204)}${arrow(985,204,1015,204)}
 <rect x="60" y="295" width="1480" height="790" rx="18" fill="#fffaf4" stroke="#fb923c" stroke-width="1.5"/>
 <text x="84" y="328" class="group">AWS account / selected region — planned private pilot footprint</text>
 <text x="84" y="351" class="sub">An eventual ALB may expose only Console, API, and identity. Model/data stores, observability, and cluster administration remain private.</text>
 <rect x="90" y="382" width="282" height="640" rx="15" fill="#fff" stroke="#fed7aa" stroke-width="1.2"/>
 <text x="112" y="414" class="group">Terraform foundation</text>
 ${card(112,440,238,68,'S3','S3 remote state','encrypted + versioned','aws')}
 ${card(112,526,238,68,'LOCK','DynamoDB lock','project-scoped state','aws')}
 ${card(112,612,238,68,'IAM','IAM + IRSA','least-privilege roles','aws')}
 ${card(112,698,238,68,'ECR','Amazon ECR','immutable images','aws')}
 ${card(112,784,238,68,'SEC','Secrets Manager','runtime secret boundary','aws')}
 ${card(112,870,238,68,'VPC','VPC + subnets','public ingress / private apps','aws')}
 <rect x="402" y="382" width="1115" height="640" rx="15" fill="#f8fbff" stroke="#93c5fd" stroke-width="1.2"/>
 <text x="426" y="414" class="group">VPC runtime boundary</text><text x="426" y="437" class="sub">CPU-first by default. GPU node groups and physical accelerator measurements remain separate, cost-approved work.</text>
 ${card(430,466,266,72,'ALB','Application Load Balancer','Console / API / identity only','blue')}
 <rect x="720" y="466" width="768" height="395" rx="14" fill="#fff" stroke="#60a5fa" stroke-width="1.4"/>
 <text x="744" y="496" class="group">Amazon EKS — private workloads</text><text x="744" y="519" class="sub">Gateway admission stays the authority; all platform slices integrate through bounded APIs and state contracts.</text>
 ${card(748,547,170,66,'GW','Gateway ×2','JWT + quota + routing','blue')}
 ${card(938,547,170,66,'ONNX','CPU runtimes','real ONNX serving','blue')}
 ${card(1128,547,170,66,'REL','Release control','MLflow plans/canary','purple')}
 ${card(1318,547,145,66,'OPA','Policy','admission guard','green')}
 ${card(748,637,170,66,'OPS','Operations','remediation + audit','blue')}
 ${card(938,637,170,66,'AG','Agent tools','delegated scopes','green')}
 ${card(1128,637,170,66,'DEV','Self-service','tenant profiles','green')}
 ${card(1318,637,145,66,'EDGE','Edge adapter','policy boundary','blue')}
 ${card(748,727,170,66,'OT','OTel Collector','traces / export','purple')}
 ${card(938,727,170,66,'P','Prometheus','metrics / alerts','purple')}
 ${card(1128,727,170,66,'T','Tempo','trace storage','purple')}
 ${card(1318,727,145,66,'G','Grafana','operator evidence','purple')}
 ${card(430,892,250,72,'RDS','RDS PostgreSQL','release/audit/control state','aws')}
 ${card(700,892,250,72,'REDIS','ElastiCache Redis','admission + metering','aws')}
 ${card(970,892,250,72,'S3','S3 artifacts','MLflow/model artifacts','aws')}
 ${card(1240,892,248,72,'CD','GitOps reconciler','Argo CD or equivalent','purple')}
 ${arrow(696,502,720,580)}${arrow(918,580,938,580)}${arrow(1108,580,1128,580)}${arrow(1298,580,1318,580)}
 ${arrow(833,613,833,637)}${arrow(1023,613,1023,637)}${arrow(1213,613,1213,637)}${arrow(1390,613,1390,637)}
 ${arrow(833,703,833,727)}${arrow(1023,703,1023,727)}${arrow(1213,703,1213,727)}${arrow(1390,703,1390,727)}
 ${arrow(833,793,555,892,'durable control state')}${arrow(1023,613,825,892,'shared admission')}${arrow(1213,613,1095,892,'artifacts')}${arrow(1300,204,1364,892,'approved desired state')}
 <rect x="60" y="1113" width="1480" height="40" rx="10" fill="#f8fafc" stroke="#cbd5e1"/>
 <text x="84" y="1138" class="legend">Legend: orange = AWS foundation/data service · blue = serving/runtime · green = identity/policy boundary · purple = delivery/observability.</text>
 <text x="1110" y="1138" class="legend">Status: intended architecture; not cloud-executed.</text>
</svg>`;

await mkdir(dirname(output), { recursive: true });
await writeFile(output, svg);
console.log(`Wrote ${output}`);
