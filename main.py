import requests
import csv
from tabulate import tabulate
import pandas as pd
from datetime import date


class Result:
    def __init__(self, date: str,
                 deposit_value: float,
                 profit_accumulated_previous: float,
                 investment_accumulated: float,
                 investment_value: float):
        self.date = date
        self.deposit_value = deposit_value
        self.investment_accumulated = investment_accumulated
        self.investment_value = investment_value
        self.profit_accumulated = investment_value - investment_accumulated
        self.profit_interval = self.profit_accumulated - profit_accumulated_previous
        self.profitability = self.profit_interval / investment_value
        self.percentage_profit = self.profit_accumulated / investment_value
        self.percentage_investment = self.investment_accumulated / investment_value


class Investment:

    def __init__(self):
        self.__investment_accumulated = 0.0  # Inversion acumulada
        self.__investment_value = 0.0  # Valor del portafolio
        self.__share_total = 0.0  # Cantidad de stock options

    def add_investment_accumulated(self, value: float):
        self.__investment_accumulated += value

    def add_investment_value(self, value: float):
        self.__investment_value += value

    def add_share(self, share: float):
        self.__share_total += share

    def get_investment_accumulated(self):
        """
        Total de la inversion realizada
        :return:
        """
        return self.__investment_accumulated

    def get_investment_value(self):
        """
        Valor de la inversion
        :return:
        """
        return self.__investment_value

    def get_share_total(self):
        """
        Cantidad de stocks comprados
        :return:
        """
        return self.__share_total

    def get_total_profit(self):
        """
        Ganancia total
        :return:
        """
        return self.__investment_value - self.__investment_accumulated

    def get_percentage_investment(self) -> float:
        """
        Porcentaje del valor que es inversion
        :return:
        """
        return self.get_investment_accumulated() / self.get_investment_value()

    def get_percentage_profit(self) -> float:
        """
        Porcentaje del valor que son ganancias
        :return:
        """
        return self.get_total_profit() / self.get_investment_value()


class StockShare:

    def __init__(self, date: str, value: float, stock_price: float):
        self.date = date
        self.value = value
        self.share = float(value / stock_price)
        self.stock_price = stock_price

    def new_stock_value(self, stock_price: float, new_date: str):
        return StockShare(new_date, self.share * stock_price, stock_price)


class Deposit:

    def __init__(self, amount: float, initial_date: str, stock_price: float):
        self.amount = amount
        self.initial_date = initial_date
        self.history = []
        self.history.append(StockShare(initial_date, amount, stock_price))

    def new_time(self, stock_price: float, date: str):
        self.history.append(self.history[-1].new_stock_value(stock_price, date))

    def get_value(self) -> float:
        return self.history[-1].value

    def get_share(self) -> float:
        return self.history[-1].share

    def print(self):
        print()
        print("------------------------------")
        print("Deposit (%s): %s" % (self.initial_date, currency_value(self.amount)))
        print("------------------------------")
        output = []
        for stock_share in self.history:
            output.append((stock_share.date, float_value(stock_share.share), currency_value(stock_share.value),
                           currency_value(stock_share.stock_price)))
        print(tabulate(output, headers=["Date", "Share", "Value", "Stock Price"], tablefmt="pipe"))
        print("------------------------------")
        print()


"""
##########################
GLOBAL VARS
##########################
"""

deposits = list()
investment = Investment()
results = list()

"""
##########################
"""


def calculate_results():
    for deposit in deposits:
        investment.add_investment_value(deposit.get_value())
        investment.add_share(deposit.get_share())


def update_deposits(date: str, new_stock_price: float):
    for i in range(len(deposits)):
        deposits[i].new_time(new_stock_price, date)


def get_deposits_investment_value() -> float:
    value = 0
    for deposit in deposits:
        value += deposit.get_value()
    return value


def convert_date_to_timestamp(date):
    """
    Convierte una fecha a timestamp.

    Devuelve:
      Timestamp de la fecha.
    """
    date_pd = pd.to_datetime(date)
    return int(date_pd.timestamp())


def currency_value(value: float) -> str:
    return "${:,.2f}".format(value)


def float_value(value: float) -> str:
    return f"{value:.2f}"


def percentage(value: float) -> str:
    return f"-{float_value(abs(value) * 100)}%" if value < 0 else f"{float_value(value * 100)}%"


def get_stock_historical(date_from: str, date_to: str, interval: str, stock: str):
    """

    Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]

    :param date_from:
    :param date_to:
    :return:
    """
    url = "https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%s&period2=%s&interval" \
          "=%s&events=history " % (
              stock, convert_date_to_timestamp(date_from), convert_date_to_timestamp(date_to), interval)

    headers = {
        "host": "query1.finance.yahoo.com",
        "user-agent": "insomnia/2023.5.8",
        "accept": "*/*"
    }
    response = requests.get(url, headers=headers)
    reader = csv.DictReader(response.text.splitlines(), delimiter=",")
    return list(reader)


if __name__ == '__main__':

    date_from = str(input("Start date (YYYY-MM-DD): "))
    date_to = str(input("Finish date (YYYY-MM-DD)(Skip: Current): "))
    print("Set interval [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]")
    interval = str(input("Interval: "))
    stock = input("Stock (Default: VOO): ")
    interval_investment = float(input("Interval investment (USD): "))
    print_deposit_evolution: bool = input("print evolution deposits? (Y|N)").lower() == "y"

    if stock is None or stock == "":
        stock = "VOO"

    date_to = date_to if date_to != "" else date.today()

    history_data = get_stock_historical(date_from, date_to, interval, stock)

    for item in history_data:

        if item['Open'] == 'null' or item['Close'] == 'null':
            continue

        date = item["Date"]
        price_open = float(item["Open"])
        price_closed = float(item["Close"])

        update_deposits(date, price_open)
        deposits.append(Deposit(interval_investment, date, price_open))

        investment.add_investment_accumulated(interval_investment)

        results.append(
            Result(date,
                   interval_investment,
                   0.0 if len(results) == 0 else results[-1].profit_accumulated,
                   investment.get_investment_accumulated(),
                   get_deposits_investment_value()
                   ))

    calculate_results()

    data = [
        ("Fecha inicial", date_from),
        ("Fecha final", date_to),
        ("Intervalo de inversion", interval),
        ("Abono", currency_value(interval_investment)),
        ("Cantidad de abonos", len(deposits)),
        ("Total inversion", currency_value(investment.get_investment_accumulated())),
        ("Valor de la inversión", currency_value(investment.get_investment_value())),
        ("Cantidad de stocks", float_value(investment.get_share_total())),
        ("Ganancias total", currency_value(investment.get_total_profit())),
        ("% Port. Ganancia", percentage(investment.get_percentage_profit())),
        ("% Port. Inversion", percentage(investment.get_percentage_investment()))
    ]

    if print_deposit_evolution:
        for deposit in deposits:
            deposit.print()

    print()
    print("===== RESULT =====")
    print(tabulate(data, tablefmt="pipe"))

    evolution_table = []

    for result in results:
        evolution_table.append((result.date, currency_value(result.deposit_value),
                                currency_value(result.investment_accumulated), percentage(result.profitability),
                                currency_value(result.profit_interval), currency_value(result.profit_accumulated),
                                percentage(result.percentage_profit),
                                percentage(result.percentage_investment), currency_value(result.investment_value)))

    print(
        tabulate(evolution_table, headers=["Fecha", "Abono", "Inversion acumulada", "Rentabilidad", "Ganancias del mes",
                                           "Ganancia acumulada", "% Port. - Ganancia", "% Port. - Inversion",
                                           "Valor portafolio"], tablefmt="pipe"))
