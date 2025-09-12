import ivory_test as deck
import time


def labview_tcp_demo_prep():
	if not device.connect():