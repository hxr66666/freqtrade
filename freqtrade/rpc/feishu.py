import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from freqtrade.constants import Config
from freqtrade.rpc import RPC
from freqtrade.rpc.webhook import Webhook

logger = logging.getLogger(__name__)


def makeMd(txt):
	md_template = '''{{
		            "tag": "markdown",
		            "content": "{}",
		            "text_align": "left",
		            "text_size": "normal_v2",
		            "margin": "0px 0px 0px 0px"
		    }}'''
	
	print(txt)
	lines = txt.split("\n")
	md_elements = []
	
	for line in lines:
		# 去除前后空格，替换引号为反引号
		cleaned_line = line.strip().replace('"', '`').replace('`', '`')
		# 格式化每个markdown元素
		md_element = md_template.format(cleaned_line)
		md_elements.append(md_element)
	
	# 用逗号连接所有元素
	return ",".join(md_elements)


class Feishu(Webhook):
	def __init__(self, rpc: "RPC", config: Config):
		self._config = config
		self.rpc = rpc
		self.strategy = config.get("strategy", "")
		self.timeframe = config.get("timeframe", "")
		self.bot_name = config.get("bot_name", "")
		
		self._url = config["feishu"]["url"]
		self._format = "json"
		self._retries = 1
		self._retry_delay = 0.1
		self._timeout = self._config["feishu"].get("timeout", 10)
	
	def cleanup(self) -> None:
		"""
		Cleanup pending module resources.
		This will do nothing for webhooks, they will simply not be called anymore
		"""
		pass
	
	def send_msg(self, msg) -> None:
		
		msg["strategy"] = self.strategy
		msg["timeframe"] = self.timeframe
		msg["bot_name"] = self.bot_name
		
		action = msg['type'].value
		exchange = msg.get('exchange', "")
		pair = msg.get('pair', "")
		
		md_table = ["| 参数 | 值 |", "| --- | --- |", f"| 交易所 | {exchange} |", f"| 交易对 | {pair} |"]
		
		if action == "entry":  # 买入订单
			action = "买入"
			md_table.append(f"| 操作类型 | {action} |")
			md_table.append(f"| 价值USD | {msg['fiat_currency']} |")
			md_table.append(f"| 开仓价格 | {msg['open_rate']} |")
			md_table.append(f"| 交易数量 | {msg['amount']} |")
			md_table.append(f"| 当前价格 | {msg['current_rate']} |")
			md_table.append(f"| 开始持仓 | {self.format_to_shanghai_time(msg['open_date'])} |")
		
		elif action == "entry_cancel":  # 取消买入订单
			action = "取消买入"
			md_table.append(f"| 操作类型 | {action} |")
			md_table.append(f"| 价值USD | {msg['fiat_currency']} |")
			md_table.append(f"| 开仓价格 | {msg['open_rate']} |")
			md_table.append(f"| 交易数量 | {msg['amount']} |")
			md_table.append(f"| 当前价格 | {msg['current_rate']} |")
			md_table.append(f"| 开始持仓 | {self.format_to_shanghai_time(msg['open_date'])} |")
		
		elif action == "entry_fill":  # 买入成交
			action = "买入成交"
			md_table.append(f"| 操作类型 | {action} |")
			md_table.append(f"| 价值USD | {msg['fiat_currency']} |")
			md_table.append(f"| 开仓价格 | {msg['open_rate']} |")
			md_table.append(f"| 交易数量 | {msg['amount']} |")
			md_table.append(f"| 当前价格 | {msg['current_rate']} |")
			md_table.append(f"| 开始持仓 | {self.format_to_shanghai_time(msg['open_date'])} |")
		
		elif action == "exit":  # 卖出订单
			action = "卖出"
			md_table.append(f"| 操作类型 | {action} |")
			md_table.append(f"| 价值USD | {msg['fiat_currency']} |")
			md_table.append(f"| 开仓价格 | {msg['open_rate']} |")
			md_table.append(f"| 平仓价格 | {msg['close_rate']} |")
			md_table.append(f"| 交易数量 | {msg['amount']} |")
			profit_amount = "" if msg['profit_amount'] is None else msg['profit_amount']
			md_table.append(f"| 实际盈利 | {profit_amount} |")
			md_table.append(f"| 当前价格 | {msg['current_rate']} |")
			md_table.append(f"| 开始持仓 | {self.format_to_shanghai_time(msg['open_date'])} |")
			md_table.append(f"| 结束持仓 | {self.format_to_shanghai_time(msg['close_date'])} |")
			md_table.append(f"| 平仓原因 | {msg['exit_reason']} |")
		
		elif action == "exit_cancel":  # 卖出取消
			action = "取消卖出，继续持仓"
			md_table.append(f"| 操作类型 | {action} |")
			md_table.append(f"| 价值USD | {msg['fiat_currency']} |")
			md_table.append(f"| 开仓价格 | {msg['open_rate']} |")
			md_table.append(f"| 平仓价格 | {msg['close_rate']} |")
			md_table.append(f"| 交易数量 | {msg['amount']} |")
			profit_amount = "" if msg['profit_amount'] is None else msg['profit_amount']
			md_table.append(f"| 实际盈利 | {profit_amount} |")
			md_table.append(f"| 当前价格 | {msg['current_rate']} |")
			md_table.append(f"| 开始持仓 | {self.format_to_shanghai_time(msg['open_date'])} |")
			md_table.append(f"| 结束持仓 | {self.format_to_shanghai_time(msg['close_date'])} |")
			md_table.append(f"| 平仓原因 | {msg['exit_reason']} |")
		
		elif action == "exit_fill":  # 卖出成交
			action = "卖出成交"
			md_table.append(f"| 操作类型 | {action} |")
			md_table.append(f"| 价值USD | {msg['fiat_currency']} |")
			md_table.append(f"| 开仓价格 | {msg['open_rate']} |")
			md_table.append(f"| 平仓价格 | {msg['close_rate']} |")
			md_table.append(f"| 交易数量 | {msg['amount']} |")
			profit_amount = "" if msg['profit_amount'] is None else msg['profit_amount']
			md_table.append(f"| 实际盈利 | {profit_amount} |")
			md_table.append(f"| 当前价格 | {msg['current_rate']} |")
			md_table.append(f"| 开始持仓 | {self.format_to_shanghai_time(msg['open_date'])} |")
			md_table.append(f"| 结束持仓 | {self.format_to_shanghai_time(self.format_to_shanghai_time(msg['close_date']))} |")
			md_table.append(f"| 平仓原因 | {msg['exit_reason']} |")
		
		elif action == "status":  # 机器人状态
			logger.info(f"机器人状态{msg['status']}")
			return
		else:
			logger.info(f"{msg}")
			return
		
		# md_table.append(f"| 交易方向 | {message.getDirection()} |")
		# md_table.append(f"| 杠杆 | {message.getLeverage()} |")
		
		md_content = "\n".join(md_table)
		make_md = makeMd(md_content)
		
		bot_msg_tmp = """
			{{
			     "msg_type": "interactive",
			     "card": {{
			       "schema": "2.0",
			       "config": {{
			         "update_multi": true,
			         "style": {{
			           "text_size": {{
			             "normal_v2": {{
			               "default": "normal",
			               "pc": "normal",
			               "mobile": "heading"
			             }}
			           }}
			         }}
			       }},
			       "body": {{
			         "direction": "vertical",
			         "padding": "12px 12px 12px 12px",
			         "elements": [
			               {}
			         ]
			       }},
			       "header": {{
			         "title": {{
			           "tag": "plain_text",
			           "content": "{}"
			         }},
			         "subtitle": {{
			           "tag": "plain_text",
			           "content": "{}"
			         }},
			         "template": "blue",
			         "padding": "12px 12px 12px 12px"
			       }}
			     }}
			   }}
			"""
		json_data = bot_msg_tmp.format(make_md, "AI策略现货信号:提醒⚡", "仅供参考，认真鉴别，亏损自己承担😁")
		
		self._send_msg(json.loads(json_data))
	
	@classmethod
	def format_to_shanghai_time(cls, dt):
		shanghai_tz = ZoneInfo('Asia/Shanghai')
		
		if isinstance(dt, datetime):
			if dt.tzinfo is None:
				dt = dt.replace(tzinfo=ZoneInfo('UTC'))
			dt_shanghai = dt.astimezone(shanghai_tz)
		else:
			dt = datetime.fromisoformat(str(dt).replace('Z', '+00:00'))
			dt_shanghai = dt.astimezone(shanghai_tz)
		
		return dt_shanghai.strftime('%y-%m-%d %H:%M:%S')
