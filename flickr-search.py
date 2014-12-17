import argparse
import time
import datetime
from dateutil import parser
import socket
import flickrapi
from sets import Set

def fetchPhotos(flickr, **kwargs):
	pages = -1
	total = -1
	page = 1
	while True:
		if pages != -1 and page > pages:
			break
		print "calling flickr.photos.search, page ", page
		photos = None
		try:
			params = {}
			photos = flickr.photos_search(page=str(page), **kwargs)
		except Exception as e:
			print e
	
		if photos is not None:
			pages = int(photos[0].attrib['pages'])
			total = int(photos[0].attrib['total'])
			if page == 1:
				print pages, ' pages'
				print total, ' total'
			if len(photos[0]) == 0:
				break
			j = 1
			for photo in photos[0]:
				#print 'photo', j, photo.attrib['id']
				if(photo.attrib['id'] not in downloaded_photo_ids):
					try:
						id = photo.attrib['id']
						user_id = photo.attrib['owner']
						title = photo.attrib['title'].encode('utf-8')
						location_lon = photo.attrib['longitude']
						location_lat = photo.attrib['latitude']
						accuracy = photo.attrib['accuracy']
						timestamp = photo.attrib['datetaken']
						user_name = photo.attrib['ownername'].encode('utf-8')
						caption = photo.find('description').text
						if caption == None:
							caption = ''
						caption = caption.encode('utf-8').replace('\n', '')
						link = photo.attrib['url_m']
						type = photo.attrib['media']
						tags = photo.attrib['tags'].encode('utf-8').replace(' ', ',')
								
						f.write(id + '|' + type + '|' + user_id + '|' + user_name + '|' + link + '|' + timestamp + '|' + str(location_lon) + '|' + str(location_lat) + '|' + accuracy + '|' + caption + '|' + tags + '\n')
						downloaded_photo_ids.add(id)
						user_ids.add(user_id)
						#print '  added'
					except Exception as e:
						#print e, '  skipping'
						pass
				else:
					#print '  already added'
					pass
				j = j + 1
			page = page + 1
		else:
			print 'waiting 1 minute for next call...'
			time.sleep(60)

socket.setdefaulttimeout(5)

argparser = argparse.ArgumentParser()
argparser.add_argument("api_key", help="instagram access-token", type=str)
argparser.add_argument("lon_min", help="bounding box minimum longitude", type=float)
argparser.add_argument("lon_max", help="bounding box maximum longitude", type=float)
argparser.add_argument("lat_min", help="bounding box minimum latitude", type=float)
argparser.add_argument("lat_max", help="bounding box maximum latitude", type=float)
argparser.add_argument("t_min", help="minimum timestamp", type=str)
argparser.add_argument("t_max", help="maximum timestamp", type=str)
argparser.add_argument("max_duration", help="maximum duration in days", type=str)
argparser.add_argument("output", help="location of output file", type=str)
argparser.add_argument("-a", help="also retrieve all photos outside of the bbox of users within the result set", action="store_true")
args = argparser.parse_args()	

flickr = flickrapi.FlickrAPI(args.api_key, cache=False)
bbox_string = str(args.lon_min) + ',' + str(args.lat_min) + ',' + str(args.lon_max) + ',' + str(args.lat_max)

t_min = parser.parse(args.t_min)
t_max = parser.parse(args.t_max)
days = (t_max - t_min).days

t_max_list = [t_max - datetime.timedelta(days=x*int(args.max_duration)) for x in range(0, (days/int(args.max_duration)) + 1)]
t_min_list = [t_max - datetime.timedelta(days=x*int(args.max_duration)) for x in range(1, (days/int(args.max_duration)) + 2)]
t_min_list = [t_min if x<t_min else x for x in t_min_list]

downloaded_photo_ids = Set([])
user_ids = Set([])
f = open(args.output, "a")
f.write('id|type|user_id|user_name|link|timestamp|lon|lat|accuracy|caption|tags\n')

for i in range(0, len(t_max_list)):
	t1 = t_min_list[i]
	t2 = t_max_list[i]
	t1_unix = time.mktime(t1.timetuple())
	t2_unix = time.mktime(t2.timetuple())
	print t1, t2
	
	fetchPhotos(flickr, bbox=bbox_string, min_taken_date=str(int(t1_unix)), max_taken_date=str(int(t2_unix)), extras='media,geo,description,owner_name,date_taken,url_m,tags')

if args.a:
	print 'Downloading all photos of users in result set...'
	call = 0
	for user_id in user_ids:
		call = call + 1
		print user_id, '(', call, ' of ', len(user_ids), ', ', round(float(call) / float(len(user_ids)) * 100, 3), '%)'
		fetchPhotos(flickr, user_id=user_id, extras='media,geo,description,owner_name,date_taken,url_m,tags')

f.close()
print 'done!'