# IMC Prosperity
I put here my trading bots and other codes related to IMC's trading competition Prosperity.

## Matching Engine
Someone who had experience with quantitative developer interviews told me he was sometimes asked to code out a matching engine. So I think it would be great to include my `matching_engine.py` here to showcase my work. I don't think this is the fastest backtester for this competition out there but it is likely to be one of the most concise one.

Matching engine is essentially my backtester for my trading bots. It aims to simulate the trading activities in the competition and provide me with a log that is competible with [this wonderful visualizer](https://jmerle.github.io/imc-prosperity-visualizer/) built by Jasper.

It matches orders placed by any bot inside the `traders` folder against the order book created using the sample datasets provided by IMC. The competition rules say that an order placed at time t will first be matched against the active orders on the order book, and any leftover orders will remain on the book for other bots to trade against until time t+1. Because I have no knowledge about how IMC implements their trading bots (they are not disclosed), I cannot deal with leftover orders with accuracy. This engine also tries to match orders will better prices first before matching with exact prices to mimic limit order behavior. It will, of course, make sure that the position limits are not breached.

PnL calculation was also added. The profit of each product is calculated as the purchasing (negative)/selling (positive) price plus the equity value of the product. One benefit of doing so is that I can conveniently update the equity values of products on every tick without remembering their original prices.

Logging support was also added to the backtester so that the format is compatible with Jasper's visualizer.

To-do list:
1. Expand engine support to all rounds (currently only round 1 is supported)
2. Perhaps add bots that mimic the bevaior of IMC's trading bots

## Traders
`default.py` is the example bot provided by IMC.
`default_with_log.py` is the example bot provided by IMC but is made compatible with visualiser.
`stanford_cardinal.py` is the trade bot by [team Stanford Cardinal](https://github.com/ShubhamAnandJain/IMC-Prosperity-2023-Stanford-Cardinal). They ranked #2 overall in the competition. All credit goes to them.
