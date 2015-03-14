from Foundation import *
from AppKit import *
from PyObjCTools import AppHelper
import objc
import feedparser
import re
import operator
import webbrowser
import os.path

NSUserNotification = objc.lookUpClass('NSUserNotification')
NSUserNotificationCenter = objc.lookUpClass('NSUserNotificationCenter')

habrahabr_rss_link = "http://habrahabr.ru/rss/feed/posts/a5294f4ae04467c9a69b3f963bf2317d/";
post_ids_filename = 'post_ids.txt'

def save_post_id(post_id):
	handle = open(post_ids_filename, 'a')
	handle.write(str(post_id) + '\n')
	handle.close()

def find_post_id(post_id):
	post_id = int(post_id)
	if not os.path.exists(post_ids_filename):
		return False

	handle = open(post_ids_filename, 'r')
	lines = []
	for line in handle:
		lines.append(int(line))
	handle.close()

	return post_id in lines

def notify(title, subtitle="", info_text="", identifier=False, delay=0, sound=False, user_info={}):
	notification = NSUserNotification.alloc().init()
	notification.setTitle_(title)
	notification.setSubtitle_(subtitle)
	notification.setIdentifier_(identifier)
	notification.setInformativeText_(info_text)
	notification.setUserInfo_(user_info)
	notification.set_identityImage_(NSImage.imageNamed_('habr.png'))
	notification.setDeliveryDate_(Foundation.NSDate.dateWithTimeInterval_sinceDate_(delay, Foundation.NSDate.date()))
	if sound:
		notification.setSoundName_("NSUserNotificationDefaultSoundName") 
	
	NSUserNotificationCenter.defaultUserNotificationCenter().scheduleNotification_(notification)

def fetch_feed_and_notify():
	feed = feedparser.parse(habrahabr_rss_link)

	for item in feed['items']:
		title = re.compile(r'\[[^\]]+\]').sub('', item['title']).strip()
		tags = ', '.join(map(operator.itemgetter("term"), item['tags']))
		text = re.compile(r'<[^>]+>').sub('', item['summary']).strip()
		link = item['id']
		post_id = re.search('(\d+)', link).group(0)
		payload = {"action": "open_url", "value": link}

		if not find_post_id(post_id):
			notify(title=title, subtitle=tags, info_text=text, identifier=post_id, user_info=payload)
			save_post_id(post_id)

class HabrNotifierAppDelegate(NSObject):
	def applicationDidFinishLaunching_(self, sender):
		user_info = sender.userInfo()
		if user_info.has_key('NSApplicationLaunchUserNotificationKey'):
			notification_payload = user_info['NSApplicationLaunchUserNotificationKey'].userInfo()
			if notification_payload.has_key('action') and notification_payload['action'] == 'open_url':
				webbrowser.open(notification_payload['value'])
		else:
			fetch_feed_and_notify()

		NSApplication.sharedApplication().terminate_(False)

if __name__ == "__main__":
	app = NSApplication.sharedApplication()
	app_delegate = HabrNotifierAppDelegate.alloc().init()
	app.setDelegate_(app_delegate)
	AppHelper.runEventLoop()
