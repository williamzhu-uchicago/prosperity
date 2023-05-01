#TODO: So far only supports round 1 data

import pandas as pd
from datamodel import Listing, OrderDepth, Trade, TradingState, Order
from traders.default_with_log import Trader, Logger

LISTINGS = {
    "PEARLS": Listing(symbol="PEARLS", product="PEARLS", denomination="SEASHELLS"),
    "BANANAS": Listing("BANANAS", "BANANAS", "SEASHELLS")
}
POS_LIMIT = {"PEARLS": 20, "BANANAS": 20}
ROUND = 1
DAY = -1
NAME = "nn" #If name of trader included (nn/wn)


class MyLog:
    """A class to record logged items"""
    def __init__(self):
        self.sandbox = "Sandbox logs:\n"
        self.submission = "Submission logs:\n"
        self.activities = "Activities log:\n" + "day;timestamp;product;bid_price_1;" + \
            "bid_volume_1;bid_price_2;bid_volume_2;bid_price_3;bid_volume_3;ask_price_1;" + \
            "ask_volume_1;ask_price_2;ask_volume_2;ask_price_3;ask_volume_3;mid_price;" + \
            "profit_and_loss\n"


class Myself:
    """ A class to record position and profit and loss"""
    def __init__(self):
        self.position = {product: 0 for product in LISTINGS}
        self.pnl = {} #timestamp as key and profit_dict {product:profit} as value
        self._cost = {product: 0 for product in LISTINGS} #Helper variable to calculate profit
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


def calculate_profit(timestamp, state, myself):
    """
    Calculates the current pnl of the bot.
    PNL is the sum of equity values (all products' mid-prices multiplied by the
    bot's positions) plus cost of purchase (negative if buy, positive if sell)
    """
    trades_made = myself.trade_hist[timestamp]
    profit = {product: 0 for product in LISTINGS}

    for product in LISTINGS:
        equity_value = 0
        mid_price = (max(state.order_depths[product].buy_orders) + min(state.order_depths[product].sell_orders)) / 2
        equity_value += (mid_price * myself.position[product])
        for trade in trades_made[product]:
            myself._cost[product] -= (trade.price * trade.quantity)
        profit[product] = equity_value + myself._cost[product]

    myself.pnl[timestamp] = profit
    return profit


def generate_log(timestamp, prices_snapshot, log, log_result):
    """
    A function to record the logs
    """
    log.sandbox += (str(timestamp) + " " + log_result +"\n")

    for _, row in prices_snapshot.iterrows():
        temp_lst = row.tolist()
        new_lst = ["" if pd.isna(i) else str(i) for i in temp_lst]
        new_lst[-1] = str(myself.pnl[int(new_lst[1])][new_lst[2]])
        activity = ";".join(new_lst)
        log.activities += (activity + "\n")



prices_data = pd.read_csv(
    "island_data_bottle/prices_round_"+str(ROUND)+"_day_"+str(DAY)+".csv"
)
trades_data = pd.read_csv(
    "island_data_bottle/trades_round_"+str(ROUND)+"_day_"+str(DAY)+"_"+NAME+".csv"
)
my_log = MyLog()
myself = Myself()
for i in range(10000): #Full thing is 10000
    timestamp = i*100
    prices_snapshot = prices_data[prices_data["timestamp"]==timestamp]
    trades_snapshot = trades_data[trades_data["timestamp"]==timestamp]
    state = generate_state(timestamp, prices_snapshot, trades_snapshot, myself)

    orders, log_result = myself.trader.run(state)
    outstanding_orders = matching(orders, state, myself)
    pnl = calculate_profit(timestamp, state, myself)

    generate_log(timestamp, prices_snapshot, my_log, log_result)

#Outputted log has to be put into visualiser_log.log to be compatible with visualiser
with open("trade_log.log", "w") as file:
    file.write(my_log.sandbox + "\n\n" + my_log.submission + "\n\n" + my_log.activities)

#logger = logging.getLogger('trade_log')
#logger.setLevel(logging.DEBUG)
## create file handler which logs even debug messages
#file_handler = logging.FileHandler('trade_log.log', mode="w", encoding='utf-8')
#file_handler.setLevel(logging.DEBUG)
#logger.addHandler(file_handler)
#logger.debug(my_log.sandbox + "\n\n" + my_log.submission + "\n\n" + my_log.activities)
