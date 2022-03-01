-- Indentify latest gains/losses.

SELECT acc.name, th.name, th.symbol, th.n_shares, th.unit_cost,
printf("%10.2f", (th.current_price - th.unit_cost) / th.unit_cost * 100) "Profit/Loss %"
FROM trade_history th,
(SELECT max(history_date) "history_date" FROM trade_history) hd
INNER JOIN account acc ON acc.number = th.account
WHERE th.history_date = hd.history_date
ORDER BY (th.current_price - th.unit_cost) / th.unit_cost * 100;
