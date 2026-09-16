# Cloud escalation example (sanitised correctly)

Pepe internally knows: Project Atlas, target name, CIM p.14, mgmt accounts,
$42m EBITDA, $3.2m normalisation, 8.5x entry, debt pending.

Task benefits from stronger reasoning → Pepe asks:

> "This task would benefit from a stronger reasoning model. I can send a
> de-identified representation to the approved cloud provider. Proceed?"

On approval, the payload sent (minimum necessary, sanitised locally):

> Company A. Revenue: $420m. EBITDA: $84m. Entry multiple: 10.5x.
> Debt: 5.0x EBITDA. Exit multiple: 9.0x.
> Question: Does this downside scenario satisfy a 15% IRR hurdle?

Never sent: company name, CIM, customer data, full financials, debt agreements.
Audit records: task, provider/model, reason, classification, payload hash +
sanitisation report, approval, result reference.
