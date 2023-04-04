# IMC Prosperity
I put here my trading bots and other codes related to IMC's trading competition Prosperity.
## Matching Engine
Someone who had experience with quantitative developer interviews told me he was sometimes asked to code out a matching engine. So I think it would be great to include my `matching_engine.py` here to showcase my work.

Matching engine is essentially my backtester for my trading bots. It aims to simulate the trading activities in the competition and provide me with a log that is competible with [this wonderful visualizer](https://jmerle.github.io/imc-prosperity-visualizer/) built by Jasper.

It matches orders placed by any bot inside the `traders` folder against the order book created using the sample datasets provided by IMC. The competition rules say that an order placed at time t will first be matched against the active orders on the order book, and any leftover orders will remain on the book for other bots to trade against until time t+1. Because I have no knowledge about how IMC implements their trading bots (they are not disclosed), I cannot deal with leftover orders with accuracy. This engine also tries to match orders will better prices first before matching with exact prices to mimic limit order behavior. It will, of course, make sure that the position limits are not breached.

To-do list:

1. Add profit and loss calculation for each timestamp
3. Add logging support
2. Expand engine support to all rounds (currently only round 1 is supported)

## Traders
`default.py` is the example bot provided by IMC.