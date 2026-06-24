# Calculation Model

Use this template for market-entry and profitability review documents.

## Inputs

| Input | Value | Unit | Evidence | Confidence |
| --- | --- | --- | --- | --- |
| Target accounts |  | accounts |  |  |
| Conversion rate |  | % |  |  |
| ARPA |  | currency/month |  |  |
| Gross margin |  | % |  |  |
| CAC |  | currency/account |  |  |
| Payback window |  | months |  |  |

## Core Formulas

```text
expected_customers = target_accounts * conversion_rate
monthly_revenue = expected_customers * arpa
gross_profit = monthly_revenue * gross_margin
payback_months = cac / monthly_gross_profit_per_customer
break_even_customers = fixed_monthly_cost / monthly_gross_profit_per_customer
```

## Scenario Table

| Scenario | Customers | Monthly Revenue | Gross Profit | Payback | Decision Signal |
| --- | ---: | ---: | ---: | ---: | --- |
| Conservative |  |  |  |  |  |
| Base |  |  |  |  |  |
| Upside |  |  |  |  |  |

## Sensitivity Notes

List the variables that most change the decision. Mark any unsupported estimate as an assumption.
