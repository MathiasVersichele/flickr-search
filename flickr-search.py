import argparse
import time
import datetime
from dateutil import parser
import socket
import flickrapi
from sets import Set

socket.setdefaulttimeout(5)

helpstring = 'usage: instagram-stsearch.py -h(elp) -t <access-token> -b <bbox min-lon,max-lon,min-lat,max-lat> -s <start timestamp in human readable format> -e <end timestamp in human readable format> -o <outputfile> [-r <radius of search circles, default 5000m>]'

argparser = argparse.ArgumentParser()
argparser.add_argument("api_key", help="instagram access-token", type=str)
argparser.add_argument("lon_min", help="bounding box minimum longitude", type=float)
argparser.add_argument("lon_max", help="bounding box maximum longitude", type=float)
argparser.add_argument("lat_min", help="bounding box minimum latitude", type=float)
argparser.add_argument("lat_max", help="bounding box maximum latitude", type=float)
argparser.add_argument("t_min", help="minimum timestamp", type=str)
argparser.add_argument("t_max", help="maximum timestamp", type=str)
argparser.add_argument("max_duration", help="maximum duration in days", type=str)
argparser.add_argument("output", help="output location", type=str)
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
f = open(args.output, "a")
f.write('id|title|user_id|lon|lat|taken|tags\n')

for i in range(0, len(t_max_list)):
	t1 = t_min_list[i]
	t2 = t_max_list[i]
	t1_unix = time.mktime(t1.timetuple())
	t2_unix = time.mktime(t2.timetuple())
	print t1, t2
	
	pages = -1
	total = -1
	page = 1
	while True:
		if pages != -1 and page > pages:
			break
		print "calling flickr.photos.search, page ", page
		photos = None
		try:
			photos = flickr.photos_search(bbox=bbox_string, min_taken_date=str(int(t1_unix)), max_taken_date=str(int(t2_unix)), page=str(page))
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
			#new_photos = 0
			for photo in photos[0]:
				print 'photo', j, photo.attrib['id']
				if(photo.attrib['id'] not in downloaded_photo_ids):
					try:
						photoLoc = flickr.photos_geo_getLocation(photo_id=photo.attrib['id'])
						photoInfo = flickr.photos_getInfo(photo_id=photo.attrib['id'])
						photoTags = flickr.tags_getListPhoto(photo_id=photo.attrib['id']).find('photo').find('tags')
						tags = []
						for tag in photoTags.getiterator():
							if not (tag.get('raw') is None):
								tags.append(tag.get('raw'))
						f.write(photo.attrib['id'] + '|' + photo.attrib['title'].encode('utf-8') + '|' + photo.attrib['owner'] + '|' + photoLoc[0][0].attrib['longitude'] + '|' + photoLoc[0][0].attrib['latitude'] + '|' + photoInfo.find('photo').find('dates').get('taken') + '|' + ','.join(tags).encode('utf-8') + '\n')
						downloaded_photo_ids.add(photo.attrib['id'])
						print '  added'
						#new_photos = new_photos + 1
					except Exception as e:
						print e
						print '  skipping'
				else:
					print '  already added'
				j = j + 1
			page = page + 1
			#if new_photos == 0:
			#	break
		else:
			print 'waiting 1 minute for next call...'
			time.sleep(60)
f.close()
print 'done!'