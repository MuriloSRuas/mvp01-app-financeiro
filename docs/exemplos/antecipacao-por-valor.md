# Antecipação de parcelas

Gerado em 31/10/2026 às 14:05.

## Dados informados

| Parâmetro                             | Valor       |
| ------------------------------------- | ----------- |
| Valor da parcela (P)                  | R$ 500,00   |
| Juros do contrato (i)                 | 2% ao mês   |
| Parcelas restantes, além da atual (m) | 10          |
| Valor disponível para antecipar       | R$ 1.000,00 |

## Fórmula

```text
valor a pagar hoje = P / (1 + i)^j
economia = P − valor a pagar hoje
```

`j` é o número de meses até o vencimento da parcela. Pagando hoje, você deixa de pagar os juros desses `j` meses. As **últimas** parcelas (maior `j`) são antecipadas primeiro, porque são as que mais economizam.

Com valor disponível: soma-se o valor a pagar a partir da última parcela, indo para trás, enquanto o total couber no valor.

## Passo a passo

| Vence em  | Cálculo          | Valor a pagar hoje | Economia      |
| --------- | ---------------- | ------------------ | ------------- |
| 10 meses  | 500,00 / 1,02^10 | R$ 410,17          | R$ 89,83      |
| 9 meses   | 500,00 / 1,02^9  | R$ 418,38          | R$ 81,62      |
| **Total** |                  | **R$ 828,55**      | **R$ 171,45** |

A próxima parcela (vence em 8 meses) custaria R$ 426,75 hoje e não cabe no que sobra (R$ 171,45).

## Resultado

**Pagando R$ 828,55 hoje, você economiza R$ 171,45 em juros.**

Isso quita 2 parcelas (as que venceriam em 10 e 9 meses), no lugar de pagar R$ 1.000,00 nas datas originais.

Continuam a vencer normalmente: a parcela atual (paga hoje) e as 8 que vencem de 1 a 8 meses.

Sobram R$ 171,45 do valor disponível.

> [!warning] Aviso
> Os valores são uma **estimativa** pela fórmula de valor presente. A quitação real depende do contrato e deve ser confirmada com o credor.
