#TODO: Add PnL support
#TODO: Add Logging support
#TODO: So far only supports round 1 data

import pandas as pd
from datamodel import Listing, OrderDepth, Trade, TradingState, Order
from traders.default import Trader

LISTINGS = {
    "PEARLS": Listing(symbol="PEARLS", product="PEARLS", denomination="SEASHELLS"),
    "BANANAS": Listing("BANANAS", "BANANAS", "SEASHELLS")
}
POS_LIMIT = {"PEARLS": 20, "BANANAS": 20}
ROUND = 1
DAY = -1
NAME = "nn"


class Myself:
    """ A class to record position and profit and loss"""
    def __init__(self):
        self.position = {product: 0 for product in LISTINGS}
        self.pnl = 0
        self.trader = Trader()
        self.trade_hist = {} #timestamp as key and own_trades as value


def generate_state(timestamp, prices_snapshot, trades_snapshot, myself):
    """
    Generates the TradingState for each iteration.
    """
    #Build order_depths
    order_depths = {}
    for _, row in prices_snapshot.iterrows():
        order_depth = OrderDepth()
        for j in range(1, 4):
            if pd.notna(row["bid_price_" + str(j)]):
                order_depth.buy_orders[int(row["bid_price_" + str(j)])] = \
                    int(row["bid_volume_" + str(j)])
        for j in range(1, 4):
            if pd.notna(row["ask_price_" + str(j)]):
                order_depth.sell_orders[int(row["ask_price_" + str(j)])] = \
                    int(row["ask_volume_" + str(j)])
        order_depths[row["product"]] = order_depth

    #Build market_trades
    market_trades = {product: [] for product in LISTINGS}
    for _, row in trades_snapshot.iterrows():
        buyer = row["buyer"] if pd.notna(row["buyer"]) else ""
        seller = row["seller"] if pd.notna(row["seller"]) else ""
        market_trades[row["symbol"]].append(Trade(
            row["symbol"], int(row["price"]), int(row["quantity"]), buyer, seller, timestamp
        ))

    position = myself.position
    own_trades = \
        myself.trade_hist[timestamp-100] if timestamp !=0 else {product: [] for product in LISTINGS}
    observations = {}

    return TradingState(
        timestamp, LISTINGS, order_depths, own_trades, market_trades, position, observations
        )


def matching(orders, state, myself):
    """
    Matches the bot's order with existing order book orders.
    Takes in a list of orders from run(), edits myself.position, and output own_trades
    Example: {"PEALS": [(PEARLS, 10002, -1)]}
    """
    own_trades = {product: [] for product in LISTINGS}
    outstanding_orders = {product: [] for product in LISTINGS}

    for product, order_list in orders.items():
        for order in order_list:
            #Checks position limit
            if abs(myself.position[product] + order.quantity) <= POS_LIMIT[product]:
                outstanding_quantity = order.quantity
            else:
                outstanding_quantity = \
                    order.quantity/abs(order.quantity)*POS_LIMIT[product] - myself.position[product]
            if outstanding_quantity > 0: #> 0 is a buy order, matched against sell_orders
                for price, quantity in state.order_depths[product].sell_orders.items():
                    if price <= order.price: #signals a legal buy
                        if quantity >= outstanding_quantity:
                            myself.position[product] += outstanding_quantity
                            own_trades[product].append(Trade(product, price, outstanding_quantity, \
                                                             "Myself", "", state.timestamp))
                            outstanding_quantity = 0
                        else:
                            myself.position[product] += quantity
                            own_trades[product].append(Trade(product, price, quantity, "Myself", \
                                                             "", state.timestamp))
                            outstanding_quantity -= quantity
            elif outstanding_quantity < 0: #< 0 is a sell order, matched against buy_orders
                for price, quantity in state.order_depths[product].buy_orders.items():
                    if price >= order.price: #signals a legal sell
                        if quantity >= -outstanding_quantity:
                            myself.position[product] += outstanding_quantity
                            own_trades[product].append(Trade(product, price, outstanding_quantity, \
                                                             "", "Myself", state.timestamp))
                            outstanding_quantity = 0
                        else:
                            myself.position[product] -= quantity
                            own_trades[product].append(Trade(product, price, -quantity, "", \
                                                             "Myself", state.timestamp))
                            outstanding_quantity += quantity
            else: #outstanding_quantity == 0
                break
            if outstanding_quantity != 0:
                outstanding_orders[product].append(Order(product,order.price,outstanding_quantity))

    myself.trade_hist[state.timestamp] = own_trades
    return outstanding_orders


prices_data = pd.read_csv(
    "island_data_bottle/prices_round_"+str(ROUND)+"_day_"+str(DAY)+".csv"
)
trades_data = pd.read_csv(
    "island_data_bottle/trades_round_"+str(ROUND)+"_day_"+str(DAY)+"_"+NAME+".csv"
)
myself = Myself()
for i in range(100): #Full thing is 10000
    timestamp = i*100
    prices_snapshot = prices_data[prices_data["timestamp"]==timestamp]
    trades_snapshot = trades_data[trades_data["timestamp"]==timestamp]
    state = generate_state(timestamp, prices_snapshot, trades_snapshot, myself)
    orders = myself.trader.run(state)
    outstanding_orders = matching(orders, state, myself)
